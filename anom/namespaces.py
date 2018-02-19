from contextlib import contextmanager
from threading import local

_default_namespace = ""
_namespace = local()


def set_default_namespace(namespace=None):
    """Set the global default namespace.

    Parameters:
      namespace(str): The namespace to set as the global default.

    Returns:
      str: The input namespace.
    """
    global _default_namespace
    _default_namespace = namespace or ""
    return _default_namespace


def get_namespace():
    """str: The namespace for the current thread.
    """
    try:
        return _namespace.current
    except AttributeError:
        return _default_namespace


def set_namespace(namespace=None):
    """Set the current thread-local default namespace.  If namespace
    is None, then the thread-local namespace value is removed, forcing
    `get_namespace()` to return the global default namespace on
    subsequent calls.

    Parameters:
      namespace(str): namespace to set as the current thread-local
        default.

    Returns:
      None
    """
    if namespace is None:
        try:
            del _namespace.current
        except AttributeError:
            pass

    else:
        _namespace.current = namespace


@contextmanager
def namespace(namespace):
    """Context manager for stacking the current thread-local default
    namespace.  Exiting the context sets the thread-local default
    namespace back to the previously-set namespace.  If there is no
    previous namespace, then the thread-local namespace is cleared.

    Example:
      >>> with namespace("foo"):
      ...   with namespace("bar"):
      ...     assert get_namespace() == "bar"
      ...   assert get_namespace() == "foo"

      >>> assert get_namespace() == ""

    Parameters:
      namespace(str): namespace to set as the current thread-local
        default.

    Returns:
      None
    """
    try:
        current_namespace = _namespace.current
    except AttributeError:
        current_namespace = None

    set_namespace(namespace)
    try:
        yield
    finally:
        set_namespace(current_namespace)
