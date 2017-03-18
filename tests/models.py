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


class ModelWithInteger(Model):
    x = props.Integer()


class ModelWithDefaulInteger(Model):
    x = props.Integer(default=42)


class ModelWithRepeatedInteger(Model):
    xs = props.Integer(repeated=True)


class ModelWithCustomPropertyName(Model):
    x = props.Integer(name="y")
