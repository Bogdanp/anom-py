import warnings

from .datastore_adapter import DatastoreAdapter  # noqa

try:
    from .memcache_adapter import MemcacheAdapter  # noqa
except ImportError:  # pragma: no cover
    warnings.warn(
        "MemcacheAdapter could not be imported.  Install anom with `pip "
        "install anom[memcache]` to add memcache support.",
        ImportWarning, stacklevel=2
    )
