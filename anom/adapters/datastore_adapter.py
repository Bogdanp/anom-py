import logging

from functools import partial
from gcloud_requests import DatastoreRequestsProxy, enter_transaction, exit_transaction
from google.cloud import datastore
from threading import local

from .. import Adapter, Key
from ..adapter import QueryResponse
from ..model import KeyLike
from ..transaction import Transaction, TransactionFailed

_logger = logging.getLogger("datastore_adapter")


class _DeferredKey(KeyLike):
    def __init__(self, ds_entity):
        self.ds_entity = ds_entity
        self._value = None

    @property
    def _anom_key(self):
        if self._value is None or self._value.is_partial:
            self._value = DatastoreAdapter._convert_key_from_datastore(self.ds_entity.key)
        return self._value

    def __getattr__(self, name):
        return getattr(self._anom_key, name)

    def __repr__(self):
        return repr(self._anom_key)


class _DatastoreOuterTransaction(Transaction):
    def __init__(self, adapter):
        self.adapter = adapter
        self.ds_transaction = adapter.client.transaction()

    def begin(self):
        _logger.debug("Beginning transaction...")
        self.ds_transaction.begin()
        self.adapter.client._push_batch(self.ds_transaction)
        enter_transaction()

    def commit(self):
        try:
            _logger.debug("Committing transaction...")
            self.ds_transaction.commit()
        except Exception as e:
            _logger.debug("Transaction failed: %s", e)
            raise TransactionFailed(e)

    def rollback(self):
        _logger.debug("Rolling transaction back...")
        self.ds_transaction.rollback()

    def end(self):
        _logger.debug("Ending transaction...")
        exit_transaction()
        self.adapter.client._pop_batch()
        self.adapter._transactions.remove(self)


class _DatastoreInnerTransaction(Transaction):
    def __init__(self, parent):
        self.parent = parent

    def begin(self):
        _logger.debug("Beginning inner transaction...")

    def commit(self):
        _logger.debug("Committing inner transaction...")

    def rollback(self):
        _logger.debug("Rolling back inner transaction...")

    def end(self):
        _logger.debug("Ending inner transaction...")
        self.adapter._transactions.remove(self)

    def __getattr__(self, name):
        return getattr(self.parent, name)


class DatastoreAdapter(Adapter):
    """A Google Cloud Datastore adapter based on :mod:`google.cloud.datastore`.

    Parameters:
      project(str, optional): The project this Adapter should connect to.
      namespace(str, optional): The namespace inside which this
        Adapter should operate by default.  Individual Datastore Keys
        may specify their own namespaces and override this.
      credentials(datastore.Credentials): The OAuth2 Credentials to
        use for this client.  If not passed, falls back to the default
        inferred from the environment.
    """

    _state = local()

    def __init__(self, *, project=None, namespace=None, credentials=None):
        self.project = project
        self.namespace = namespace
        self.credentials = credentials

    @property
    def client(self):
        """datastore.Client: The underlying datastore client for this
        adapter instance.  This property is thread-local.
        """
        client = getattr(self._state, "client", None)
        if client is None:
            client = self._state.client = datastore.Client(
                credentials=self.credentials,
                project=self.project,
                namespace=self.namespace,
                _http=DatastoreRequestsProxy(),
                _use_grpc=False,
            )
        return client

    @property
    def _transactions(self):
        "list[Transaction]: The current stack of Transactions."
        transactions = getattr(self._state, "transactions", None)
        if transactions is None:
            transactions = self._state.transactions = []
        return transactions

    def delete_multi(self, keys):
        self.client.delete_multi(self._convert_key_to_datastore(key) for key in keys)

    def get_multi(self, keys):
        get_multi = self.client.get_multi
        if self.in_transaction:
            transaction = self.current_transaction
            get_multi = partial(get_multi, transaction=transaction.ds_transaction)

        datastore_keys = [self._convert_key_to_datastore(key) for key in keys]
        request_keys = set(datastore_keys)
        found, missing, deferred = [], [], []
        while True:
            found.extend(get_multi(request_keys, missing=missing, deferred=deferred))
            if not deferred:
                break

            for entity in found:
                request_keys.remove(entity.key)

            for key in missing:
                request_keys.remove(key)

        results = [None] * len(keys)
        for entity in found:
            index = datastore_keys.index(entity.key)
            results[index] = self._prepare_to_load(entity)

        return results

    def put_multi(self, requests):
        entities = [self._prepare_to_store(*request) for request in requests]
        self.client.put_multi(entities)
        if self.in_transaction:
            return [_DeferredKey(entity) for entity in entities]
        return [self._convert_key_from_datastore(entity.key) for entity in entities]

    def query(self, query, options):
        ancestor = None
        if query.ancestor:
            ancestor = self._convert_key_to_datastore(query.ancestor)

        query = self.client.query(
            kind=query.kind,
            ancestor=ancestor,
            namespace=query.namespace,
            projection=query.projection,
            filters=query.filters,
            order=query.orders,
        )
        if options.keys_only:
            query.keys_only()

        result_iterator = query.fetch(
            limit=options.batch_size,
            offset=options.offset,
            start_cursor=options.cursor,
        )

        entities = []
        for entity in result_iterator:
            key, data = self._convert_key_from_datastore(entity.key), None
            if not options.keys_only:
                data = self._prepare_to_load(entity)

            entities.append((key, data))

        return QueryResponse(entities=entities, cursor=result_iterator.next_page_token)

    def transaction(self, propagation):
        if propagation == Transaction.Propagation.Independent:
            transaction = _DatastoreOuterTransaction(self)
            self._transactions.append(transaction)
            return transaction

        elif propagation == Transaction.Propagation.Nested:
            if self._transactions:
                transaction = _DatastoreInnerTransaction(self.current_transaction)
            else:
                transaction = _DatastoreOuterTransaction(self)

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

    def _convert_key_to_datastore(self, anom_key):
        return self.client.key(*anom_key.path, namespace=anom_key.namespace)

    @staticmethod
    def _convert_key_from_datastore(datastore_key):
        return Key.from_path(*datastore_key.flat_path, namespace=datastore_key.namespace)

    def _prepare_to_store(self, key, unindexed, data):
        datastore_key = self._convert_key_to_datastore(key)
        entity = datastore.Entity(datastore_key, unindexed)
        for name, value in data:
            if isinstance(value, Key):
                value = self._convert_key_to_datastore(value)

            entity[name] = value

        return entity

    def _prepare_to_load(self, entity):
        data = {}
        for name, value in entity.items():
            if isinstance(value, datastore.Key):
                value = self._convert_key_from_datastore(value)

            data[name] = value

        return data
