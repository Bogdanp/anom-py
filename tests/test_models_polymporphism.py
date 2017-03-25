import pytest

from anom import Model, props


class Animal(Model, poly=True):
    endangered = props.Bool(default=False)
    birthday = props.DateTime(indexed=True, auto_now_add=True)


class Bird(Animal):
    flightless = props.Bool(default=False)


class Eagle(Bird):
    pass


class Mammal(Animal):
    hair_color = props.String(default="black")
    name = props.String()


class Human(Mammal):
    pass


class Cat(Mammal):
    pass


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


def test_models_can_be_polymorphic(cat, human, eagle):
    assert [e.key.kind for e in (cat, human, eagle)] == ["Animal"] * 3


def test_polymorphic_models_can_be_queried_via_their_root_model(cat, human, eagle):
    animals = Animal.query().order_by(+Animal.birthday).run()
    assert list(animals) == [cat, human, eagle]


def test_polymorphic_models_can_be_queried_via_intermediate_models(cat, human, eagle):
    mammals = Mammal.query().order_by(+Mammal.birthday).run()
    assert list(mammals) == [cat, human]

    bird = Bird.query().get()
    assert bird == eagle


def test_polymorphic_models_can_be_queried_via_leaf_models(cat, human, eagle):
    for entity in (cat, human, eagle):
        entities = type(entity).query().run()
        assert list(entities) == [entity]
