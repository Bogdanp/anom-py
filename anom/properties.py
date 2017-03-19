import json
import zlib

from datetime import datetime
from dateutil import tz

from .model import Key as DSKey, Model, Property


#: The maximum length of indexed properties.
_max_indexed_length = 1500


class Blob:
    """Mixin for Properties whose values cannot be indexed.
    """

    def __init__(self, **options):
        if options.get("indexed"):
            classname = type(self).__name__
            raise TypeError(f"{classname} properties cannot be indexed.")

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
        if value is None:
            return value

        if self.compressed:
            value = zlib.decompress(value)

        return super().prepare_to_load(entity, value)

    def prepare_to_store(self, entity, value):
        value = super().prepare_to_store(entity, value)
        if self.compressed and value is not None:
            value = zlib.compress(value, level=self.compression_level)

        return value


class Encodable:
    """Mixins for string properties that have an encoding.

    Parameters:
      encoding(str): The encoding to use when persisting this Property
        to Datastore.  Defaults to ``utf-8``.
    """

    def __init__(self, *, encoding="utf-8", **options):
        super().__init__(**options)

        self.encoding = encoding

    def prepare_to_load(self, entity, value):
        if value is None:
            return value

        value = super().prepare_to_load(entity, value)
        if isinstance(value, str):
            # BUG(gcloud): Projections seem to cause bytes to be loaded as strings.
            return value

        return value.decode(self.encoding)

    def prepare_to_store(self, entity, value):
        if value is not None:
            value = value.encode(self.encoding)

        return super().prepare_to_store(entity, value)


class Bool(Property):
    """A Property for boolean values.

    Parameters:
      name(str, optional): The name of this property on the Datastore
        entity.  Defaults to the name of this property on the model.
      default(object, optional): The property's default value.
      indexed(bool, optional): Whether or not this property should be
        indexed.  Defaults to ``False``.
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
      indexed(bool, optional): Whether or not this property should be
        indexed.  Defaults to ``False``.
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


class DateTime(Property):
    """A Property for :class:`datetime.datetime` values.

    Parameters:
      name(str, optional): The name of this property on the Datastore
        entity.  Defaults to the name of this property on the model.
      default(object, optional): The property's default value.
      indexed(bool, optional): Whether or not this property should be
        indexed.  Defaults to ``False``.
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
      optional(bool, optional): Whether or not this property is
        optional.  Defaults to ``False``.  Required but empty values
        cause models to raise an exception before data is persisted.
      repeated(bool, optional): Whether or not this property is
        repeated.  Defaults to ``False``.  Optional repeated
        properties default to an empty list.
    """

    _types = (int,)


class Json(Compressable, Property):
    """A Property for values that should be stored as JSON.

    Parameters:
      name(str, optional): The name of this property on the Datastore
        entity.  Defaults to the name of this property on the model.
      default(object, optional): The property's default value.
      indexed(bool, optional): Whether or not this property should be
        indexed.  Defaults to ``False``.
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

    _types = (bool, bytes, datetime, float, int, str)

    def prepare_to_load(self, entity, value):
        if value is not None:
            value = json.loads(value)

        return super().prepare_to_load(entity, value)

    def prepare_to_store(self, entity, value):
        if value is not None:
            value = json.dumps(value, separators=(",", ":"))

        return super().prepare_to_store(entity, value)


class Key(Property):
    """A Property for :class:`anom.Key` values.

    Parameters:
      name(str, optional): The name of this property on the Datastore
        entity.  Defaults to the name of this property on the model.
      default(object, optional): The property's default value.
      indexed(bool, optional): Whether or not this property should be
        indexed.  Defaults to ``False``.
      optional(bool, optional): Whether or not this property is
        optional.  Defaults to ``False``.  Required but empty values
        cause models to raise an exception before data is persisted.
      repeated(bool, optional): Whether or not this property is
        repeated.  Defaults to ``False``.  Optional repeated
        properties default to an empty list.
    """

    _types = (DSKey,)

    def validate(self, value):
        if value is not None and isinstance(value, Model):
            value = value.key

        value = super().validate(value)
        if value is not None and not value.is_complete:
            raise ValueError("Cannot assign incomplete Keys to Key properties.")
        return value


class String(Encodable, Property):
    """A Property for indexable string values.

    Parameters:
      name(str, optional): The name of this property on the Datastore
        entity.  Defaults to the name of this property on the model.
      default(object, optional): The property's default value.
      indexed(bool, optional): Whether or not this property should be
        indexed.  Defaults to ``False``.
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

    def validate(self, value):
        value = super().validate(value)
        if not self.indexed:
            return value

        if len(value) > _max_indexed_length and \
           len(value.encode(self.encoding)) > _max_indexed_length:
            raise ValueError(
                f"String value is longer than the maximum allowed length "
                f"({_max_indexed_length}) for indexed properties. Set "
                f"indexed to False if the value should not be indexed."
            )

        return value


class Text(Compressable, Encodable, Property):
    """A Property for long string values that are never indexed.

    Parameters:
      name(str, optional): The name of this property on the Datastore
        entity.  Defaults to the name of this property on the model.
      default(object, optional): The property's default value.
      indexed(bool, optional): Whether or not this property should be
        indexed.  Defaults to ``False``.
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
