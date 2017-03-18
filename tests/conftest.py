import logging
import pytest

from anom import adapters, get_adapter, set_adapter
from anom.testing import Emulator

from .models import Person

logging.basicConfig(level=logging.DEBUG)


@pytest.fixture(scope="session")
def emulator():
    emulator = Emulator()
    emulator.start(inject=True)
    yield
    emulator.terminate()


@pytest.fixture(autouse=True)
def adapter(emulator):
    old_adapter = get_adapter()
    adapter = set_adapter(adapters.DatastoreAdapter())
    yield adapter
    set_adapter(old_adapter)


@pytest.fixture()
def person():
    return Person(
        email="john.smith@example.com",
        first_name="John",
        last_name="Smith"
    ).put()
