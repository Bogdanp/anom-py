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
        See :module:`zlib` for details.
    """

    def __init__(self, *, compressed=False, compression_level=-1, **options):
        if not (-1 <= compression_level <= 9):
            raise ValueError("compression_level must be an integer between -1 and 9.")

        super().__init__(**options)

        self.compressed = compressed
        self.compression_level = compression_level

    def prepare_to_load(self, ob, value):
        if value is None:
            return value

        if self.compressed:
            value = zlib.decompress(value)

        return super().prepare_to_load(ob, value)

    def prepare_to_store(self, ob, value):
        value = super().prepare_to_store(ob, value)
        if self.compressed and value is not None:
            value = zlib.compress(value, level=self.compression_level)

        return value


class Encodable:
    """Mixins for string properties that have an encoding.

    Parameters:
      encoding(str)
    """

    def __init__(self, *, encoding="utf-8", **options):
        super().__init__(**options)

        self.encoding = encoding

    def prepare_to_load(self, ob, value):
        if value is None:
            return value

        return super().prepare_to_load(ob, value).decode(self.encoding)

    def prepare_to_store(self, ob, value):
        if value is not None:
            value = value.encode(self.encoding)

        return super().prepare_to_store(ob, value)


class Bool(Property):
    """A Property for boolean values.
    """

    _types = (bool,)


class Bytes(Compressable, Property):
    """A Property for bytestring values.
    """

    _types = (bytes,)


class DateTime(Property):
    """A Property for :class:`datetime.datetime` values.
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

    def prepare_to_store(self, ob, value):
        if value is None and self.auto_now_add:
            value = ob._data[self.name_on_entity] = self._current_value()
        elif self.auto_now:
            value = ob._data[self.name_on_entity] = self._current_value()

        if value is not None:
            value = ob._data[self.name_on_entity] = value.astimezone(tz.tzutc())

        return super().prepare_to_store(ob, value)

    def validate(self, value):
        value = super().validate(value)
        if value is not None and not value.tzinfo:
            return value.replace(tzinfo=tz.tzlocal())
        return value


class Float(Property):
    """A Property for floating point values.
    """

    _types = (float,)


class Integer(Property):
    """A Property for integer values.
    """

    _types = (int,)


class Json(Compressable, Property):
    """A Property for values that should be stored as JSON.
    """

    _types = (bool, bytes, datetime, float, int, str)

    def prepare_to_load(self, ob, value):
        if value is not None:
            value = json.loads(value)

        return super().prepare_to_load(ob, value)

    def prepare_to_store(self, ob, value):
        if value is not None:
            value = json.dumps(value, separators=(",", ":"))

        return super().prepare_to_store(ob, value)


class Key(Property):
    """A Property for :class:`.DSKey` values.
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
    """

    _types = (str,)
