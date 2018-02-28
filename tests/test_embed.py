import pytest

from anom import Model, props
from anom.model import PropertyFilter


class Nested(Model):
    y = props.Integer()
    z = props.Integer(indexed=True)


class Outer(Model):
    x = props.Float(indexed=True)
    nested = props.Embed(name="child", kind=Nested)


def test_embed_properties_cannot_have_defaults():
    # When I try to make an Embed property with a default
    # Then I should get back a type error
    with pytest.raises(TypeError):
        props.Embed(kind=Nested, default=42)


def test_embed_properties_proxy_their_models(adapter):
    # When I access an embedded model's property via an Embed
    # Then I should get back that model's property
    assert Outer.nested._kind == "Nested"


def test_can_embed_entities_inside_other_entities(adapter):
    # Given that I have an entity w/ another entity inside it
    outer = Outer(x=1.0, nested=Nested(y=42, z=43))
    # When I save that entity
    outer.put()

    # Then I should be able to retrieve the same data from datastore
    assert outer == outer.key.get()

    # And only the x and nested.z properties should be indexed
    assert outer.unindexed_properties == ("child.y",)


def test_embedded_entities_are_required_by_default(adapter):
    # Given that I have an entity w/ an empty embedded value
    outer = Outer(x=1.0)
    # When I try to save that enttiy
    # Then I should get back a runtime error
    with pytest.raises(RuntimeError):
        outer.put()


def test_embedded_entities_validate_the_data_they_are_given(adapter):
    # Given that I have an entity w/ an empty embedded value
    outer = Outer(x=1.0)
    # When I try to assign an int to the nested property
    # Then I should get back a type error
    with pytest.raises(TypeError):
        outer.nested = 24


class OptionalNested(Model):
    x = props.Integer()


class OptionalOuter(Model):
    nested = props.Embed(kind=OptionalNested, optional=True)


def test_embedded_properties_can_be_optional(adapter):
    # Given that I have an outer entity w/o its nested property
    outer = OptionalOuter()

    # When I save that entity
    outer.put()

    # Then I should be able to get back the same entity from datastore
    assert outer == outer.key.get()


def test_optional_embedded_properties_can_be_assigned_None(adapter):
    # Given that I have an outer entity w/ a nested property
    outer = OptionalOuter(nested=OptionalNested(x=42))

    # When I assign none to that nested property
    outer.nested = None

    # And save that entity
    outer.put()

    # Then I should be able to get back the same entity from datastore
    assert outer == outer.key.get()


class Variation(Model):
    weight = props.Integer(indexed=True)


class SplitTest(Model):
    name = props.String(indexed=True)
    slug = props.String(indexed=True)
    variations = props.Embed(kind=Variation, repeated=True)


def test_can_embed_lists_of_entities_inside_other_entities(adapter):
    # Given that I have a split test with multiple variations
    split_test = SplitTest(name="A split test", slug="a-split-test")
    split_test.variations = [Variation(weight=20), Variation(weight=80)]

    # When I save that split test
    split_test.put()

    # Then I should be able to retrieve that same data from datastore
    assert split_test == split_test.key.get()

    # And all the properties should be indexed
    assert split_test.unindexed_properties == ()


def test_embedded_entities_validate_the_repeated_data_they_are_given(adapter):
    # Given that I have an entity w/ an empty embedded value
    split_test = SplitTest(name="A split test", slug="a-split-test")

    # When I try to assign a list of ints to the variations property
    # Then I should get back a type error
    with pytest.raises(TypeError):
        split_test.variations = [1, 2]


class DeepD(Model):
    x = props.Integer()


class DeepC(Model):
    child = props.Embed(kind=DeepD)


class DeepB(Model):
    child = props.Embed(kind=DeepC)


class DeepA(Model):
    child = props.Embed(kind=DeepB)


def test_can_deeply_embed_entitites_inside_other_entities(adapter):
    # Given that I have a deeply nested entitity
    e = DeepA(child=DeepB(child=DeepC(child=DeepD(x=42))))

    # When I save that entity
    e.put()

    # Then I should be able to retrieve that same data from datastore
    assert e == e.key.get()

    # And the deeply nested property should not be indexed
    assert e.unindexed_properties == ("child.child.child.x",)


def test_embed_properties_can_generate_filters():
    assert (Outer.nested.z == 1) == PropertyFilter("child.z", "=", 1)
    assert (SplitTest.variations.weight >= 10) == PropertyFilter("variations.weight", ">=", 10)

    with pytest.raises(TypeError):
        DeepA.child.child.child.x > 10


def test_embed_properties_can_generate_sort_orders():
    assert +Outer.nested.z == "child.z"
    assert -Outer.nested.z == "-child.z"
    assert +SplitTest.variations.weight == "variations.weight"
    assert -SplitTest.variations.weight == "-variations.weight"
    assert +DeepA.child.child.child.x == "child.child.child.x"
    assert -DeepA.child.child.child.x == "-child.child.child.x"
