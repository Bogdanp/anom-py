import pytest

from anom import Query

from .models import Person


def test_queries_can_fail_to_get_single_items():
    assert Person.query().where(Person.email == "invalid").get() is None


def test_queries_can_fail_given_unknown_kind():
    with pytest.raises(RuntimeError):
        next(Query("UnknownKind").run())


def test_queries_can_fetch_entire_datasets(people):
    all_people = Person.query().run()
    assert list(all_people) == people


def test_keys_only_queries_can_fetch_entire_datasets(people):
    all_people = Person.query().run(keys_only=True)
    assert list(all_people) == [person.key for person in people]


def test_queries_can_project_fields(people):
    one_person = Person.query().select(Person.email, Person.first_name, Person.created_at).get()
    assert one_person.email
    assert one_person.first_name
    assert one_person.created_at
    assert one_person.last_name is None


def test_queries_can_be_filtered(people):
    all_people = Person.query().where(Person.email == "1@example.com").run()
    assert list(all_people) == people[0:1]


def test_queries_can_be_filtered_and_return_no_results(people):
    invalid_people = Person.query().where(Person.email == "invalid").run()
    assert list(invalid_people) == []


def test_queries_can_be_limited(people):
    all_people = Person.query().with_limit(1).run()
    assert list(all_people) == people[:1]


def test_queries_can_have_an_offset(people):
    all_people = Person.query().with_offset(1).run()
    assert list(all_people) == people[1:]


def test_queries_can_be_ordered(people):
    all_people = Person.query().order_by(-Person.email, +Person.created_at).run()
    assert list(all_people) == list(reversed(sorted(people, key=lambda p: p.email)))


def test_queries_can_be_namespaced(people, person_in_ns):
    all_people_in_ns = Person.query().with_namespace(person_in_ns.key.namespace).run()
    assert list(all_people_in_ns) == [person_in_ns]


def test_queries_can_have_ancestors(people, person, person_with_ancestor):
    all_people_with_ancestor = Person.query().with_ancestor(person.key).run()
    assert list(all_people_with_ancestor) == [person, person_with_ancestor]


def test_queries_be_paginated(people):
    page_size = 3
    pages = Person.query().paginate(page_size=page_size)
    for i, page in enumerate(pages):
        lo = i * page_size
        hi = (i + 1) * page_size
        assert list(page) == people[lo:hi]


def test_queries_be_paginated_with_limit(people):
    page_size, limit = 3, 5
    pages = Person.query().with_limit(limit).paginate(page_size=page_size)
    for i, page in enumerate(pages):
        lo = i * page_size
        hi = min(limit, (i + 1) * page_size)
        assert list(page) == people[lo:hi]

    assert i == limit // page_size


def test_pages_can_tell_if_there_are_more_pages(people):
    pages = Person.query().paginate(page_size=10)
    assert pages.has_more

    for _ in pages:
        assert pages.has_more
    assert not pages.has_more


def test_pages_can_be_paginated_manually(people):
    people_query = Person.query()
    page_1 = people_query.paginate(page_size=2).fetch_next_page()
    page_2 = people_query.paginate(page_size=2, cursor=page_1.cursor).fetch_next_page()
    assert list(page_1) == people[:2]
    assert list(page_2) == people[2:4]


def test_pages_fetch_next_page_returns_empty_iterator_if_there_are_no_more_pages():
    pages = Person.query().paginate(page_size=10)
    assert list(pages.fetch_next_page()) == []


def test_queries_preprocess_keys(person):
    child = Person(email="child@example.com", first_name="Child", parent=person).put()
    child = Person.query().where(Person.email == "child@example.com").get()
    assert child.parent == person.key
