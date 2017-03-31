import pylibmc
import uuid

from contextlib import contextmanager
from hashlib import md5
from threading import local

from .. import Adapter, Transaction
from ..properties import Msgpack


class _MemcacheOuterTransaction(Transaction):
    def __init__(self, adapter, ds_transaction):
        self.adapter = adapter
        self.ds_transaction = ds_transaction

        self.batch = []
        self.begin = self.ds_transaction.begin
        self.rollback = self.ds_transaction.rollback

    def _push_keys(self, keys):
        self.batch.extend(keys)

    def commit(self):
        with self.adapter._bust(self.batch):
            self.ds_transaction.commit()

    def end(self):
        self.ds_transaction.end()
        self.adapter._transactions.remove(self)


class _MemcacheInnerTransaction(Transaction):
    def __init__(self, parent, ds_transaction):
        self.parent = parent
        self.ds_transaction = ds_transaction

        self.begin = ds_transaction.begin
        self.commit = ds_transaction.commit
        self.rollback = ds_transaction.rollback

    def end(self):
        self.ds_transaction.end()
        self.adapter._transactions.remove(self)

    def __getattr__(self, name):
        return getattr(self.parent, name)


class MemcacheAdapter(Adapter):
    """Transparently adds memcached-based strongly-consistent caching
    on top of another adapter for delete, get and put operations.

    Parameters:
      client(pylibmc.Client): The memcached client instance to use.
        This is automatically wrapped inside a ThreadMappedPool.
      adapter(Adapter): The adapter to wrap.
      namespace(str, optional): The string keys should be prefixed
        with.  Defaults to ``anom``.
    """

    _state = local()

    _lock_prefix = b"LOCK@"
    _lock_timeout = 60  # seconds
    _item_timeout = 86400  # one day in seconds

    def __init__(self, client, adapter, *, namespace="anom"):
        self.client_pool = pylibmc.ThreadMappedPool(client)
        self.adapter = adapter
        self.namespace = namespace

        self.query = self.adapter.query

    @property
    def _transactions(self):
        "list[Transaction]: The current stack of Transactions."
        transactions = getattr(self._state, "transactions", None)
        if transactions is None:
            transactions = self._state.transactions = []
        return transactions

    def delete_multi(self, keys):
        if self.in_transaction:
            self.current_transaction._push_keys(keys)
            return self.adapter.delete_multi(keys)

        with self._bust(keys):
            return self.adapter.delete_multi(keys)

    def get_multi(self, keys):
        if self.in_transaction:
            return self.adapter.get_multi(keys)

        # Get all the cached keys.
        pairs = {self._convert_key_to_memcache(key): key for key in keys}
        with self.client_pool.reserve() as client:
            mapping = client.get_multi(pairs.keys())

        # Sort out which ones were found in Memcache and which ones we
        # need to get from Datastore.
        found, missing = [None] * len(keys), []
        for memcache_key, anom_key in pairs.items():
            data = mapping.get(memcache_key)
            # If there is no data or the data appears to be locked, we
            # have to grab the entity from datastore.
            if data is None or data.startswith(self._lock_prefix):
                missing.append(anom_key)
                continue

            index = keys.index(anom_key)
            found[index] = Msgpack._loads(data)

        # Get and cache missing keys from Datastore.
        ds_results = self.adapter.get_multi(missing)
        for anom_key, entity in zip(missing, ds_results):
            index = keys.index(anom_key)
            found[index] = entity
            if entity is None:
                continue

            key = self._convert_key_to_memcache(anom_key)
            data = Msgpack._dumps(entity)
            self._cache(key, data)

        return found

    def put_multi(self, requests):
        # Partial keys' cache doesn't need to be cleared since they
        # can't have been already set so we have to collect the full
        # keys and pass them to the transaction.
        full_keys = [request.key for request in requests if not request.key.is_partial]
        if self.in_transaction:
            self.current_transaction._push_keys(full_keys)
            return self.adapter.put_multi(requests)

        with self._bust(full_keys):
            return self.adapter.put_multi(requests)

    def transaction(self, propagation):
        ds_transaction = self.adapter.transaction(propagation)

        if propagation == Transaction.Propagation.Independent:
            transaction = _MemcacheOuterTransaction(self, ds_transaction)
            self._transactions.append(transaction)
            return transaction

        elif propagation == Transaction.Propagation.Nested:
            if self._transactions:
                transaction = _MemcacheInnerTransaction(self.current_transaction, ds_transaction)
            else:
                transaction = _MemcacheOuterTransaction(self, ds_transaction)

            self._transactions.append(transaction)
            return transaction

        else:  # pragma: no cover
            raise ValueError(f"Invalid propagation option {propagation!r}.")

    @property
    def in_transaction(self):
        return bool(self._transactions)

    @property
    def current_transaction(self):
        return self._transactions[-1]

    def _convert_key_to_memcache(self, anom_key):
        digest = md5(str(anom_key).encode("utf-8")).hexdigest()
        return f"{self.namespace}:{digest}"

    @contextmanager
    def _bust(self, keys):
        current_lock = self._lock_value()
        memcache_keys = [self._convert_key_to_memcache(key) for key in keys]
        memcache_pairs = {key: current_lock for key in memcache_keys}

        # Lock the keys so that they can't be set for the duration of
        # the delete (or until timeout).
        with self.client_pool.reserve() as client:
            client.set_multi(memcache_pairs, self._lock_timeout)

        try:
            # Delete the keys from Datastore.
            yield

        finally:
            # Finally, delete the keys from Memcache.
            with self.client_pool.reserve() as client:
                client.delete_multi(memcache_keys)

    def _cache(self, key, data):
        current_lock = self._lock_value()
        with self.client_pool.reserve() as client:
            while True:
                value, cid = client.gets(key)
                # If there is a lock value in Memcache that is
                # different from our own we have to bail.
                if value and value.startswith(self._lock_prefix) and value != current_lock:
                    return

                # If there isn't a value at all, we have to add one
                # and try again.
                if cid is None:
                    client.add(key, current_lock, self._lock_timeout)
                    continue

                try:
                    return client.cas(key, data, cid, self._item_timeout)

                # There is a small chance that between the `gets` and
                # "now" the key will have been deleted by a concurrent
                # process, so we account for that possibility here.
                except pylibmc.NotFound:  # pragma: no cover
                    return

    def _lock_value(self):
        random_value = str(uuid.uuid4()).encode("ascii")
        lock_value = self._lock_prefix + random_value
        return lock_value
