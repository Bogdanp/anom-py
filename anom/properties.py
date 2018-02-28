import base64
import json
import msgpack
import operator
import zlib

from collections import defaultdict
from copy import copy
from datetime import datetime
from dateutil import tz
from enum import IntEnum
from functools import reduce
from itertools import chain

from . import model
from .model import EmbedLike, Property, NotFound, Skip, classname


#: The UNIX epoch.
_epoch = datetime(1970, 1, 1, tzinfo=tz.tzutc())


def _seconds_since_epoch(dt):
    return (dt - _epoch).total_seconds()


#: The maximum length of indexed properties.
_max_indexed_length = 1500


class Blob:
    """Mixin for Properties whose values cannot be indexed.
    """

    def __init__(self, **options):
        if options.get("indexed") or options.get("indexed_if"):
            raise TypeError(f"{classname(self)} properties cannot be indexed.")

        super().__init__(**options)


class Compressable(Blob):
    """Mixin for Properties whose values can be gzipped before being
    persisted.

    Parameters:
      compressed(bool): Whether or not values belonging to this
        Property should be stored gzipped in Datastore.
      compression_level(int): The amount of compression to apply.
        See :func:`zlib.compress` for details.
    """

    def __init__(self, *, compressed=False, compression_level=-1, **options):
        if not (-1 <= compression_level <= 9):
            raise ValueError("compression_level must be an integer between -1 and 9.")

        super().__init__(**options)

        self.compressed = compressed
        self.compression_level = compression_level

    def prepare_to_load(self, entity, value):
        if value is not None and self.compressed:
            value = zlib.decompress(value)

        return super().prepare_to_load(entity, value)

    def prepare_to_store(self, entity, value):
        if value is not None and self.compressed:
            value = zlib.compress(value, level=self.compression_level)

        return super().prepare_to_store(entity, value)


class Encodable:
    """Mixin for string properties that have an encoding.

    Parameters:
      encoding(str): The encoding to use when persisting this Property
        to Datastore.  Defaults to ``utf-8``.
    """

    def __init__(self, *, encoding="utf-8", **options):
        super().__init__(**options)

        self.encoding = encoding

    def prepare_to_load(self, entity, value):
        value = super().prepare_to_load(entity, value)

        # BUG(gcloud): Projections seem to cause bytes to be
        # loaded as strings so this instance check is required.
        if value is not None and isinstance(value, (list, bytes)):
            if self.repeated:
                value = [v.decode(self.encoding) for v in value]
            else:
                value = value.decode(self.encoding)

        return value

    def prepare_to_store(self, entity, value):
        if value is not None:
            if self.repeated:
                value = [v.encode(self.encoding) for v in value]
            else:
                value = value.encode(self.encoding)

        return super().prepare_to_store(entity, value)


class Serializer(Compressable, Property):
    """Base class for properties that serialize data.
    """

    _types = (bool, bytes, dict, float, int, str, datetime, model.Key, model.Model)

    @classmethod
    def _serialize(cls, value):  # pragma: no cover
        raise NotImplementedError

    @classmethod
    def _deserialize(cls, data):  # pragma: no cover
        raise NotImplementedError

    @classmethod
    def _dumps(cls, value):  # pragma: no cover
        raise NotImplementedError

    @classmethod
    def _loads(cls, data):  # pragma: no cover
        raise NotImplementedError

    @staticmethod
    def _entity_to_dict(entity):
        return {
            "key": entity.key,
            "kind": entity._kind,
            "data": dict(entity),
        }

    @staticmethod
    def _entity_from_dict(data):
        key = model.Key(*data["key"])
        clazz = model.lookup_model_by_kind(data["kind"])
        instance = clazz._load(key, data["data"])
        return instance

    def prepare_to_load(self, entity, value):
        if value is not None:
            value = self._loads(value)

        return super().prepare_to_load(entity, value)

    def prepare_to_store(self, entity, value):
        if value is not None:
            value = self._dumps(value)

        return super().prepare_to_store(entity, value)


class Bool(Property):
    """A Property for boolean values.

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
        optional.  Defaults to ``False``.  Required but empty values
        cause models to raise an exception before data is persisted.
      repeated(bool, optional): Whether or not this property is
        repeated.  Defaults to ``False``.  Optional repeated
        properties default to an empty list.
    """

    _types = (bool,)

    @property
    def is_true(self):
        "PropertyFilter: A filter that checks if this value is True."
        return self == True  # noqa

    @property
    def is_false(self):
        "PropertyFilter: A filter that checks if this value is False."
        return self == False  # noqa


class Bytes(Compressable, Property):
    """A Property for bytestring values.

    Parameters:
      name(str, optional): The name of this property on the Datastore
        entity.  Defaults to the name of this property on the model.
      default(object, optional): The property's default value.
      optional(bool, optional): Whether or not this property is
        optional.  Defaults to ``False``.  Required but empty values
        cause models to raise an exception before data is persisted.
      repeated(bool, optional): Whether or not this property is
        repeated.  Defaults to ``False``.  Optional repeated
        properties default to an empty list.
      compressed(bool, optional): Whether or not this property should
        be compressed before being persisted.
      compression_level(int, optional): The amount of compression to
        apply when compressing values.
    """

    _types = (bytes,)


class Computed(Property):
    """A Property for values that should be computed dinamically based
    on the state of the entity.  Values on an entity are only computed
    the first time computed properties are accessed on that entity and
    they are re-computed every time the entity is loaded from
    Datastore.

    Computed properties cannot be assigned to and their "cache" can be
    busted by deleting them::

      del an_entity.a_property

    Note:

      Computed properties are **indexed** and **optional** by default
      for convenience.  This is different from all other built-in
      properties.

    Parameters:
      fn(callable): The function to use when computing the data.
      name(str, optional): The name of this property on the Datastore
        entity.  Defaults to the name of this property on the model.
      default(object, optional): The property's default value.
      indexed(bool, optional): Whether or not this property should be
        indexed.  Defaults to ``True``.
      indexed_if(callable, optional): Whether or not this property
        should be indexed when the callable returns ``True``.
        Defaults to ``None``.
      optional(bool, optional): Whether or not this property is
        optional.  Defaults to ``True``.
      repeated(bool, optional): Whether or not this property is
        repeated.  Defaults to ``False``.
    """

    _types = (object,)

    def __init__(self, fn, **options):
        # Computed properties are/should mainly be used for filtering
        # purposes, so it makes sense for them to default to being
        # both optional and indexed for convenience.
        options.setdefault("indexed", True)
        options.setdefault("optional", True)

        super().__init__(**options)

        self.fn = fn

    def __get__(self, ob, obtype):
        if ob is None:
            return self

        value = ob._data.get(self.name_on_entity, NotFound)
        if value is NotFound:
            value = ob._data[self.name_on_entity] = self.fn(ob)

        return value

    def __set__(self, ob, value):
        raise AttributeError("Can't set attribute.")

    def prepare_to_load(self, entity, value):
        return Skip


class DateTime(Property):
    """A Property for :class:`datetime.datetime` values.

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
        optional.  Defaults to ``False``.  Required but empty values
        cause models to raise an exception before data is persisted.
      repeated(bool, optional): Whether or not this property is
        repeated.  Defaults to ``False``.  Optional repeated
        properties default to an empty list.
      auto_now_add(bool, optional): Whether or not to set this
        property's value to the current time the first time it's
        stored.
      auto_now(bool, optional): Whether or not this property's value
        should be set to the current time every time it is stored.
    """

    _types = (datetime,)

    def __init__(self, *, auto_now_add=False, auto_now=False, **options):
        super().__init__(**options)

        self.auto_now_add = auto_now_add
        self.auto_now = auto_now

        if self.repeated and (auto_now_add or auto_now):
            raise TypeError("Cannot use auto_now{,_add} with repeated properties.")

    def _current_value(self):
        return datetime.now(tz.tzlocal())

    def prepare_to_load(self, entity, value):
        # BUG(gcloud): Projections seem to cause datetimes to be
        # loaded as ints in microseconds.
        if value is not None and isinstance(value, int):
            value = datetime.fromtimestamp(value / 1000000, tz.tzutc())

        return super().prepare_to_load(entity, value)

    def prepare_to_store(self, entity, value):
        if value is None and self.auto_now_add:
            value = entity._data[self.name_on_entity] = self._current_value()
        elif self.auto_now:
            value = entity._data[self.name_on_entity] = self._current_value()

        if value is not None:
            value = entity._data[self.name_on_entity] = value.astimezone(tz.tzutc())

        return super().prepare_to_store(entity, value)

    def validate(self, value):
        value = super().validate(value)
        if value is not None and not value.tzinfo:
            return value.replace(tzinfo=tz.tzlocal())
        return value


class Float(Property):
    """A Property for floating point values.

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
        optional.  Defaults to ``False``.  Required but empty values
        cause models to raise an exception before data is persisted.
      repeated(bool, optional): Whether or not this property is
        repeated.  Defaults to ``False``.  Optional repeated
        properties default to an empty list.
    """

    _types = (float,)


class Integer(Property):
    """A Property for integer values.

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
        optional.  Defaults to ``False``.  Required but empty values
        cause models to raise an exception before data is persisted.
      repeated(bool, optional): Whether or not this property is
        repeated.  Defaults to ``False``.  Optional repeated
        properties default to an empty list.
    """

    _types = (int,)


class Json(Serializer):
    """A Property for values that should be stored as JSON.

    Parameters:
      name(str, optional): The name of this property on the Datastore
        entity.  Defaults to the name of this property on the model.
      default(object, optional): The property's default value.
      optional(bool, optional): Whether or not this property is
        optional.  Defaults to ``False``.  Required but empty values
        cause models to raise an exception before data is persisted.
      compressed(bool, optional): Whether or not this property should
        be compressed before being persisted.
      compression_level(int, optional): The amount of compression to
        apply when compressing values.
    """

    #: The name of the field that is used to store type information
    #: about non-standard JSON values.
    _type_field = "__anom_type"

    @classmethod
    def _serialize(cls, value):
        if isinstance(value, bytes):
            kind, value = "blob", base64.b64encode(value).decode("utf-8")

        elif isinstance(value, datetime):
            kind, value = "datetime", _seconds_since_epoch(value)

        elif isinstance(value, model.Model):
            kind, value = "model", cls._entity_to_dict(value)

        else:
            raise TypeError(f"Value of type {type(value)} cannot be serialized.")

        return {cls._type_field: kind, "value": value}

    @classmethod
    def _deserialize(cls, data):
        kind = data.get(cls._type_field, None)
        if kind is None:
            return data

        value = data.get("value")
        if kind == "blob":
            return base64.b64decode(value.encode("utf-8"))

        elif kind == "datetime":
            return datetime.fromtimestamp(value, tz.tzutc())

        elif kind == "model":
            return cls._entity_from_dict(value)

        else:
            raise ValueError(f"Invalid kind {kind!r}.")

    @classmethod
    def _dumps(cls, value):
        return json.dumps(value, separators=(",", ":"), default=Json._serialize)

    @classmethod
    def _loads(cls, data):
        return json.loads(data, object_hook=Json._deserialize)


class Key(Property):
    """A Property for :class:`anom.Key` values.

    Parameters:
      name(str, optional): The name of this property on the Datastore
        entity.  Defaults to the name of this property on the model.
      default(object, optional): The property's default value.
      kind(str or model, optional): The kinds of keys that may be
        assigned to this property.
      indexed(bool, optional): Whether or not this property should be
        indexed.  Defaults to ``False``.
      indexed_if(callable, optional): Whether or not this property
        should be indexed when the callable returns ``True``.
        Defaults to ``None``.
      optional(bool, optional): Whether or not this property is
        optional.  Defaults to ``False``.  Required but empty values
        cause models to raise an exception before data is persisted.
      repeated(bool, optional): Whether or not this property is
        repeated.  Defaults to ``False``.  Optional repeated
        properties default to an empty list.
    """

    _types = (model.Model, model.Key, tuple)

    def __init__(self, *, kind=None, **options):
        super().__init__(**options)

        if isinstance(kind, model.model):
            self.kind = kind._kind
        else:
            self.kind = kind

    def validate(self, value):
        value = super().validate(value)

        if value is not None:
            if self.repeated and isinstance(value, list):
                return [self.validate(v) for v in value]

            if isinstance(value, model.Model):
                value = value.key

            # Serialized keys may end up being turned into tuples
            # (JSON, msgpack) so we attempt to coerce them here.
            if isinstance(value, tuple):
                value = model.Key(*value)

            if value.is_partial:
                raise ValueError("Cannot assign partial Keys to Key properties.")

            elif self.kind and self.kind != value.kind:
                raise ValueError(f"Property {self.name_on_model} cannot be assigned keys of kind {value.kind}.")

        return value


class Msgpack(Serializer):
    """A Property for values that should be stored as msgpack data.

    Parameters:
      name(str, optional): The name of this property on the Datastore
        entity.  Defaults to the name of this property on the model.
      default(object, optional): The property's default value.
      optional(bool, optional): Whether or not this property is
        optional.  Defaults to ``False``.  Required but empty values
        cause models to raise an exception before data is persisted.
      compressed(bool, optional): Whether or not this property should
        be compressed before being persisted.
      compression_level(int, optional): The amount of compression to
        apply when compressing values.
    """

    class Extensions(IntEnum):
        Model = 0
        DateTime = 1

    @classmethod
    def _serialize(cls, value):
        if isinstance(value, model.Model):
            kind, value = cls.Extensions.Model, cls._entity_to_dict(value)

        elif isinstance(value, datetime):
            kind, value = cls.Extensions.DateTime, _seconds_since_epoch(value)

        else:
            raise TypeError(f"Value of type {type(value)} cannot be serialized.")

        return msgpack.ExtType(kind, cls._dumps(value))

    @classmethod
    def _deserialize(cls, code, data):
        try:
            kind = cls.Extensions(code)
        except ValueError:
            raise ValueError(f"Invalid extension code {code}.")

        value = cls._loads(data)
        if kind is cls.Extensions.Model:
            return cls._entity_from_dict(value)

        elif kind is cls.Extensions.DateTime:
            return datetime.fromtimestamp(value, tz.tzutc())

    @classmethod
    def _dumps(cls, value):
        return msgpack.packb(value, default=cls._serialize, use_bin_type=True)

    @classmethod
    def _loads(cls, data):
        return msgpack.unpackb(data, ext_hook=cls._deserialize, encoding="utf-8")


class String(Encodable, Property):
    """A Property for indexable string values.

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
        optional.  Defaults to ``False``.  Required but empty values
        cause models to raise an exception before data is persisted.
      repeated(bool, optional): Whether or not this property is
        repeated.  Defaults to ``False``.  Optional repeated
        properties default to an empty list.
      encoding(str): The encoding to use when persisting this Property
        to Datastore.  Defaults to ``utf-8``.
    """

    _types = (str,)

    def _validate_length(self, value):
        if len(value) > _max_indexed_length and \
           len(value.encode(self.encoding)) > _max_indexed_length:
            raise ValueError(
                f"String value is longer than the maximum allowed length "
                f"({_max_indexed_length}) for indexed properties. Set "
                f"indexed to False if the value should not be indexed."
            )

    def validate(self, value):
        value = super().validate(value)
        if not self.indexed:
            return value

        if not self.repeated:
            self._validate_length(value)

        return value


class Text(Encodable, Compressable, Property):
    """A Property for long string values that are never indexed.

    Parameters:
      name(str, optional): The name of this property on the Datastore
        entity.  Defaults to the name of this property on the model.
      default(object, optional): The property's default value.
      optional(bool, optional): Whether or not this property is
        optional.  Defaults to ``False``.  Required but empty values
        cause models to raise an exception before data is persisted.
      repeated(bool, optional): Whether or not this property is
        repeated.  Defaults to ``False``.  Optional repeated
        properties default to an empty list.
      compressed(bool, optional): Whether or not this property should
        be compressed before being persisted.
      compression_level(int, optional): The amount of compression to
        apply when compressing values.
      encoding(str): The encoding to use when persisting this Property
        to Datastore.  Defaults to ``utf-8``.
    """

    _types = (str,)


class Embed(EmbedLike):
    """A property for embedding entities inside other entities.

    Parameters:
      kind(str or model): The kinds of keys that may be assigned to
        this property.
      optional(bool, optional): Whether or not this property is
        optional.  Defaults to ``False``.  Required but empty values
        cause models to raise an exception before data is persisted.
      repeated(bool, optional): Whether or not this property is
        repeated.  Defaults to ``False``.  Optional repeated
        properties default to an empty list.
    """

    def __init__(self, *, kind, **options):
        if "name" in options or "default" in options or "indexed" in options or "indexed_if" in options:
            raise TypeError(f"{classname(self)} does not support name, default, indexed or indexed_if.")

        super().__init__(**options)

        if isinstance(kind, model.model):
            self.kind = kind._kind
        else:
            self.kind = kind

    def __copy__(self):
        prop = type(self)(kind=self.kind)
        for name in vars(self):
            setattr(prop, name, getattr(self, name))

        return prop

    def get_unindexed_properties(self, entity):
        if isinstance(entity, list):
            return tuple(set(chain.from_iterable(self.get_unindexed_properties(e) for e in entity)))
        return tuple(f"{self.name_on_entity}.{name}" for name in entity.unindexed_properties)

    def validate(self, value):
        if self.optional and value is None:
            return value

        model_class = model.lookup_model_by_kind(self.kind)
        if self.repeated and not all(isinstance(v, model_class) for v in value):
            raise TypeError(f"{self.name_on_model} properties must be instances of {self.kind}.")

        elif not self.repeated and not isinstance(value, model_class):
            raise TypeError(f"{self.name_on_model} properties must be instances of {self.kind}.")

        return value

    def prepare_to_load(self, entity, data):
        embed_prefix = f"{self.name_on_entity}."
        embed_prefix_len = len(embed_prefix)
        data = {k[embed_prefix_len:]: v for k, v in data.items() if k.startswith(embed_prefix)}
        if self.repeated:
            return self._prepare_to_load_repeated_properties(data)
        return self._prepare_to_load_properties(data)

    def _prepare_to_load_repeated_properties(self, data):
        datas = [{} for _ in range(len(next(iter(data.values()))))]
        for key, values in data.items():
            for i, value in enumerate(values):
                datas[i][key] = value

        return [self._prepare_to_load_properties(data) for data in datas]

    def _prepare_to_load_properties(self, data):
        if self.optional and not data:
            return None

        model_class = model.lookup_model_by_kind(self.kind)
        model_key = model.Key(self.kind)
        return model_class._load(model_key, data)

    def prepare_to_store(self, entity, value):
        if value is not None:
            if isinstance(value, list):
                yield from self._prepare_to_store_repeated_properties(value)

            else:
                yield from self._prepare_to_store_properties(value)

        elif not self.optional:
            raise RuntimeError(f"Property {self.name_on_model} requires a value.")

    def _prepare_to_store_repeated_properties(self, entities):
        properties = defaultdict(list)
        for entity in entities:
            for name, value in self._prepare_to_store_properties(entity):
                properties[name].append(value)

        # Ensure all sublists are equal, otherwise rebuilding the
        # entity is not going to be possible.
        props_are_valid = reduce(operator.eq, (len(val) for val in properties.values()))
        if not props_are_valid:  # pragma: no cover
            raise ValueError(
                "Repeated properties for {self.name_on_model} have different lengths. "
                "You probably just found a bug in anom, please report it!"
            )

        for name, values in properties.items():
            yield name, values

    def _prepare_to_store_properties(self, entity):
        for name, prop in entity._properties.items():
            value = getattr(entity, name)
            if isinstance(prop, EmbedLike):
                for name, value in prop.prepare_to_store(entity, value):
                    yield f"{self.name_on_entity}.{name}", value
            else:
                yield f"{self.name_on_entity}.{prop.name_on_entity}", prop.prepare_to_store(entity, value)

    def __getattr__(self, name):
        model_class = model.lookup_model_by_kind(self.kind)
        value = getattr(model_class, name)
        if isinstance(value, model.Property):
            value = copy(value)
            value._name_on_entity = f"{self.name_on_entity}.{value.name_on_entity}"
            value._name_on_model = f"{self.name_on_model}.{value.name_on_model}"
            return value
        return value
