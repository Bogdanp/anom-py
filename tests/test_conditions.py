from anom import Model, conditions, props


def test_is_empty():
    class ConditionsModelIsEmpty(Model):
        s = props.String(indexed_if=conditions.is_empty)

    e = ConditionsModelIsEmpty()
    assert "s" not in e.unindexed_properties

    e.s = "hello!"
    assert "s" in e.unindexed_properties


def test_is_not_empty():
    class ConditionsModelIsNotEmpty(Model):
        s = props.String(indexed_if=conditions.is_not_empty)

    e = ConditionsModelIsNotEmpty()
    assert "s" in e.unindexed_properties

    e.s = "hello!"
    assert "s" not in e.unindexed_properties


def test_is_default():
    class ConditionsModelIsDefault(Model):
        s = props.String(default="hello", indexed_if=conditions.is_default)

    e = ConditionsModelIsDefault()
    assert "s" not in e.unindexed_properties

    e.s = "goodbye"
    assert "s" in e.unindexed_properties


def test_is_not_default():
    class ConditionsModelIsNotDefault(Model):
        s = props.String(default="hello", indexed_if=conditions.is_not_default)

    e = ConditionsModelIsNotDefault()
    assert "s" in e.unindexed_properties

    e.s = "goodbye"
    assert "s" not in e.unindexed_properties


def test_is_true():
    class ConditionsModelIsTrue(Model):
        b = props.Bool(indexed_if=conditions.is_true)

    e = ConditionsModelIsTrue()
    assert "b" in e.unindexed_properties

    e.b = True
    assert "b" not in e.unindexed_properties


def test_is_false():
    class ConditionsModelIsFalse(Model):
        b = props.Bool(indexed_if=conditions.is_false)

    e = ConditionsModelIsFalse()
    assert "b" in e.unindexed_properties

    e.b = True
    assert "b" in e.unindexed_properties

    e.b = False
    assert "b" not in e.unindexed_properties


def test_is_none():
    class ConditionsModelIsNone(Model):
        b = props.Bool(optional=True, indexed_if=conditions.is_none)

    e = ConditionsModelIsNone()
    assert "b" in e.unindexed_properties

    e.b = False
    assert "b" in e.unindexed_properties

    e.b = None
    assert "b" not in e.unindexed_properties


def test_is_not_none():
    class ConditionsModelIsNotNone(Model):
        b = props.Bool(optional=True, indexed_if=conditions.is_not_none)

    e = ConditionsModelIsNotNone()
    assert "b" in e.unindexed_properties

    e.b = None
    assert "b" in e.unindexed_properties

    e.b = False
    assert "b" not in e.unindexed_properties
