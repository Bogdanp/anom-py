import inspect
import json
import pytest

from anom import Key, Property, props
from datetime import datetime
from dateutil.tz import tzlocal, tzutc

from . import models

all_properties = inspect.getmembers(props, lambda x: inspect.isclass(x) and issubclass(x, Property))
blob_properties = (props.Bytes, props.Json, props.Text)
encodable_properties = (props.String, props.Text)


def test_blobs_cannot_be_indexed():
    for property_class in blob_properties:
        with pytest.raises(TypeError):
            property_class(indexed=True)


def test_compressables_can_be_compressed():
    string = "a" * 1000
    text = props.Text(compressed=True, compression_level=9)
    compressed_bytes = text.prepare_to_store(None, string)
    assert len(compressed_bytes) == 17

    uncompressed_string = text.prepare_to_load(None, compressed_bytes)
    assert uncompressed_string == string


def test_compressables_compression_level_needs_to_be_in_a_specific_range():
    with pytest.raises(ValueError):
        props.Text(compressed=True, compression_level=20)


def test_encodables_respect_their_encodings():
    string = "こんにちは"
    encoded_string = string.encode("utf-8")
    for property_class in encodable_properties:
        prop = property_class()
        assert prop.prepare_to_store(None, string) == encoded_string
        assert prop.prepare_to_load(None, encoded_string) == string


def test_encodables_avoid_loading_nones():
    for property_class in encodable_properties:
        prop = property_class()
        assert prop.prepare_to_load(None, None) is None


def test_keys_can_be_assigned_complete_keys():
    assert props.Key().validate(Key("Person", 12))


def test_keys_cannot_be_assigned_incomplete_keys():
    with pytest.raises(ValueError):
        key = props.Key()
        key.validate(Key("Person"))


def test_jsons_dump_data_to_json_on_store():
    data = {"foo": {"bar": 42}}
    assert props.Json().prepare_to_store(None, data) == json.dumps(data, separators=(",", ":"))


def test_jsons_load_data_from_json_on_load():
    data = {"foo": {"bar": 42}}
    assert props.Json().prepare_to_load(None, json.dumps(data)) == data


def test_strings_that_are_not_indexed_can_be_assigned_arbitrarily_long_values():
    string = props.String()
    assert string.validate(" " * 1501)


def test_strings_that_are_indexed_cannot_be_assigned_values_longer_than_the_max():
    with pytest.raises(ValueError):
        string = props.String(indexed=True)
        string.validate(" " * 1501)


def test_repeated_properties_validate_their_data_types():
    string = props.String(repeated=True)
    assert string.validate([]) == []
    assert string.validate(["a", "b", "c"])

    with pytest.raises(TypeError):
        string.validate([1])


def test_required_properties_cannot_be_assigned_none():
    for _, property_class in all_properties:
        prop = property_class()
        with pytest.raises(TypeError):
            prop.validate(None)


def test_optional_properties_can_be_assigned_none():
    for _, property_class in all_properties:
        prop = property_class(optional=True)
        assert prop.validate(None) is None


def test_uninitialized_properties_return_none_on_get():
    entity = models.ModelWithInteger()
    assert entity.x is None


def test_uninitialized_repeated_properties_return_lists_on_get():
    entity = models.ModelWithRepeatedInteger()
    assert entity.xs == []


def test_uninitialized_repeated_properties_can_be_appended_to():
    entity = models.ModelWithRepeatedInteger()
    entity.xs.append(1)
    assert entity.xs == [1]


def test_uninitialized_properties_return_their_default_value():
    entity = models.ModelWithDefaulInteger()
    assert entity.x == 42


def test_named_properties_assign_values_to_the_appropriate_slots():
    entity = models.ModelWithCustomPropertyName(x=42)
    assert dict(entity) == {models.ModelWithCustomPropertyName.x.name_on_entity: 42}


def test_deleting_properties_unsets_them_on_their_models():
    entity = models.ModelWithInteger(x=42)

    del entity.x
    assert entity.x is None


def test_naive_datetimes_are_converted_to_local_time():
    now = datetime.now()
    prop = props.DateTime()
    assert prop.validate(now) == now.replace(tzinfo=tzlocal())


def test_tz_aware_datetimes_are_not_converted():
    now = datetime.now(tzutc())
    prop = props.DateTime()
    assert prop.validate(now) == now


def test_datetimes_can_be_set_on_create():
    user = models.User(email="user@example.com", password="password")
    assert not user.created_at
    assert not user.updated_at
    user.put()

    assert user.created_at
    assert user.updated_at


def test_datetimes_can_update_on_every_put():
    user = models.User(email="user@example.com", password="password")
    assert not user.created_at
    assert not user.updated_at
    user.put()

    assert user.created_at
    assert user.created_at

    previous_created_at = user.created_at
    previous_updated_at = user.updated_at
    user.put()

    assert user.created_at == previous_created_at
    assert user.updated_at != previous_updated_at


def test_datetimes_cannot_be_both_auto_and_repeated():
    with pytest.raises(TypeError):
        props.DateTime(auto_now_add=True, repeated=True)


def test_unindexed_properties_cant_be_filtered():
    with pytest.raises(TypeError):
        models.ModelWithInteger.x == "abc"


def test_properties_cant_be_filtered_against_values_of_invalid_types():
    with pytest.raises(TypeError):
        models.ModelWithIndexedInteger.x == "abc"


def test_properties_can_be_filtered():
    assert (models.ModelWithIndexedInteger.x == 1) == ("x", "=", 1)
    assert (models.ModelWithIndexedInteger.x != 1) == ("x", "!=", 1)
    assert (models.ModelWithIndexedInteger.x >= 1) == ("x", ">=", 1)
    assert (models.ModelWithIndexedInteger.x <= 1) == ("x", "<=", 1)
    assert (models.ModelWithIndexedInteger.x > 1) == ("x", ">", 1)
    assert (models.ModelWithIndexedInteger.x < 1) == ("x", "<", 1)


def test_bools_can_be_filtered_against_true_and_false():
    assert models.ModelWithIndexedBool.active.is_true == ("active", "=", True)
    assert models.ModelWithIndexedBool.active.is_false == ("active", "=", False)


def test_properties_can_be_filtered_against_none():
    assert models.ModelWithOptionalIndexedInteger.x.is_null == ("x", "=", None)


def test_required_properties_cant_be_filtered_against_none():
    with pytest.raises(TypeError):
        models.ModelWithIndexedInteger.x.is_null


def test_key_properties_can_be_assigned_entities(person):
    entity = models.ModelWithKeyProperty()
    entity.k = person
    assert entity.k == person.key
