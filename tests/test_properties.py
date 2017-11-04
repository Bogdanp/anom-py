import inspect
import json
import msgpack
import pytest

from anom import Key, Model, Property, props
from datetime import datetime
from dateutil.tz import tzlocal, tzutc

from . import models

all_properties = inspect.getmembers(props, lambda x: (
    inspect.isclass(x) and issubclass(x, Property) and
    x is not props.Computed
))
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


def test_encodables_respect_repeated_option():
    string_list = ["a", "b"]
    bytes_list = [b"a", b"b"]
    for property_class in encodable_properties:
        prop = property_class(repeated=True)
        assert prop.prepare_to_store(None, string_list) == bytes_list
        assert prop.prepare_to_load(None, bytes_list) == string_list


def test_keys_can_be_assigned_full_keys():
    assert props.Key().validate(Key("Person", 12))


def test_keys_cannot_be_assigned_partial_keys():
    with pytest.raises(ValueError):
        key = props.Key()
        key.validate(Key("Person"))


def test_jsons_dump_data_to_json_on_store():
    data = {"foo": {"bar": 42}}
    assert props.Json().prepare_to_store(None, data) == json.dumps(data, separators=(",", ":"))


def test_jsons_load_data_from_json_on_load():
    data = {"foo": {"bar": 42}}
    assert props.Json().prepare_to_load(None, json.dumps(data)) == data


def test_jsons_dump_and_load_entities(person, mutant, human):
    for entity in (person, mutant, human):
        json = props.Json()
        entity_json = json.prepare_to_store(None, entity)
        loaded_entity = json.prepare_to_load(None, entity_json)
        assert loaded_entity == entity


def test_jsons_fail_to_dump_invalid_data():
    with pytest.raises(TypeError):
        props.Json().prepare_to_store(None, object())


def test_jsons_fail_to_load_invalid_data():
    with pytest.raises(ValueError):
        props.Json().prepare_to_load(None, json.dumps({"__anom_type": "unknown"}))


def test_msgpacks_dump_data_to_msgpack_on_store():
    data = {"foo": {"bar": 42}}
    assert props.Msgpack().prepare_to_store(None, data) == msgpack.packb(data)


def test_msgpacks_load_data_from_msgpack_on_load():
    data = {"foo": {"bar": 42}}
    assert props.Msgpack().prepare_to_load(None, msgpack.packb(data)) == data


def test_msgpacks_dump_and_load_entities(person, mutant, human):
    for entity in (person, mutant, human):
        msgpack = props.Msgpack()
        entity_msgpack = msgpack.prepare_to_store(None, entity)
        loaded_entity = msgpack.prepare_to_load(None, entity_msgpack)
        assert loaded_entity == entity


def test_msgpacks_fail_to_dump_invalid_data():
    with pytest.raises(TypeError):
        props.Msgpack().prepare_to_store(None, object())


def test_msgpacks_fail_to_load_invalid_data():
    def default(ob):
        return msgpack.ExtType(127, b"")

    with pytest.raises(ValueError):
        props.Msgpack().prepare_to_load(None, msgpack.packb(object(), default=default))


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


def test_datetimes_can_be_set_on_create(adapter):
    user = models.User(email="user@example.com", password="password")
    assert not user.created_at
    assert not user.updated_at
    user.put()

    assert user.created_at
    assert user.updated_at


def test_datetimes_can_update_on_every_put(adapter):
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
    assert (models.ModelWithIndexedInteger.x >= 1) == ("x", ">=", 1)
    assert (models.ModelWithIndexedInteger.x <= 1) == ("x", "<=", 1)
    assert (models.ModelWithIndexedInteger.x > 1) == ("x", ">", 1)
    assert (models.ModelWithIndexedInteger.x < 1) == ("x", "<", 1)


def test_bools_can_be_filtered_against_true_and_false():
    assert models.ModelWithIndexedBool.active.is_true == ("active", "=", True)
    assert models.ModelWithIndexedBool.active.is_false == ("active", "=", False)


def test_properties_can_be_filtered_against_none():
    assert models.ModelWithOptionalIndexedInteger.x.is_none == ("x", "=", None)


def test_required_properties_cant_be_filtered_against_none():
    with pytest.raises(TypeError):
        models.ModelWithIndexedInteger.x.is_none


def test_key_properties_can_be_assigned_entities(person):
    entity = models.ModelWithKeyProperty()
    entity.k = person
    assert entity.k == person.key


def test_key_properties_can_be_restricted_by_kind():
    assert props.Key(kind="Person").kind == "Person"
    assert props.Key(kind=models.Person).kind == "Person"


def test_restricted_key_properties_can_only_be_assigned_keys_of_that_kind(person):
    entity = models.ModelWithRestrictedKeyProperty()
    entity.k = person.key

    with pytest.raises(ValueError):
        entity.k = Key("Foo", 1)


def test_keys_are_converted_to_and_from_datastore(person):
    with models.temp_person(email="child@example.com", first_name="Child", parent=person) as child:
        assert child.parent == person.key

        child = child.key.get()
        assert child.parent == person.key


def test_computed_properties_are_computed_lazily():
    entity = models.ModelWithComputedProperty()
    entity.s = "hello"
    assert entity.c == "HELLO"


def test_computed_properties_cant_be_set():
    with pytest.raises(AttributeError):
        entity = models.ModelWithComputedProperty()
        entity.c = "HELLO"


def test_computed_properties_are_only_computed_once():
    calls = []

    def f(ob):
        calls.append(1)
        return 42

    class ModelWithComputedProperty1(Model):
        c = props.Computed(f)

    e = ModelWithComputedProperty1()
    assert e.c == 42
    assert e.c == 42
    assert sum(calls) == 1


def test_computed_properties_are_stored(adapter):
    entity = models.ModelWithComputedProperty2().put()
    queried_entity = models.ModelWithComputedProperty2.query().where(
        models.ModelWithComputedProperty2.c == 42
    ).get()
    assert entity == queried_entity


def test_computed_properties_are_always_computed(adapter):
    models.ModelWithComputedProperty3.calls = calls = []
    entity_1 = models.ModelWithComputedProperty3().put()
    entity_2 = entity_1.key.get()
    assert entity_1 == entity_2
    assert sum(calls) == 2


def test_computed_properties_cache_can_be_busted():
    models.ModelWithComputedProperty3.calls = calls = []

    entity_1 = models.ModelWithComputedProperty3()
    assert entity_1.c == 42
    assert sum(calls) == 1

    del entity_1.c
    assert entity_1.c == 42
    assert sum(calls) == 2


def test_repeated_keys_can_be_assigned_to_model(adapter):
    tag1 = models.Tag(name="funny").put()
    tag2 = models.Tag(name="insightful").put()
    subscriber = models.Subscriber(tags=[tag1.key, tag2.key]).put()
    assert subscriber
    assert subscriber.tags[0].get() == tag1
    assert subscriber.tags[1].get() == tag2
