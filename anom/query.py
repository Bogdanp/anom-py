from collections import namedtuple


class PropertyFilter(namedtuple("PropertyFilter", ("name", "operator", "value"))):
    """Represents an individual filter on a Property within a Query.
    """


class PropertyOrder(namedtuple("PropertyOrder", ("name", "order"))):
    """Represents the order of a Property within a Query.
    """
