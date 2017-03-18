from collections import namedtuple

#: The global adapter instance.
_adapter = None


def get_adapter():
    """Get the current global Adapter instance.

    Returns:
      Adapter: Or ``None`` if there is no global adapter instance.
    """
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
    """Represents requests to persist an individual Models.

    Parameters:
      key(anom.Key): A datastore Key.
      unindexed(list[str]): A list of properties that should not be indexed.
      properties(iter[tuple[str, Property]]): An iterable representing
        the properties that should be stored by this put.
    """


class Adapter:
    """Abstract base class for Datastore adapters.  Adapters determine
    how your :class:`Models<Model>` interact with the Datastore.

    Parameters:
      project(str): The project this Adapter should connect to.
      namespace(str): The namespace inside which this Adapter should
        operate by default.  Individual Datastore Keys may specify
        their own namespaces and override this.
    """

    def __init__(self, *, project=None, namespace=None):
        self.project = project
        self.namespace = namespace

    def delete_multi(self, keys):  # pragma: no cover
        """Delete a list of entities from the Datastore by their
        respective keys.

        Parameters:
          keys(list[anom.Key]): A list of datastore Keys to delete.
        """
        raise NotImplementedError

    def get_multi(self, keys):  # pragma: no cover
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

    def put_multi(self, requests):  # pragma: no cover
        """Store multiple entities into the Datastore.

        Parameters:
          requests(list[PutRequest]): A list of datastore requets to
            persist a set of entities.

        Returns:
          list[anom.Key]: The list of completed keys for each stored
          entity.
        """
        raise NotImplementedError
