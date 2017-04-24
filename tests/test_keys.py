import pytest

from anom import Key, get_multi

from . import models  # noqa


def test_keys_can_be_partial():
    assert Key("Person").is_partial


def test_keys_can_be_full():
    assert not Key("Person", 123).is_partial


def test_partial_keys_dont_have_an_id():
    assert Key("Person").id_or_name is None
    assert Key("Person").int_id is None
    assert Key("Person").str_id is None


def test_keys_are_hierarchical():
    assert Key("Person", 123, parent=Key("Organization", 1)).path == (
        "Organization", 1, "Person", 123
    )


def test_keys_parents_must_not_be_partial():
    with pytest.raises(ValueError):
        Key("Person", 123, parent=Key("Organization"))


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


def test_key_delete_deletes_nonexistent_entities(adapter):
    assert Key("Person", 123).delete() is None


def test_key_delete_deletes_entities(person):
    person.key.delete()
    assert person.key.get() is None


def test_keys_can_get_single_entities(person):
    assert person.key.get() == person


def test_keys_can_fail_to_get_single_entities(adapter):
    assert Key(models.Person, "nonexistent").get() is None


def test_keys_can_get_multiple_entities_at_once(person):
    entities = get_multi([person.key, Key("Person", "nonexistent")])
    assert entities == [person, None]


def test_keys_get_multi_fails_given_partial_keys():
    with pytest.raises(RuntimeError):
        get_multi([Key("Person")])


def test_keys_get_multi_fails_unknown_kind():
    with pytest.raises(RuntimeError):
        get_multi([Key("UnknownKind")])


def test_keys_can_be_constructed_from_models():
    assert Key(models.Person) == Key("Person")


def test_keys_are_hashable():
    entities = {}
    for i in range(10):
        entities[Key("Person", i)] = i

    for i in range(10):
        assert entities[Key("Person", i)] == i


@pytest.mark.parametrize("case,expected", [
    (Key.from_path("Person", 1, "Person"),
     Key("Person", parent=Key("Person", 1))),

    (Key.from_path("Person", 1, "Person", 2),
     Key("Person", 2, parent=Key("Person", 1))),

    (Key.from_path("Person", 1, "Person", 2, "Person", 3),
     Key("Person", 3, parent=Key("Person", 2, parent=Key("Person", 1))))
])
def test_keys_build_up_parents_from_path(case, expected):
    assert case == expected
