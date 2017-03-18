import pytest

from anom import Key, put_multi

from .models import Person


def test_key_delete_deletes_nonexistent_entities(adapter):
    assert Key("Person", 123).delete() is None


def test_key_delete_deletes_entities(adapter, person):
    person.key.delete()
    assert person.key.get() is None


def test_model_delete_deletes_entities(adapter, person):
    person.delete()
    assert person.key.get() is None


def test_model_delete_is_idempotent(adapter, person):
    for i in range(2):
        assert person.key.delete() is None
    assert person.key.get() is None


def test_model_put_requires_fields_that_are_not_optional_to_be_set(adapter):
    with pytest.raises(RuntimeError):
        person = Person()
        person.put()


def test_key_properties_are_converted_to_and_from_datastore_keys(adapter, person):
    child = Person(email="child@example.com", first_name="Child", parent=person)
    child.put()

    child = child.key.get()
    assert child.parent == person.key


def test_basic_crud(adapter):
    people = []
    for i in range(10):
        people.append(Person(email=f"{i}@example.com", first_name=f"Person {1}"))

    put_multi(people)

    for i, person in enumerate(people):
        person = person.key.get()
        assert person == people[i]

    for person in people:
        person.delete()
        assert person.key.get() is None
