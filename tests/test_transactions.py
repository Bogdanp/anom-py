import pytest

from anom import Model, Transaction, RetriesExceeded, props, get_multi, put_multi, transactional
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch


class BankAccount(Model):
    balance = props.Integer()


def test_transactions_are_serializable():
    @transactional(retries=128)
    def transfer_money(source_account_key, target_account_key, amount):
        source_account, target_account = get_multi([source_account_key, target_account_key])
        source_account.balance -= amount
        target_account.balance += amount
        put_multi([source_account, target_account])

    source = BankAccount(balance=100).put()
    target = BankAccount(balance=0).put()

    futures = []
    with ThreadPoolExecutor(max_workers=10) as e:
        for _ in range(10):
            futures.append(e.submit(transfer_money, source.key, target.key, 10))

    for future in futures:
        future.result()

    source, target = get_multi([source.key, target.key])
    assert source.balance == 0
    assert target.balance == 100


def test_transactions_can_delete_data(person):
    @transactional()
    def successful(person_key):
        person_key.delete()

    successful(person.key)
    assert person.key.get() is None


def test_transactions_can_be_rolled_back(person):
    @transactional()
    def failing(person_key):
        person = person_key.get()
        person.first_name = "Johan"
        person.put()
        raise RuntimeError("some error")

    with pytest.raises(RuntimeError):
        first_name = person.first_name
        failing(person.key)

    person = person.key.get()
    assert person.first_name == first_name


def test_transactions_can_be_nested(person):
    @transactional()
    def successful_inner(person_key):
        person = person_key.get()
        person.first_name = "Johan"
        person.put()

    @transactional()
    def successful_outer(person_key):
        person = person_key.get()
        person.first_name = "Iohan"
        person.put()
        successful_inner(person.key)

    successful_outer(person.key)
    person = person.key.get()
    assert person.first_name == "Johan"


def test_nested_transactions_roll_back_the_outer_transaction(person):
    @transactional()
    def failing_inner(person_key):
        person = person_key.get()
        person.first_name = "Johan"
        person.put()
        raise RuntimeError("some error")

    @transactional()
    def successful_outer(person_key):
        person = person_key.get()
        person.first_name = "Iohan"
        person.put()
        failing_inner(person.key)

    with pytest.raises(RuntimeError):
        first_name = person.first_name
        successful_outer(person.key)

    person = person.key.get()
    assert person.first_name == first_name


def test_transactions_can_be_independent(person):
    @transactional(propagation=Transaction.Propagation.Independent)
    def failing_inner(person_key):
        person = person_key.get()
        person.first_name = "Johan"
        person.put()
        raise RuntimeError("some error")

    @transactional()
    def successful_outer(person_key):
        person = person_key.get()
        person.first_name = "Iohan"
        person.put()

        with pytest.raises(RuntimeError):
            failing_inner(person.key)

    successful_outer(person.key)
    person = person.key.get()
    assert person.first_name == "Iohan"


def test_transactions_can_run_out_of_retries(person):
    @transactional()
    def failing(person_key):
        pass

    with patch("google.cloud.datastore.Transaction.commit") as commit_mock:
        commit_mock.side_effect = RuntimeError

        with pytest.raises(RetriesExceeded):
            failing(person.key)
