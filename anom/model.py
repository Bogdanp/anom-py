from threading import RLock
from weakref import WeakValueDictionary

from .adapter import PutRequest, get_adapter
from .query import PropertyFilter, PropertyOrder

#: The set of known models.  This is used to look up model classes at
#: runtime by their kind.
_known_models = WeakValueDictionary()
_known_models_lock = RLock()

#: Canary value for unset properties.
NotFound = type("NotFound", (object,), {})()


def classname(ob):
    "Returns the name of ob's class."
    return type(ob).__name__


class Key:
    """A Datastore key.

    Parameters:
      kind(str)
      path(int or str)
      parent(Key)
      namespace(str)
    """

    def __init__(self, kind, *path, parent=None, namespace=None):
        if parent and not parent.is_complete:
            raise ValueError("Cannot use incomplete Keys as parents.")

        elif parent:
            self.path = parent.path + (kind,) + path

        else:
            self.path = (kind,) + path

        self.kind = kind
        self.parent = parent
        self.namespace = namespace

        self.is_complete = len(self.path) % 2 == 0
        self.id_or_name = None
        self.int_id = None
        self.str_id = None

        if self.is_complete:
            self.id_or_name = self.path[-1]

        if self.id_or_name is not None:
            if isinstance(self.id_or_name, int):
                self.int_id = self.id_or_name
            else:
                self.str_id = self.id_or_name

    def get_model(self):
        """Get the model class for this Key.

        Raises:
          RuntimeError: If a model isn't registered for the Key's
            kind.

        Returns:
          model: A Model class.
        """
        model = lookup_model_by_kind(self.kind)
        if model is None:
            raise RuntimeError(f"There is no Model class for kind {self.kind!r}.")
        return model

    def delete(self):
        """Delete the entity represented by this Key from Datastore.

        Returns:
          None
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
        return f"Key({path}, parent={self.parent!r}, namespace={self.namespace!r})"

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
    """

    #: The types of values that may be assigned to these types of
    #: Properties.
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
        "The name of this Property inside the Datastore entity."
        return self._name_on_entity

    @property
    def name_on_model(self):
        "The name of this Property on the Model instance."
        return self._name_on_model

    def validate(self, value):
        """Validates that `value` can be assigned to this Property.

        Parameters:
          value(ob)

        Raises:
          TypeError: If the type of the assigned value is invalid.

        Returns:
          ob: The potentially-modified value that should be assigned
          to this Property.
        """
        if isinstance(value, self._types):
            return value

        elif self.optional and value is None:
            return value

        elif self.repeated and isinstance(value, list) and all(isinstance(x, self._types) for x in value):
            return value

        else:
            raise TypeError(f"Value of type {classname(value)} assigned to {classname(self)} property.")

    def prepare_to_load(self, ob, value):
        """Prepare `value` to be loaded into a Model.  Called by the
        model for each Property, value pair contained in the persisted
        data when loading it from an adapter.
        """
        return value

    def prepare_to_store(self, ob, value):
        """Prepare `value` for storage.  Called by the Model for each
        Property, value pair it contains before handing the data off
        to an adapter.
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
        ob._data[self.name_on_entity] = None

    def _build_filter(self, op, value):
        if not self.indexed:
            raise RuntimeError(f"{self.name_on_model} is not indexed.")
        return PropertyFilter(self.name_on_entity, op, self.validate(value))

    def __contains__(self, value):
        if not self.repeated:
            raise RuntimeError(f"{self.name_on_model} is not a repeated property.")

        return self._build_filter("==", value)

    def __eq__(self, value):
        return self._build_filter("==", value)

    def __ne__(self, value):
        return self._build_filter("!=", value)

    def __le__(self, value):
        return self._build_filter("<=", value)

    def __ge__(self, value):
        return self._build_filter(">=", value)

    def __lt__(self, value):
        return self._build_filter("<", value)

    def __gt__(self, value):
        return self._build_filter(">", value)

    def __neg__(self):
        return PropertyOrder(self.name_on_entity, "desc")

    def __pos__(self):
        return PropertyOrder(self.name_on_entity, "asc")


class _adapter:
    def __get__(self, ob, obtype):
        adapter = get_adapter()
        if adapter is None:
            raise RuntimeError("No adapter set.")
        return adapter


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
                raise TypeError(f"Multiple models for kind {kind!r}.")

            _known_models[kind] = model

        return model


class Model(metaclass=model):
    """Base class for Datastore models.
    """

    def __init__(self, *, key=None, **params):
        self.key = key or Key(self._kind)

        self._data = {}
        for name, value in params.items():
            if name not in self._properties:
                raise TypeError(f"{classname(self)}() does not take a {name!r} parameter.")

            setattr(self, name, value)

    def __iter__(self):
        for name, prop in self._properties.items():
            yield prop.name_on_entity, prop.prepare_to_store(self, getattr(self, name))

    def _to_dict(self):
        # This is used to to avoid having to call `prepare_to_store`
        # on each property for every comparison.
        data = {}
        for name, prop in self._properties.items():
            data[prop.name_on_entity] = getattr(self, name)

        return data

    @classmethod
    def _load(cls, key, data):
        instance = cls()
        instance.key = key

        for name, prop in instance._properties.items():
            setattr(instance, name, prop.prepare_to_load(instance, data.get(name)))

        return instance

    def pre_delete_hook(self):
        """A hook that runs before this entity is deleted.  Raising an
        exception here will prevent the entity from being deleted.
        """

    def post_delete_hook(self):
        """A hook that runs after this entity is deleted.
        """

    def delete(self):
        """Delete this entity from Datastore.
        """
        if not self.key.is_complete:
            raise RuntimeError("Entity has an incomplete Key and cannot be deleted.")

        self.pre_delete_hook()
        self._adapter.delete_multi([self.key])
        self.post_delete_hook()

    def pre_put_hook(self):
        """A hook that runs before this entity is persisted.  Raising
        an exception here will prevent the entity from being persisted.
        """

    def post_put_hook(self):
        """A hook that runs after this entity is persisted.
        """

    def put(self):
        """Persist this entity to Datastore.
        """
        return put_multi([self])[0]

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

        return self._to_dict() == other._to_dict()

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

    Parameters:
      keys(Key list)

    Raises:
      RuntimeError: If the given set of keys have models that use
        a disparate set of adapters or if any of the keys are
        incomplete.

    Returns:
      None
    """
    adapter, _ = _collect_models_and_adapter(keys)
    return adapter.delete_multi(keys)


def get_multi(keys):
    """Get a set of entities from Datastore by their respective keys.

    Parameters:
      keys(Key list)

    Raises:
      RuntimeError: If the given set of keys have models that use
        a disparate set of adapters or if any of the keys are
        incomplete.

    Returns:
      Model list: Entities that do not exist are going to be None
      in the result list.  The order of results matches the order
      of the input keys.
    """
    adapter, models_by_kind = _collect_models_and_adapter(keys)
    entities_data, entities = adapter.get_multi(keys), []
    for key, entity_data in zip(keys, entities_data):
        if entity_data is None:
            entities.append(None)
            continue

        model = models_by_kind[key.kind]
        entities.append(model._load(key, entity_data))

    return entities


def put_multi(entities):
    """Persist a set of entities to Datastore.

    Parameters:
      entities(Model list)

    Raises:
      RuntimeError: If the given set of keys have models that use
        a disparate set of adapters or if any of the keys are
        incomplete.

    Returns:
      Model list: The list of persisted entitites.
    """
    adapter, requests = None, []
    for entity in entities:
        if adapter is not None and adapter != entity._adapter:
            raise RuntimeError("Cannot run put_multi across multiple Adapters.")

        adapter = entity._adapter
        entity.pre_put_hook()
        requests.append(PutRequest(entity.key, entity._unindexed, entity))

    keys = adapter.put_multi(requests)
    for key, entity in zip(keys, entities):
        entity.key = key
        entity.post_put_hook()

    return entities


def _collect_models_and_adapter(keys):
    adapter, models_by_kind = None, {}
    for key in keys:
        if not key.is_complete:
            raise RuntimeError(f"Key {key!r} is incomplete.")

        if key not in models_by_kind:
            model = key.get_model()
            if adapter is not None and adapter != model._adapter:
                raise RuntimeError("Cannot run {delete,get}_multi across multiple Adapters.")

            adapter = model._adapter
            models_by_kind[key.kind] = model

    return adapter, models_by_kind
