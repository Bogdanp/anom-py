from .models import Animal, Mammal, Bird


def test_polymorphic_entitites_share_the_same_root_kind(cat, human, eagle):
    assert [e.key.kind for e in (cat, human, eagle)] == ["Animal"] * 3


def test_polymorphic_models_can_be_queried_via_their_root_model(cat, human, eagle):
    animals = Animal.query().order_by(+Animal.birthday).run()
    assert list(animals) == [cat, human, eagle]


def test_polymorphic_models_can_be_queried_via_intermediate_models(cat, human, eagle):
    mammals = Mammal.query().order_by(+Mammal.birthday).run()
    assert list(mammals) == [cat, human]

    birds = Bird.query().run()
    assert list(birds) == [eagle]


def test_polymorphic_models_can_be_queried_via_leaf_models(cat, human, eagle):
    for entity in (cat, human, eagle):
        entities = type(entity).query().run()
        assert list(entities) == [entity]
