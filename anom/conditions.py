def is_default(entity, prop, name):
    "bool: True if the value of a property is equal to its default."
    return getattr(entity, name) == prop.default


def is_not_default(entity, prop, name):
    "bool: True if the value of a property is not equal to its default."
    return getattr(entity, name) != prop.default


def is_empty(entity, prop, name):
    "bool: True if the value of a property is not set."
    return name not in entity._data


def is_not_empty(entity, prop, name):
    "bool: True if the value of a  property is set."
    return name in entity._data


def is_none(entity, prop, name):
    "bool: True if the value of a property is None."
    return is_not_empty(entity, prop, name) and getattr(entity, name) is None


def is_not_none(entity, prop, name):
    "bool: True if the value of a property is not None."
    return is_not_empty(entity, prop, name) and name in entity._data and getattr(entity, name) is not None


def is_true(entity, prop, name):
    "bool: True if the value of a property is True."
    return is_not_empty(entity, prop, name) and name in entity._data and bool(getattr(entity, name))


def is_false(entity, prop, name):
    "bool: True if the value of a property is False."
    return is_not_empty(entity, prop, name) and name in entity._data and not bool(getattr(entity, name))
