from anom import Model, props


class User(Model):
    email = props.String(indexed=True)
    password = props.String()
    first_name = props.String(optional=True)
    last_name = props.String(optional=True)
    created_at = props.DateTime(auto_now_add=True)
    updated_at = props.DateTime(auto_now=True)


class Person(Model):
    email = props.String(indexed=True)
    first_name = props.String()
    last_name = props.String(optional=True)
    parent = props.Key(optional=True)
    created_at = props.DateTime(auto_now_add=True, indexed=True)


class ModelWithIndexedBool(Model):
    active = props.Bool(indexed=True)


class ModelWithInteger(Model):
    x = props.Integer()


class ModelWithIndexedInteger(Model):
    x = props.Integer(indexed=True)


class ModelWithOptionalIndexedInteger(Model):
    x = props.Integer(indexed=True, optional=True)


class ModelWithDefaulInteger(Model):
    x = props.Integer(default=42)


class ModelWithRepeatedInteger(Model):
    xs = props.Integer(repeated=True)


class ModelWithRepeatedIndexedInteger(Model):
    xs = props.Integer(indexed=True, repeated=True)


class ModelWithCustomPropertyName(Model):
    x = props.Integer(name="y")


class ModelWithKeyProperty(Model):
    k = props.Key()


class ModelWithRestrictedKeyProperty(Model):
    k = props.Key(kind=Person)
