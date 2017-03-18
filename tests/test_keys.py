import pytest

from anom import Key, get_multi

from . import models  # noqa


def test_keys_can_be_incomplete():
    assert not Key("Person").is_complete


def test_keys_can_be_complete():
    assert Key("Person", 123).is_complete


def test_keys_are_hierarchical():
    assert Key("Person", 123, parent=Key("Organization", 1)).path == (
        "Organization", 1, "Person", 123
    )


def test_keys_parents_must_be_complete():
    with pytest.raises(ValueError):
        assert Key("Person", 123, parent=Key("Organization"))


def test_keys_can_have_numeric_ids():
    assert Key("Person", 123).int_id == 123
    assert Key("Person", 123).str_id is None


def test_keys_can_have_string_ids():
    assert Key("Person", "Jim").str_id == "Jim"
    assert Key("Person", "Jim").int_id is None


def test_keys_can_lookup_models_by_kind():
    assert Key("Person").get_model()


def test_keys_can_fail_to_lookup_models_by_kind():
    with pytest.raises(RuntimeError):
        Key("UnknownKind").get_model()


def test_keys_reprs_can_be_used_to_rebuild_them():
    assert repr(Key("Foo", 123)) == "Key('Foo', 123, parent=None, namespace=None)"


def test_keys_can_be_equal():
    key = Key("Foo")
    assert key == key
    assert Key("Foo") == Key("Foo")
    assert Key("Foo", 123) == Key("Foo", 123)
    assert Key("Foo", 123, parent=Key("Bar", 1)) == Key("Foo", 123, parent=Key("Bar", 1))


def test_keys_can_be_not_equal():
    assert Key("Foo") != Key("Bar")
    assert Key("Foo", 123) != Key("Foo", 124)
    assert Key("Foo", 123, parent=Key("Bar", 1)) != Key("Foo", 123, parent=Key("Bar", 2))
    assert Key("Foo", 123, namespace="foos") != Key("Foo", 123, parent=Key("Bar", 1))


def test_keys_can_get_multiple_entities_at_once(person):
    entities = get_multi([person.key, Key("Person", "nonexistent")])
    assert entities == [person, None]


def test_keys_get_multi_fails_given_incomplete_keys():
    with pytest.raises(RuntimeError):
        get_multi([Key("Person")])


def test_keys_get_multi_fails_unknown_kind():
    with pytest.raises(RuntimeError):
        get_multi([Key("UnknownKind")])
