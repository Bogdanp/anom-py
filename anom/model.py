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


class Key:
    """A Datastore key.

    Parameters:
      kind(str or model): The Datastore kind this key represents.
      path(int or str): The id or name of this key.
      parent(anom.Key, optional): This key's ancestor.
      namespace(str, optional): This key's namespace.
    """

    def __init__(self, kind, *path, parent=None, namespace=None):
        if isinstance(kind, model):
            kind = kind._kind

        if parent and not parent.is_complete:
            raise ValueError("Cannot use incomplete Keys as parents.")

        elif parent:
            self.path = parent.path + (kind,) + path

        else:
            self.path = (kind,) + path

        self.kind = kind
        self.parent = parent
        self.namespace = namespace

    @property
    def is_complete(self):
        "bool: Whether or not this key has an id."
        return len(self.path) % 2 == 0

    @property
    def id_or_name(self):
        "id or str: This key's id."
        if not self.is_complete:
            return None
        return self.path[-1]

    @property
    def int_id(self):
        "int: This key's numeric id."
        id_or_name = self.id_or_name
        if id_or_name is not None and isinstance(id_or_name, int):
            return id_or_name
        return None

    @property
    def str_id(self):
        "str: This key's numeric id."
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
        model = _known_models.get(self.kind)
        if model is None:
            raise RuntimeError("There is no Model class for kind {kind!r}.".format(kind=self.kind))
        return model

    def delete(self):
        """Delete the entity represented by this Key from Datastore.
        """
        return delete_multi([self])

    def get(self):
        """Get the entity represented by this Key from Datastore.

        Returns:
          Model: Or None if the entity does not exist.
        """
        return get_multi([self])[0]

    def __repr__(self):
        path = ", ".join(repr(elem) for elem in self.path)
        return "Key({path}, parent={parent!r}, namespace={namespace!r})".format(
            path=path, parent=self.parent, namespace=self.namespace
        )

    def __hash__(self):
        return hash(self.path) + hash(self.parent) + hash(self.namespace)

    def __eq__(self, other):
        if not isinstance(other, Key):
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
      optional(bool, optional): Whether or not this property is
        optional.  Defaults to ``False``.  Required-but-empty values
        cause models to raise an exception before data is persisted.
      repeated(bool, optional): Whether or not this property is
        repeated.  Defaults to ``False``.  Optional repeated
        properties default to an empty list.
    """

    #: The types of values that may be assigned to this property.
    _types = ()

    def __init__(self, *, name=None, default=None, indexed=False, optional=False, repeated=False):
        self.default = self.validate(default) if default else None
        self.indexed = indexed
        self.optional = optional
        self.repeated = repeated

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

    #: Alias of is_none.
    is_null = is_none

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
            raise TypeError("Value of type {value_class} assigned to {self_class} property.".format(
                value_class=classname(value), self_class=classname(self)
            ))

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
            raise RuntimeError("Property {} requires a value.".format(self.name_on_model))
        return value

    def __set_name__(self, ob, name):
        self._name_on_entity = self.name_on_entity or name
        self._name_on_model = name

    def __get__(self, ob, obtype):
        if ob is None:
            return self

        value = ob._data.get(self.name_on_entity, NotFound)
        if value is NotFound:
            if self.default:
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
            raise TypeError("{} is not indexed.".format(self.name_on_model))
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
    def __new__(cls, classname, bases, attrs):
        # Collect all of the properties defined on this model.
        attrs["_adapter"] = _adapter()
        attrs["_properties"] = properties = {}
        attrs["_unindexed"] = unindexed = ()
        for name, value in attrs.items():
            if isinstance(value, Property):
                properties[name] = value

                if not value.indexed:
                    unindexed += (name,)

        # Ensure that a single model maps to a single kind at runtime.
        kind = attrs.setdefault("_kind", classname)
        model = super().__new__(cls, classname, bases, attrs)

        with _known_models_lock:
            if kind in _known_models:
                raise TypeError("Multiple models for kind {!r}.".format(kind))

            _known_models[kind] = model

        return model


class Model(metaclass=model):
    """Base class for Datastore models.

    Attributes:
      key(anom.Key): The Datastore Key for this entity.  If the entity
        was never stored then the Key is going to be incomplete.

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
                raise TypeError("{self_class}() does not take a {name!r} parameter.".format(
                    self_class=classname(self), name=name,
                ))

            setattr(self, name, value)

    def __iter__(self):
        for name, prop in self._properties.items():
            yield prop.name_on_entity, prop.prepare_to_store(self, getattr(self, name))

    @classmethod
    def _load(cls, key, data):
        instance = cls()
        instance.key = key

        for name, prop in instance._properties.items():
            value = prop.prepare_to_load(instance, data.get(name))
            if value is not Skip:
                setattr(instance, name, value)

        return instance

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
            key is incomplete).
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
        props = ", ".join("{name}={value!r}".format(name=name, value=getattr(self, name)) for name in properties)
        return "{constructor}({props})".format(constructor=constructor, props=props)

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

    Returns:
      Model: Or None if a model does not exist for the given kind.
    """
    return _known_models.get(kind)


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
        incomplete.
    """
    if not keys:
        return

    adapter = None
    for key in keys:
        if not key.is_complete:
            raise RuntimeError("Key {!r} is incomplete.".format(key))

        model = key.get_model()
        if adapter is None:
            adapter = key.get_model()._adapter

        model.pre_delete_hook(key)

    adapter.delete_multi(keys)
    for key in keys:
        model = _known_models[key.kind]  # Micro-optimization, avoids calling get_model
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
        incomplete.

    Returns:
      list[Model]: Entities that do not exist are going to be None
      in the result list.  The order of results matches the order
      of the input keys.
    """
    if not keys:
        return []

    adapter = None
    for key in keys:
        if not key.is_complete:
            raise RuntimeError("Key {!r} is incomplete.".format(key))

        model = key.get_model()
        if adapter is None:
            adapter = key.get_model()._adapter

        model.pre_get_hook(key)

    entities_data, entities = adapter.get_multi(keys), []
    for key, entity_data in zip(keys, entities_data):
        if entity_data is None:
            entities.append(None)
            continue

        model = _known_models[key.kind]  # Micro-optimization, avoids calling get_model
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
        requests.append(PutRequest(entity.key, entity._unindexed, entity))
        entity.pre_put_hook()

    keys = adapter.put_multi(requests)
    for key, entity in zip(keys, entities):
        entity.key = key
        entity.post_put_hook()

    return entities
