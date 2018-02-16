from contextlib import contextmanager
from threading import local

_default_namespace = ""
_namespace = local()
_namespace.current = _default_namespace


def set_default_namespace(namespace=None):
    """Set the global default namespace (and the thread-local default).

    Parameters:
      namespace(str): The namespace to set as the global default.

    Returns:
      str: The input namespace
    """
    global _default_namespace
    _namespace.current = _default_namespace = namespace or ""
    return _default_namespace


def get_namespace():
    """Get the current thread-local default namespace.

    Returns:
      str: The current thread-local default namespace.
    """
    try:
        return _namespace.current
    except AttributeError:
        _namespace.current = _default_namespace
        return _namespace.current


def set_namespace(namespace=None):
    """Set the current thread-local default namespace.

    Parameters:
      namespace(str): namespace to set as the current thread-local default.

    Returns:
      None
    """
    if namespace is None:
        namespace = _default_namespace
    _namespace.current = namespace


@contextmanager
def namespace(namespace):
    """Context manager for setting the current thread-local default namespace.
    Exiting the context sets the thread-local default namespace back to the
    global default namespace.

    Parameters:
      namespace(str): namespace to set as the current thread-local default.

    Returns:
      None
    """
    set_namespace(namespace)
    try:
        yield
    finally:
        set_namespace(None)
