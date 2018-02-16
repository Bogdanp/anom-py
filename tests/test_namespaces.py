import anom

from . import models  # noqa


def test_can_set_default_namespace(executor):
    # Given that the current namespace is the empty/global namespace
    assert anom.get_namespace() == ""

    # When I set the global default namespace to "anomspace"
    anom.set_default_namespace("anomspace")

    # I expect get_namespace to return the new global default
    assert anom.get_namespace() == "anomspace"

    # And keys without an explicit namespace to use the global default
    assert anom.Key(models.BankAccount).namespace == "anomspace"

    # And queries without an explicit namespace to use the global default
    assert models.BankAccount().query().namespace == "anomspace"

    # And for other threads to use the global default
    assert executor.submit(anom.get_namespace).result() == "anomspace"


def test_can_set_namespace(default_namespace, executor):
    # Given that I have some global default namespace
    assert anom.get_namespace() == default_namespace

    # And that namespace is not "anomspace"
    assert default_namespace != "anomspace"

    # When I set the local default namespace to "anomspace"
    anom.set_namespace("anomspace")

    # I expect get_namespace to return the new local default namespace
    assert anom.get_namespace() == "anomspace"

    # And keys without an explicit namespace to use the local default
    assert anom.Key(models.BankAccount).namespace == "anomspace"

    # And queries without an explicit namespace to use the local default
    assert models.BankAccount().query().namespace == "anomspace"

    # And for other threads to still use the global default
    assert executor.submit(anom.get_namespace).result() == default_namespace

    # When I set the local default namespace to None
    anom.set_namespace(None)

    # I expect everything to go back to using the global default
    assert anom.get_namespace() == default_namespace
    assert anom.Key(models.BankAccount).namespace == default_namespace
    assert models.BankAccount().query().namespace == default_namespace
    assert executor.submit(anom.get_namespace).result() == default_namespace


def test_namespace_context_manager(default_namespace, executor):
    # Given that I have some global default namespace
    assert anom.get_namespace() == default_namespace

    # And that namespace is not "anomspace"
    assert default_namespace != "anomspace"

    # When I set the local default namespace with the context manager
    with anom.namespace("anomspace"):
        # I expect everything inside the context to use the new local default
        assert anom.get_namespace() == "anomspace"
        assert anom.Key(models.BankAccount).namespace == "anomspace"
        assert models.BankAccount().query().namespace == "anomspace"

        # But other threads should still use the global default
        assert executor.submit(anom.get_namespace).result() == default_namespace

    # When I exit the context, I expect everything to revert to using the global
    # default namespace again
    assert anom.get_namespace() == default_namespace
    assert anom.Key(models.BankAccount).namespace == default_namespace
    assert models.BankAccount().query().namespace == default_namespace
    assert executor.submit(anom.get_namespace).result() == default_namespace


def test_namespaces_persist_through_changes_once_set(default_namespace):
    # Given that I have some global default namespace
    assert anom.get_namespace() == default_namespace

    # And I have some things that I instantiated with that default namespace
    key = anom.Key(models.BankAccount)
    query = models.BankAccount.query()

    # When I change the local default namespace
    anom.set_namespace("anomspace")

    # I expect all of those things to still use the global default namespace
    assert key.namespace == default_namespace
    assert query.namespace == default_namespace

    # Given that I made new things with the new local default namespace
    key = anom.Key(models.BankAccount)
    query = models.BankAccount.query()

    # When I change the local default namespace again
    with anom.namespace("monaspace"):
        # I expect all of those things to still use the previous local default
        assert key.namespace == "anomspace"
        assert query.namespace == "anomspace"

        # Given that I made new things with the new local default namespace
        key = anom.Key(models.BankAccount)
        query = models.BankAccount.query()

    # When I exit the context and the local default goes back to the global
    # default, I expect everything to still use the namespace they were created
    # with
    assert key.namespace == "monaspace"
    assert query.namespace == "monaspace"


def test_datastore_client_uses_the_default_namespace():
    # Given that I've set a default namespace
    anom.set_default_namespace("anomspace")

    # And I have a DatastoreAdapter
    adapter = anom.adapters.DatastoreAdapter()

    # And the adapter hasn't instantiated a client yet
    adapter._state.client = None

    # When I get the adapter's client
    client = adapter.client

    # I expect the client's namespace to match the global default
    assert client.namespace == "anomspace"

    anom.set_default_namespace()
    adapter._state.client = None
