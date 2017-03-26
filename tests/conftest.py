import logging
import pytest

from anom import Key, adapters, get_adapter, set_adapter, delete_multi
from anom.testing import Emulator

from .models import Person, Mutant, Cat, Human, Eagle

logging.basicConfig(level=logging.DEBUG)


@pytest.fixture(scope="session")
def emulator():
    emulator = Emulator()
    emulator.start(inject=True)
    yield
    emulator.stop()


@pytest.fixture(autouse=True)
def adapter(emulator):
    old_adapter = get_adapter()
    adapter = set_adapter(adapters.DatastoreAdapter())
    yield adapter
    set_adapter(old_adapter)


@pytest.fixture()
def person():
    person = Person(
        email="john.smith@example.com",
        first_name="John",
        last_name="Smith"
    )
    person.put()
    yield person
    person.delete()


@pytest.fixture()
def person_in_ns():
    person = Person(
        email="namespaced@example.com",
        first_name="Namespaced",
        last_name="Person"
    )
    person.key = Key(Person, namespace="a-namespace")
    person.put()
    yield person
    person.delete()


@pytest.fixture()
def person_with_ancestor(person):
    child = Person(
        email="child@example.com",
        first_name="Child",
        last_name="Person",
    )
    child.key = Key(Person, parent=person.key)
    child.put()
    yield child
    child.delete()


@pytest.fixture()
def people():
    people = []
    for i in range(1, 21):
        person = Person(email=f"{i}@example.com", first_name="Person", last_name=str(i))
        person.key = Key(Person, i)
        people.append(person.put())

    yield people

    delete_multi([person.key for person in people])


@pytest.fixture()
def mutant():
    mutant = Mutant(email="charles@xavier.edu", first_name="Charles", last_name="Xavier")
    mutant.power = "telepathy"
    mutant.put()
    yield mutant
    mutant.delete()


@pytest.fixture
def cat():
    cat = Cat(name="Volgar the Destoryer").put()
    yield cat
    cat.delete()


@pytest.fixture
def human():
    human = Human(name="Steve").put()
    yield human
    human.delete()


@pytest.fixture
def eagle():
    eagle = Eagle().put()
    yield eagle
    eagle.delete()
