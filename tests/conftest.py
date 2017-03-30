import logging
import pylibmc
import pytest

from anom import Adapter, Key, adapters, get_adapter, set_adapter, delete_multi
from anom.testing import Emulator

from .models import Person, Mutant, Cat, Human, Eagle

logging.basicConfig(level=logging.DEBUG)


@pytest.fixture(scope="session")
def emulator():
    emulator = Emulator()
    emulator.start(inject=True)
    yield
    emulator.stop()


@pytest.fixture(scope="session")
def memcache_client():
    client = pylibmc.Client(["127.0.0.1"], binary=True, behaviors={"cas": True})
    yield client
    client.flush_all()


@pytest.fixture(autouse=True)
def noop_adapter():
    old_adapter = get_adapter()
    adapter = set_adapter(Adapter())
    yield adapter
    set_adapter(old_adapter)


@pytest.fixture(params=["datastore", "memcache"])
def adapter(request, emulator, memcache_client):
    old_adapter = get_adapter()
    ds_adapter = adapters.DatastoreAdapter()

    if request.param == "datastore":
        adapter = ds_adapter
    elif request.param == "memcache":
        adapter = adapters.MemcacheAdapter(memcache_client, ds_adapter)

    adapter = set_adapter(adapter)
    yield adapter
    set_adapter(old_adapter)


@pytest.fixture()
def memcache_adapter(emulator, memcache_client):
    old_adapter = get_adapter()
    adapter = set_adapter(adapters.MemcacheAdapter(memcache_client, adapters.DatastoreAdapter()))
    yield adapter
    set_adapter(old_adapter)


@pytest.fixture()
def person(adapter):
    person = Person(
        email="john.smith@example.com",
        first_name="John",
        last_name="Smith"
    )
    person.put()
    yield person
    person.delete()


@pytest.fixture()
def person_in_ns(adapter):
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
def people(adapter):
    people = []
    for i in range(1, 21):
        person = Person(email=f"{i}@example.com", first_name="Person", last_name=str(i))
        person.key = Key(Person, i)
        people.append(person.put())

    yield people

    delete_multi([person.key for person in people])


@pytest.fixture()
def mutant(adapter):
    mutant = Mutant(email="charles@xavier.edu", first_name="Charles", last_name="Xavier")
    mutant.power = "telepathy"
    mutant.put()
    yield mutant
    mutant.delete()


@pytest.fixture
def cat(adapter):
    cat = Cat(name="Volgar the Destoryer").put()
    yield cat
    cat.delete()


@pytest.fixture
def human(adapter):
    human = Human(name="Steve").put()
    yield human
    human.delete()


@pytest.fixture
def eagle(adapter):
    eagle = Eagle().put()
    yield eagle
    eagle.delete()
