from collections import namedtuple
from threading import RLock
from weakref import WeakValueDictionary

from .adapter import PutRequest, get_adapter
from .query import PropertyFilter, Query

#: The set of known models.  This is used to look up model classes at
#: runtime by their kind.
_known_models = WeakValueDictionary()
_known_models_lock = RLock()

#: Canary value for unset properties.
NotFound = type("NotFound", (object,), {})()

#: Canary value for properties that should be skipped when loading
#: entities from Datastore.
Skip = type("Skip", (object,), {})()


def classname(ob):
    "Returns the name of ob's class."
    return type(ob).__name__


class KeyLike:
    """Base class for objects that should be treated as if they are
    datastore keys (for example, when comparing two objects with one
    another).
    """


class Key(KeyLike, namedtuple("Key", ("kind", "id_or_name", "parent", "namespace"))):
    """A Datastore key.

    Parameters:
      kind(str or model): The Datastore kind this key represents.
      id_or_name(int or str): The id or name of this key.
      parent(anom.Key, optional): This key's ancestor.
      namespace(str, optional): This key's namespace.

    Attributes:
      kind(str): This key's kind.
      id_or_name(int or str or None): This key's integer id or string
        name.  This is ``None`` for partial keys.
      parent(anom.Key or None): This key's ancestor.
      namespace(str or None): This key's namespace.
    """

    def __new__(cls, kind, id_or_name=None, parent=None, namespace=None):
        if isinstance(kind, model):
            kind = kind._kind

        if parent and parent.is_partial:
            raise ValueError("Cannot use partial Keys as parents.")

        return super().__new__(cls, kind, id_or_name, parent, namespace)

    @classmethod
    def from_path(cls, *path, namespace=None):
        """Build up a Datastore key from a path.

        Parameters:
          \*path(tuple[str or int]): The path segments.
          namespace(str): An optional namespace for the key. This is
            applied to each key in the tree.

        Returns:
          anom.Key: The Datastore represented by the given path.
        """
        parent = None
        for i in range(0, len(path), 2):
            parent = cls(*path[i:i + 2], parent=parent, namespace=namespace)

        return parent

    @property
    def path(self):
        "tuple: The full Datastore path represented by this key."
        prefix = ()
        if self.parent:
            prefix = self.parent.path

        if self.id_or_name:
            return prefix + (self.kind, self.id_or_name)

        return prefix + (self.kind,)

    @property
    def is_partial(self):
        "bool: ``True`` if this key doesn't have an id yet."
        return len(self.path) % 2 != 0

    @property
    def int_id(self):
        "int: This key's numeric id."
        id_or_name = self.id_or_name
        if id_or_name is not None and isinstance(id_or_name, int):
            return id_or_name
        return None

    @property
    def str_id(self):
        "str: This key's string id."
        id_or_name = self.id_or_name
        if id_or_name is not None and isinstance(id_or_name, str):
            return id_or_name
        return None

    def get_model(self):
        """Get the model class for this Key.

        Raises:
          RuntimeError: If a model isn't registered for the Key's
            kind.

        Returns:
          type: A Model class.
        """
        return lookup_model_by_kind(self.kind)

    def delete(self):
        """Delete the entity represented by this Key from Datastore.
        """
        return delete_multi([self])

    def get(self):
        """Get the entity represented by this Key from Datastore.

        Returns:
          Model: The entity or ``None`` if it does not exist.
        """
        return get_multi([self])[0]

    def __repr__(self):
        return f"Key({self.kind!r}, {self.id_or_name!r}, parent={self.parent!r}, namespace={self.namespace!r})"

    def __hash__(self):
        return hash(tuple(self))

    def __eq__(self, other):
        if not isinstance(other, KeyLike):
            return False

        if self is other:
            return True

        if other.parent != self.parent or \
           other.namespace != self.namespace:
            return False

        return self.path == other.path

    def __ne__(self, other):
        return not (self == other)


class Property:
    """Base class for Datastore model properties.

    The property lifecycle is as follows:

    * :meth:`__init__` is called every time a property is defined on a
      model class.
    * :meth:`validate` is called every time a value is assigned to a
      property on a model instance.
    * :meth:`prepare_to_load` is called before a property is assigned
      to a model instance that is being loaded from Datastore.
    * :meth:`prepare_to_store` is called before a property is
      persisted from a model instance to Datastore.

    Parameters:
      name(str, optional): The name of this property on the Datastore
        entity.  Defaults to the name of this property on the model.
      default(object, optional): The property's default value.
      indexed(bool, optional): Whether or not this property should be
        indexed.  Defaults to ``False``.
      indexed_if(callable, optional): Whether or not this property
        should be indexed when the callable returns ``True``.
        Defaults to ``None``.
      optional(bool, optional): Whether or not this property is
        optional.  Defaults to ``False``.  Required-but-empty values
        cause models to raise an exception before data is persisted.
      repeated(bool, optional): Whether or not this property is
        repeated.  Defaults to ``False``.  Optional repeated
        properties default to an empty list.
    """

    #: The types of values that may be assigned to this property.
    _types = ()

    def __init__(self, *, name=None, default=None, indexed=False, indexed_if=None, optional=False, repeated=False):
        self.indexed = indexed or bool(indexed_if)
        self.indexed_if = indexed_if
        self.optional = optional
        self.repeated = repeated

        self.default = self.validate(default) if default is not None else None

        self._name_on_entity = name
        self._name_on_model = None

    @property
    def name_on_entity(self):
        "str: The name of this Property inside the Datastore entity."
        return self._name_on_entity

    @property
    def name_on_model(self):
        "str: The name of this Property on the Model instance."
        return self._name_on_model

    @property
    def is_none(self):
        "PropertyFilter: A filter that checks if this value is None."
        if not self.optional:
            raise TypeError("Required properties cannot be compared against None.")
        return self == None  # noqa

    def validate(self, value):
        """Validates that `value` can be assigned to this Property.

        Parameters:
          value: The value to validate.

        Raises:
          TypeError: If the type of the assigned value is invalid.

        Returns:
          The value that should be assigned to the entity.
        """
        if isinstance(value, self._types):
            return value

        elif self.optional and value is None:
            return value

        elif self.repeated and isinstance(value, (tuple, list)) and all(isinstance(x, self._types) for x in value):
            return value

        else:
            raise TypeError(f"Value of type {classname(value)} assigned to {classname(self)} property.")

    def prepare_to_load(self, entity, value):
        """Prepare `value` to be loaded into a Model.  Called by the
        model for each Property, value pair contained in the persisted
        data when loading it from an adapter.

        Parameters:
          entity(Model): The entity to which the value belongs.
          value: The value being loaded.

        Returns:
          The value that should be assigned to the entity.
        """
        return value

    def prepare_to_store(self, entity, value):
        """Prepare `value` for storage.  Called by the Model for each
        Property, value pair it contains before handing the data off
        to an adapter.

        Parameters:
          entity(Model): The entity to which the value belongs.
          value: The value being stored.

        Raises:
          RuntimeError: If this property is required but no value was
            assigned to it.

        Returns:
          The value that should be persisted.
        """
        if value is None and not self.optional:
            raise RuntimeError(f"Property {self.name_on_model} requires a value.")
        return value

    def __set_name__(self, ob, name):
        self._name_on_entity = self.name_on_entity or name
        self._name_on_model = name

    def __get__(self, ob, obtype):
        if ob is None:
            return self

        value = ob._data.get(self.name_on_entity, NotFound)
        if value is NotFound:
            if self.default is not None:
                return self.default

            elif self.repeated:
                value = ob._data[self.name_on_entity] = []

            else:
                return None

        return value

    def __set__(self, ob, value):
        ob._data[self.name_on_entity] = self.validate(value)

    def __delete__(self, ob):
        del ob._data[self.name_on_entity]

    def _build_filter(self, op, value):
        if not self.indexed:
            raise TypeError(f"{self.name_on_model} is not indexed.")
        return PropertyFilter(self.name_on_entity, op, self.validate(value))

    def __eq__(self, value):
        return self._build_filter("=", value)

    def __le__(self, value):
        return self._build_filter("<=", value)

    def __ge__(self, value):
        return self._build_filter(">=", value)

    def __lt__(self, value):
        return self._build_filter("<", value)

    def __gt__(self, value):
        return self._build_filter(">", value)

    def __neg__(self):
        return "-" + self.name_on_entity

    def __pos__(self):
        return self.name_on_entity


class _adapter:
    def __get__(self, ob, obtype):
        return get_adapter()


class model(type):
    """Metaclass of Model classes.

    Parameters:
      poly(bool, optional): Determines if the model should be
        polymorphic or not.  Subclasses of polymorphic models are all
        stored under the same kind.

    Attributes:
      _adapter(Adapter): A computed property that returns the adapter
        for this model class.
      _is_child(bool): Whether or not this is a child model in a
        polymorphic hierarchy.
      _is_root(bool): Whether or not this is the root model in a
        polymorphic hierarchy.
      _kind(str): The underlying Datastore kind of this model.
      _kinds(list[str]): The list of kinds in this model's hierarchy.
      _properties(dict): A dict of all of the properties defined on
        this model.
    """

    #: The name of the field that holds the flattened class hierarchy
    #: on polymodel entities.
    _kinds_name = "^k"

    def __new__(cls, classname, bases, attrs, poly=False, **kwargs):
        attrs["_adapter"] = _adapter()
        attrs["_is_child"] = is_child = False
        attrs["_is_root"] = poly
        attrs["_kind"] = kind = attrs.pop("_kind", classname)
        attrs["_kinds"] = kinds = [kind]

        # Collect all of the properties defined on this model.
        attrs["_properties"] = properties = {}
        for name, value in attrs.items():
            if isinstance(value, Property):
                properties[name] = value

        # Collect all of the properties and kinds defined on parents
        # of this model.
        for base in bases:
            if not isinstance(base, model):
                continue

            # Avoid adding the base Model class to kinds.
            if "Model" in globals() and base is Model:
                continue

            kinds.extend(base._kinds)
            if base._is_polymorphic:  # Poly bases "infect" everything below them.
                attrs["_is_child"] = is_child = True
                attrs["_kind"] = base._kind

            for name, prop in base._properties.items():
                if name not in properties:
                    properties[name] = prop

        clazz = type.__new__(cls, classname, bases, attrs)

        # Ensure that a single model maps to a single kind at runtime.
        with _known_models_lock:
            if kind in _known_models and not is_child:
                raise TypeError(f"Multiple models for kind {kind!r}.")

            _known_models[kind] = clazz

        return clazz

    @property
    def _is_polymorphic(self):
        "bool: True if this child belongs to a polymorphic hierarchy."
        return self._is_root or self._is_child


class Model(metaclass=model):
    """Base class for Datastore models.

    Attributes:
      key(anom.Key): The Datastore Key for this entity.  If the entity
        was never stored then the Key is going to be partial.

    Note:
      Hooks are only called when dealing with individual entities via
      their keys.  They *do not* run when entities are loaded from a
      query.
    """

    def __init__(self, *, key=None, **properties):
        self.key = key or Key(self._kind)

        self._data = {}
        for name, value in properties.items():
            if name not in self._properties:
                raise TypeError(f"{classname(self)}() does not take a {name!r} parameter.")

            setattr(self, name, value)

    def __iter__(self):
        for name, prop in self._properties.items():
            yield prop.name_on_entity, prop.prepare_to_store(self, getattr(self, name))

        # Polymorphic models need to keep track of their bases.
        if type(self)._is_polymorphic:
            yield model._kinds_name, self._kinds

    @classmethod
    def _load(cls, key, data):
        # Polymorphic models need to instantiate leaf classes.
        if cls._is_polymorphic and model._kinds_name in data:
            name = data[model._kinds_name][0]
            cls = lookup_model_by_kind(name)

        instance = cls()
        instance.key = key

        for name, prop in instance._properties.items():
            value = prop.prepare_to_load(instance, data.get(name))
            if value is not Skip:
                instance._data[name] = value

        return instance

    @property
    def unindexed_properties(self):
        "tuple[str]: The names of all the unindexed properties on this entity."
        properties = ()
        for name, prop in self._properties.items():
            if not prop.indexed or prop.indexed_if and prop.indexed_if(self, prop, name):
                properties += (prop.name_on_entity,)

        return properties

    @classmethod
    def pre_get_hook(cls, key):
        """A hook that runs before an entity is loaded from Datastore.
        Raising an exception here will prevent the entity from being
        loaded.

        Parameters:
          key(anom.Key): The datastore Key of the entity being loaded.
        """

    def post_get_hook(self):
        """A hook that runs after an entity has been loaded from
        Datastore.
        """

    @classmethod
    def get(cls, id_or_name, *, parent=None, namespace=None):
        """Get an entity by id.

        Parameters:
          id_or_name(int or str): The entity's id.
          parent(anom.Key, optional): The entity's parent Key.
          namespace(str, optional): The entity's namespace.

        Returns:
          Model: An entity or ``None`` if the entity doesn't exist in
          Datastore.
        """
        return Key(cls, id_or_name, parent=parent, namespace=namespace).get()

    @classmethod
    def pre_delete_hook(cls, key):
        """A hook that runs before an entity is deleted.  Raising an
        exception here will prevent the entity from being deleted.

        Parameters:
          key(anom.Key): The datastore Key of the entity being deleted.
        """

    @classmethod
    def post_delete_hook(cls, key):
        """A hook that runs after an entity has been deleted.

        Parameters:
          key(anom.Key): The datastore Key of the entity being deleted.
        """

    def delete(self):
        """Delete this entity from Datastore.

        Raises:
          RuntimeError: If this entity was never stored (i.e. if its
            key is partial).
        """
        return delete_multi([self.key])

    def pre_put_hook(self):
        """A hook that runs before this entity is persisted.  Raising
        an exception here will prevent the entity from being persisted.
        """

    def post_put_hook(self):
        """A hook that runs after this entity has been persisted.
        """

    def put(self):
        """Persist this entity to Datastore.
        """
        return put_multi([self])[0]

    @classmethod
    def query(cls, **options):
        """Return a new query for this Model.

        Parameters:
          \**options(dict): Parameters to pass to the :class:`Query`
            constructor.

        Returns:
          Query: The new query.
        """
        return Query(cls, **options)

    def __repr__(self):
        constructor = type(self).__name__
        properties = ("key",) + tuple(self._properties.keys())
        props = ", ".join(f"{name}={getattr(self, name)!r}" for name in properties)
        return f"{constructor}({props})"

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False

        if self is other:
            return True

        if self.key != other.key:
            return False

        for name in self._properties:
            if getattr(self, name) != getattr(other, name):
                return False

        return True

    def __ne__(self, other):
        return not (self == other)


def lookup_model_by_kind(kind):
    """Look up the model instance for a given Datastore kind.

    Parameters:
      kind(str)

    Raises:
      RuntimeError: If a model for the given kind has not been
        defined.

    Returns:
      model: The model class.
    """
    model = _known_models.get(kind)
    if model is None:
        raise RuntimeError(f"Model for kind {kind!r} not found.")
    return model


def delete_multi(keys):
    """Delete a set of entitites from Datastore by their
    respective keys.

    Note:
      This uses the adapter that is tied to the first model in the list.
      If the keys have disparate adapters this function may behave in
      unexpected ways.

    Warning:
      You must pass a **list** and not a generator or some other kind
      of iterable to this function as it has to iterate over the list
      of keys multiple times.

    Parameters:
      keys(list[anom.Key]): The list of keys whose entities to delete.

    Raises:
      RuntimeError: If the given set of keys have models that use
        a disparate set of adapters or if any of the keys are
        partial.
    """
    if not keys:
        return

    adapter = None
    for key in keys:
        if key.is_partial:
            raise RuntimeError(f"Key {key!r} is partial.")

        model = lookup_model_by_kind(key.kind)
        if adapter is None:
            adapter = model._adapter

        model.pre_delete_hook(key)

    adapter.delete_multi(keys)
    for key in keys:
        # Micro-optimization to avoid calling get_model.  This is OK
        # to do here because we've already proved that a model for
        # that kind exists in the previous block.
        model = _known_models[key.kind]
        model.post_delete_hook(key)


def get_multi(keys):
    """Get a set of entities from Datastore by their respective keys.

    Note:
      This uses the adapter that is tied to the first model in the
      list.  If the keys have disparate adapters this function may
      behave in unexpected ways.

    Warning:
      You must pass a **list** and not a generator or some other kind
      of iterable to this function as it has to iterate over the list
      of keys multiple times.

    Parameters:
      keys(list[anom.Key]): The list of keys whose entities to get.

    Raises:
      RuntimeError: If the given set of keys have models that use
        a disparate set of adapters or if any of the keys are
        partial.

    Returns:
      list[Model]: Entities that do not exist are going to be None
      in the result list.  The order of results matches the order
      of the input keys.
    """
    if not keys:
        return []

    adapter = None
    for key in keys:
        if key.is_partial:
            raise RuntimeError(f"Key {key!r} is partial.")

        model = lookup_model_by_kind(key.kind)
        if adapter is None:
            adapter = model._adapter

        model.pre_get_hook(key)

    entities_data, entities = adapter.get_multi(keys), []
    for key, entity_data in zip(keys, entities_data):
        if entity_data is None:
            entities.append(None)
            continue

        # Micro-optimization to avoid calling get_model.  This is OK
        # to do here because we've already proved that a model for
        # that kind exists in the previous block.
        model = _known_models[key.kind]
        entity = model._load(key, entity_data)
        entities.append(entity)
        entity.post_get_hook()

    return entities


def put_multi(entities):
    """Persist a set of entities to Datastore.

    Note:
      This uses the adapter that is tied to the first Entity in the
      list.  If the entities have disparate adapters this function may
      behave in unexpected ways.

    Warning:
      You must pass a **list** and not a generator or some other kind
      of iterable to this function as it has to iterate over the list
      of entities multiple times.

    Parameters:
      entities(list[Model]): The list of entities to persist.

    Raises:
      RuntimeError: If the given set of models use a disparate set of
        adapters.

    Returns:
      list[Model]: The list of persisted entitites.
    """
    if not entities:
        return []

    adapter, requests = None, []
    for entity in entities:
        if adapter is None:
            adapter = entity._adapter

        adapter = entity._adapter
        requests.append(PutRequest(entity.key, entity.unindexed_properties, entity))
        entity.pre_put_hook()

    keys = adapter.put_multi(requests)
    for key, entity in zip(keys, entities):
        entity.key = key
        entity.post_put_hook()

    return entities
