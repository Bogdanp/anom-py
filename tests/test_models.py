import pytest

from anom import Key, Model

from .models import Person, Mutant, MutantUser, ModelWithCustomKind


def test_constructor_params_must_be_valid_properties():
    with pytest.raises(TypeError):
        Person(name="Jim")


def test_model_delete_deletes_entities(person):
    person.delete()
    assert person.key.get() is None


def test_model_delete_is_idempotent(person):
    for _ in range(2):
        assert person.key.delete() is None


def test_model_adapter_instantiates_a_default_adapter_if_none_was_set():
    assert Person._adapter


def test_model_delete_fails_if_the_entity_was_never_saved(adapter):
    with pytest.raises(RuntimeError):
        person = Person()
        person.delete()


def test_model_put_requires_fields_that_are_not_optional_to_be_set(adapter):
    with pytest.raises(RuntimeError):
        person = Person()
        person.put()


def test_model_instances_can_be_equal():
    person = Person()
    assert person == person
    assert Person(key=Key("Person", 1)) == Person(key=Key("Person", 1))
    assert Person(key=Key("Person", 1), first_name="John") == Person(key=Key("Person", 1), first_name="John")


def test_model_instances_can_not_be_equal():
    assert Person() != {}
    assert Person(key=Key("Person", 1)) != Person(key=Key("Person", 2))
    assert Person(key=Key("Person", 1), first_name="John") != Person(key=Key("Person", 1), first_name="Jane")


def test_models_cannot_have_overlapping_kinds():
    class Overlapping(Model):
        pass

    with pytest.raises(TypeError):
        class Overlapping(Model):  # noqa
            pass


def test_model_reprs_can_be_used_to_rebuild_them():
    assert repr(Person(email="foo@example.com")) == \
        "Person(key=Key('Person', None, parent=None, namespace=''), em" \
        "ail='foo@example.com', first_name=None, last_name=None, parent=" \
        "None, created_at=None)"


def test_models_can_get_entities_by_id(person):
    assert Person.get(person.key.int_id) == person


def test_models_can_be_inherited(mutant):
    assert mutant.key.kind == "Mutant"


def test_models_can_inherit_from_many_models(mutant):
    mutant_user_child = MutantUser(
        email="david.haller@xavier.edu",
        password="shadowking123",
        first_name="David",
        last_name="Haller",
        parent=mutant,
        power="literally everything",
    ).put()

    assert mutant_user_child
    assert mutant_user_child.full_name == "David Haller"
    assert mutant_user_child.parent == mutant.key


def test_inherited_models_can_be_queried(mutant):
    mutant = Mutant.query().where(Mutant.power == "telepathy").get()
    assert mutant
    assert mutant.full_name == "Charles Xavier"


def test_models_can_have_custom_kinds(adapter):
    e = ModelWithCustomKind(x=42).put()
    assert e.key.kind == "CustomKind"
    assert e.key.get() == e
    assert e.delete() is None


def test_default_model_key_uses_default_namespace(adapter, default_namespace):
    assert Person().key.namespace == default_namespace
