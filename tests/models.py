from anom import Model, props
from contextlib import contextmanager


class FullName:
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class BankAccount(Model):
    balance = props.Integer()


class User(FullName, Model):
    email = props.String(indexed=True)
    password = props.String()
    first_name = props.String(optional=True)
    last_name = props.String(optional=True)
    created_at = props.DateTime(auto_now_add=True)
    updated_at = props.DateTime(auto_now=True)


class Person(FullName, Model):
    email = props.String(indexed=True)
    first_name = props.String(indexed=True)
    last_name = props.String(optional=True)
    parent = props.Key(optional=True)
    created_at = props.DateTime(auto_now_add=True, indexed=True)


class Mutant(Person):
    power = props.String(indexed=True)


class MutantUser(User, Mutant):
    pass


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


class ModelWithComputedProperty(Model):
    s = props.String()

    def compute(self):
        return self.s.upper() if self.s else None

    c = props.Computed(compute)


class ModelWithComputedProperty2(Model):
    c = props.Computed(lambda s: 42)


class ModelWithComputedProperty3(Model):
    calls = []

    def __compute(self):
        self.calls.append(1)
        return 42

    c = props.Computed(__compute)


class ModelWithJsonProperty(Model):
    j = props.Json()


@contextmanager
def temp_person(**options):
    person = Person(**options).put()
    yield person
    person.delete()
