import pytest

from anom import Query
from anom.query import PropertyFilter

from .models import Person, temp_person


def test_queries_can_fail_to_get_single_items(adapter):
    assert Person.query().where(Person.email == "invalid").get() is None


def test_queries_can_fail_given_unknown_kind():
    with pytest.raises(RuntimeError):
        Query("UnknownKind")


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


def test_queries_where_can_replace_filters(people):
    query = Person.query() \
                  .where(Person.email == "invalid") \
                  .where(Person.email == "valid")

    assert query.filters == (PropertyFilter("email", "=", "valid"),)


def test_queries_and_where_can_add_filters(people):
    query = Person.query() \
                  .where(Person.email == "invalid") \
                  .and_where(Person.first_name == "Jim")

    assert query.filters == (
        PropertyFilter("email", "=", "invalid"),
        PropertyFilter("first_name", "=", "Jim"),
    )


def test_queries_can_be_limited(people):
    all_people = Person.query().with_limit(1).run()
    assert list(all_people) == people[:1]


@pytest.mark.xfail(reason="broken in google-cloud-datastore")
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


def test_pages_fetch_next_page_returns_empty_iterator_if_there_are_no_more_pages(adapter):
    pages = Person.query().paginate(page_size=10)
    assert list(pages.fetch_next_page()) == []


def test_pages_cursor_points_to_the_next_page(adapter):
    pages = Person.query().paginate(page_size=10)
    page_1 = pages.fetch_next_page()
    assert pages.cursor == page_1.cursor


def test_queries_preprocess_keys(person):
    with temp_person(email="child@example.com", first_name="Child", parent=person) as child:
        child = Person.query().where(Person.email == "child@example.com").get()
        assert child.parent == person.key


def test_kindless_queries(people):
    queried_people = list(Query().run())
    assert sorted(queried_people, key=lambda e: e.key) == \
        sorted(people, key=lambda e: e.key)


def test_kindless_queries_in_ns(people, person_in_ns):
    queried_people = list(Query(namespace=person_in_ns.key.namespace).run())
    assert sorted(queried_people, key=lambda e: e.key) == \
        sorted([person_in_ns], key=lambda e: e.key)


def test_queries_can_be_filtered_by_key(people):
    # XREF: https://github.com/Bogdanp/anom-py/issues/4
    assert list(Person.query().where(Person.parent == people[0]).run()) == []


def test_can_delete_entities_by_query(people):
    # Given that I have some number of people
    # When I delete one person by query
    deleted = Person.query().where(Person.email == "1@example.com").delete()
    # Then I should get back the number of deleted people
    assert deleted == 1

    # When I try to delete the same query again
    deleted = Person.query().where(Person.email == "1@example.com").delete()
    # Then that number should be 0
    assert deleted == 0


def test_can_delete_many_pages_of_entities_by_query(people):
    # Given that I have some number of people
    # When I delete all those people in batches of one at a time
    deleted = Person.query().delete(page_size=1)
    # Then I should get back the total number of deleted people and it
    # should equal the number of people I had originally
    assert deleted == len(people)


def test_can_count_entities_by_query(people):
    # Given that I have some number of people
    # When I attempt to count all the people
    # Then I should get back that number of people
    assert len(people) == Person.query().count()

    # When I attempt to filter down the query
    # Then I should get back a smaller count
    assert 1 == Person.query().where(Person.email == "1@example.com").count()

    # When my query doesn't match any results
    # Then I should get back a count of 0
    assert 0 == Person.query().where(Person.email == "idontexist").count()
