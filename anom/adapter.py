from collections import namedtuple

#: The global adapter instance.
_adapter = None


def get_adapter():
    """Get the current global Adapter instance.

    Returns:
      Adapter: The global adapter.  If no global adapter was set, this
      instantiates a :class:`adapters.DatastoreAdapter` and makes it
      the default.
    """
    if _adapter is None:
        from .adapters import DatastoreAdapter
        return set_adapter(DatastoreAdapter())
    return _adapter


def set_adapter(adapter):
    """Set the global Adapter instance.

    Parameters:
      adapter(Adapter): The instance to set as the global adapter.
        Model-specific adapters will not be replaced.

    Returns:
      Adapter: The input adapter.
    """
    global _adapter
    _adapter = adapter
    return _adapter


class PutRequest(namedtuple("PutRequest", ("key", "unindexed", "properties"))):
    """Represents requests to persist individual Models.

    Parameters:
      key(anom.Key): A datastore Key.
      unindexed(list[str]): A list of properties that should not be indexed.
      properties(iter[tuple[str, Property]]): An iterable representing
        the properties that should be stored by this put.
    """


class QueryResponse(namedtuple("QueryResponse", ("entities", "cursor"))):
    """Represents query responses from Datastore.

    Parameters:
      entities(list[tuple[anom.Key, dict]]): The list of results.
      cursor(str): The cursor that points to the next page of results.
        This value must be url-safe.
    """


class Adapter:  # pragma: no cover
    """Abstract base class for Datastore adapters.  Adapters determine
    how your :class:`Models<Model>` interact with the Datastore.
    """

    def delete_multi(self, keys):
        """Delete a list of entities from the Datastore by their
        respective keys.

        Parameters:
          keys(list[anom.Key]): A list of datastore Keys to delete.
        """
        raise NotImplementedError

    def get_multi(self, keys):
        """Get multiple entities from the Datastore by their
        respective keys.

        Parameters:
          keys(list[anom.Key]): A list of datastore Keys to get.

        Returns:
          list[dict]: A list of dictionaries of data that can be loaded
          into individual Models.  Entries for Keys that cannot be
          found are going to be ``None``.
        """
        raise NotImplementedError

    def put_multi(self, requests):
        """Store multiple entities into the Datastore.

        Parameters:
          requests(list[PutRequest]): A list of datastore requets to
            persist a set of entities.

        Returns:
          list[anom.Key]: The list of full keys for each stored
          entity.
        """
        raise NotImplementedError

    def query(self, query, options):
        """Run a query against the datastore.

        Parameters:
          query(Query): The query to run.
          options(QueryOptions): Options that determine how the data
            should be fetched.

        Returns:
          QueryResponse: The query response from Datastore.
        """
        raise NotImplementedError

    def transaction(self, propagation):
        """Create a new Transaction object.

        Parameters:
          propagation(Transaction.Propagation): How the new
            transaction should be propagated with regards to any
            previously-created transactions.

        Returns:
          Transaction: The transaction.
        """
        raise NotImplementedError

    @property
    def in_transaction(self):
        "bool: True if the adapter is currently in a Transaction."
        raise NotImplementedError

    @property
    def current_transaction(self):
        "Transaction: The current Transaction or None."
        raise NotImplementedError
