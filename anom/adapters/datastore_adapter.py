from google.cloud import datastore
from threading import local

from .. import Adapter, Key
from ..adapter import QueryResponse


class DatastoreAdapter(Adapter):
    """A Google Cloud Datastore adapter based on :mod:`google.cloud.datastore`.
    """

    _state = local()

    @property
    def client(self):
        """datastore.Client: The underlying datastore client for this
        adapter instance.  This property is thread-local.
        """
        client = getattr(self._state, "client", None)
        if client is None:
            client = self._state.client = datastore.Client(
                project=self.project,
                namespace=self.namespace,
            )
        return client

    def delete_multi(self, keys):
        self.client.delete_multi(self._convert_key_to_datastore(key) for key in keys)

    def get_multi(self, keys):
        datastore_keys = [self._convert_key_to_datastore(key) for key in keys]
        request_keys = set(datastore_keys)
        found, missing, deferred = [], [], []
        while True:
            found.extend(self.client.get_multi(
                request_keys,
                missing=missing,
                deferred=deferred
            ))
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

    def _convert_key_to_datastore(self, anom_key):
        return self.client.key(*anom_key.path, namespace=anom_key.namespace)

    def _convert_key_from_datastore(self, datastore_key):
        return Key.from_path(*datastore_key.flat_path, namespace=datastore_key.namespace)

    def _prepare_to_store(self, key, unindexed, data):
        """Populate an Entity with data from the Model.

        Parameters:
          key(Key)
          unindexed(str list)
          data(iterable)

        Returns:
          datastore.Entity
        """
        datastore_key = self._convert_key_to_datastore(key)
        entity = datastore.Entity(datastore_key, unindexed)
        for name, value in data:
            if isinstance(value, Key):
                value = self._convert_key_to_datastore(value)

            entity[name] = value

        return entity

    def _prepare_to_load(self, entity):
        """Preprocess Entity data before returning it to the Model.

        Parameters:
          entity(datastore.Entity)

        Returns:
          dict
        """
        data = {}
        for name, value in entity.items():
            if isinstance(value, datastore.Key):
                value = self._convert_key_from_datastore(value)

            data[name] = value

        return data
