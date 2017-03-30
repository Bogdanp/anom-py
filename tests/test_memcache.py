from anom import delete_multi, get_multi
from concurrent.futures import ThreadPoolExecutor

from . import models


def test_get_multi_retrieves_cached_and_non_cached_entities(memcache_adapter):
    person_1 = models.Person(email="someone@example.com", first_name="Person 1").put()
    person_2 = models.Person(email="someone.else@example.com", first_name="Person 2").put()
    try:
        for _ in range(2):
            assert get_multi([person_1.key]) == [person_1]
            assert get_multi([person_1.key, person_2.key]) == [person_1, person_2]
    finally:
        delete_multi([person_1.key, person_2.key])


def test_delete_wins_under_contention(memcache_adapter):
    person = models.Person(email="someone@example.com", first_name="Person").put()

    with ThreadPoolExecutor(max_workers=32) as e:
        futures = []
        futures.append(e.submit(person.delete))
        futures.extend(e.submit(person.key.get) for _ in range(31))

    for future in futures:
        future.result()

    assert person.key.get() is None
