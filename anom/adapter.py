from collections import namedtuple

#: The global adapter instance.
_adapter = None


def get_adapter():
    """Get the current global Adapter instance.
    """
    return _adapter


def set_adapter(adapter):
    """Set the global Adapter instance.
    """
    global _adapter
    _adapter = adapter
    return _adapter


class PutRequest(namedtuple("PutRequest", ("key", "unindexed", "properties"))):
    """Represents requests to persist an individual Models.

    Parameters:
      key(Key)
      unindexed(str list)
      properties(iterable)
    """


class Adapter:
    """Base class for Datastore adapters.  Adapters determine your
    :class:`.model.Model<Models>` interact with the Datastore.

    Parameters:
      project(str)
      namespace(str)
    """

    def __init__(self, *, project=None, namespace=None):
        self.project = project
        self.namespace = namespace

    def delete_multi(self, keys):  # pragma: no cover
        """Delete a list of entities from the Datastore by their
        respective keys.

        Parameters:
          keys(Key list)
        """
        raise NotImplementedError

    def get_multi(self, keys):  # pragma: no cover
        """Get multiple entities from the Datastore by their
        respective keys.

        Parameters:
          keys(Key list)

        Returns:
          dict list: A list of dictionaries of data that can be loaded
          into individual Models.  Entries for Keys that cannot not be
          found are going to be None.
        """
        raise NotImplementedError

    def put_multi(self, requests):  # pragma: no cover
        """Store multiple entities into the Datastore.

        Parameters:
          requests(PutRequest list)

        Returns:
          Key list: The list of complete keys for each stored model.
        """
        raise NotImplementedError
