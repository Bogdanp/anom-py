.. include:: global.rst

Quickstart
==========

To get started, ensure you've installed `gcloud`_ then spin up a
`Datastore Emulator`_ with::

  $ gcloud beta emulators start

Ensure your environment points to that emulator before running any of
the code below by first running::

  $ $(gcloud beta emulators env-init)

For more information see the `official docs`_.

These steps are *important* since anom will connect to whatever
Datastore the current environment points to by default.


Models
------

Models define how data is shaped in Datastore and where it should be
stored.  To get started, import |Model| and |props| from the |anom|
module::

  >>> from anom import Model, props

.. note::

   ``anom.props`` is an alias of the :mod:`anom.properties` module for
   convenience.

Declaring models is very simple and should come naturally to you if
you've ever used any other Python ORM::

  >>> class Greeting(Model):
  ...   email = props.String(indexed=True, optional=True)
  ...   message = props.Text()
  ...   created_at = props.DateTime(indexed=True, auto_now_add=True)
  ...   updated_at = props.DateTime(indexed=True, auto_now=True)

This says that ``Greeting`` is a model with 4 properties:

``email``
  an indexed string that may or may not be set,

``message``
  an unindexed string that is required,

``created_at``
  a date time that defaults to whenever each entity is
  saved for the first time and

``updated_at``
  a date time that is updated every time the entity is
  saved.

.. note::

   Even though, in general, you can name properties on a model
   whatever you like, certain names are reserved.  You may not give a
   property a name that would clash with any of the attributes on the
   |Model| class.

You can instantiate models like you would normal Python classes::

  >>> greeting = Greeting()

and then access their properties as if they were normal instance
attributes (under the hood, that's more or less what they are!)::

  >>> greeting.email = "someone@example.com"
  >>> greeting.email
  "someone@example.com"
  >>> print(greeting.message)
  None

You can also specify which properties should be populated when you
construct entities::

  >>> greeting = Greeting(email="someone@example.com", message="Hi!")

Every entity\ [#]_ has a |Key| that you can access via its |Model_key|
attribute.  Entities that have not yet been saved have what are known
as partial keys, keys without an id or a name assigned to them.

You can store the greeting by calling its |Model_put| method::

  >>> greeting.put()

Doing so will serialize the entity, store it in Datastore and update
its key to point to its location in Datastore.  You can get the
greeting's automatically-assigned id by accessing |Key_int_id| on its
key::

  >>> greeting.key.int_id
  1001

You can fetch entities by id by calling |Model_get|::

  >>> same_greeting = Greeting.get(1001)  # Replace 1001 with whatever id your greeting was assigned
  >>> same_greeting
  Greeting(Key("Greeting", 1001, parent=None, namespace=None), email="someone@example.com", message="Hi!", created_at=..., updated_at=...)

And entities can be compared with each other for equality::

  >>> same_greeting == greeting
  True

Finally, you can |Model_delete| entities::

  >>> greeting.delete()

Doing so will permanently remove ``greeting`` from Datastore.


Properties
----------

anom comes with the following predefined properties:

=================================  ======================================================================
Property                           Description
=================================  ======================================================================
:class:`anom.properties.Bool`      Stores :class:`bool` values.
:class:`anom.properties.Bytes`     Stores blobs of binary data (:class:`bytes`). Never indexed.
:class:`anom.properties.Computed`  Stores values computed by arbitrary functions.
:class:`anom.properties.DateTime`  Stores :class:`datetime.datetime` values.
:class:`anom.properties.Float`     Stores :class:`float` values.
:class:`anom.properties.Integer`   Stores :class:`int` values.
:class:`anom.properties.Json`      Stores JSON values. Never indexed.
:class:`anom.properties.Key`       Stores :class:`anom.Key` values.
:class:`anom.properties.String`    Stores :class:`str` values.
:class:`anom.properties.Msgpack`   Stores msgpack values. Never indexed.
:class:`anom.properties.Text`      Stores long :class:`str` values. Never indexed.
:class:`anom.properties.Embed`     Stores embedded models.  Indexed if any nested properties are indexed.
=================================  ======================================================================

These properties all map to built-in Datastore types and they each
support the following set of options:

============  =========  ===============================================================================================================================
Option        Default    Description
============  =========  ===============================================================================================================================
``name``      ``None``   The name of the property on the stored entity in Datastore. Defaults to its name on the model.
``default``   ``None``   The default value to return when the property isn't populated with data.
``indexed``   ``False``  Whether or not the property should be indexed in Datastore. Bytes, Json, Msgpack and Text properties cannot be indexed.
``optional``  ``False``  Whether or not the property is optional. Required-but-empty values cause models to raise an exception before data is persisted.
``repeated``  ``False``  Whether or not the property is repeated.
============  =========  ===============================================================================================================================

Compressable Properties
^^^^^^^^^^^^^^^^^^^^^^^

The following properties can be g{un,}zipped before being stored to or
loaded from Datastore:

* :class:`anom.properties.Bytes`
* :class:`anom.properties.Json`
* :class:`anom.properties.Msgpack`
* :class:`anom.properties.String`
* :class:`anom.properties.Text`

Compressable properties support the following additional set of
options:

=====================  =========  ============================================================================================================================
Option                 Default    Description
=====================  =========  ============================================================================================================================
``compressed``         ``False``  Whether or not values assigned to this property should be compressed.
``compression_level``  ``-1``     The amount of compression to apply. This must be an integer between ``-1`` and ``9``. See :func:`zlib.compress` for details.
=====================  =========  ============================================================================================================================

Compression is applied as late as possible (on ``put``) to avoid
wasting CPU so assigning values to compressed properties has no
additional cost until you save the entity.

.. note::

   Currently, compression is all-or-nothing.  anom does not check if
   values are compressed before loading them unless you explicitly ask
   it to.  Likewise, if you tell it that a property's values are
   compressed it won't validate that they are compressed before trying
   to decompress them.

DateTime Properties
^^^^^^^^^^^^^^^^^^^

|prop_DateTime| properties support the following additional set of
options:

================  =========  =========================================================================================================================================
Option            Default    Description
================  =========  =========================================================================================================================================
``auto_now_add``  ``False``  Whether or not this value should default to the current time the first time it's saved.  You'd use this for `created_at` type properties.
``auto_now``      ``False``  Whether or not this value should default to the current time every time it's saved.  You'd use this for `updated_at` type properties.
================  =========  =========================================================================================================================================

Encodable Properties
^^^^^^^^^^^^^^^^^^^^

|prop_String| and |prop_Text| properties have an ``encoding`` option
which controls which codec to use when {en,de}coding values.

The default ``encoding`` is ``utf-8``.


Keys
----

|Keys| represent the locations of individual entities inside
Datastore.  They consist of a Datastore kind, an optional id, a parent
key and a namespace.

Keys are immutable and they can be stored on individual entities via
|prop_Key| properties.

You can instantiate new keys::

  >>> greeting_key = Key("Greeting", 1001)

And you can use them to get entities::

  >>> greeting = greeting_key.get()

Or to delete them::

  >>> greeting_key.delete()

Keys can have ancestors::

  >>> jim_key = Key("Person", "Jim", parent=Key("Person", "John"))

And they can be namespaced::

  >>> jim_key_in_ns = Key("Person", "Jim", namespace="people")


Indexes
-------

Writing a new single-property index requires two Datastore operations
and changing an existing single-property index requires *four*.  With
large Models this cost can add up quickly, increasing the time it takes
for data to become consistent across Datastore and increasing your
overall Datastore costs.

For this reason, all anom properties except for |prop_Computed| are
*unindexed by default*.  This means that if you want to filter on or
sort by a property you have to decide up front if it's going to be
indexed or not.

Changing a property from unindexed to indexed (or vice-versa) on your
model **will not** affect the indexing schemes of previously-saved
data.  You need to re-save individual entities in order to add or
remove indexes.

Conditional Indexes
^^^^^^^^^^^^^^^^^^^

Conditional indexes on properties let you specify whether or not
certain properties should be indexed based on their value at the time
they are stored.  This provides a convenient mechanism for indexing
subsets of your data.  For example::

  from anom import conditions

  class User(Model):
    is_admin = props.Bool(default=False, indexed_if=conditions.is_true)

  # This adds an index entry for is_admin
  admin_user = User(is_admin=True).put()

  # whereas this doesn't.
  normal_user = User().put()

  # This query would return all admin users,
  all_admins = User.query().where(User.is_admin.is_true).run()

  # whereas this wouldn't return any users at all.
  no_users = User.query().where(User.is_admin.is_false).run()

If you only ever need to query for the (presumably small) subset of
admins based on the ``is_admin`` property, then it would be wasteful
to index all of the individual ``False`` values.

The following conditions are built-in:

* :func:`anom.conditions.is_default`
* :func:`anom.conditions.is_not_default`
* :func:`anom.conditions.is_empty`
* :func:`anom.conditions.is_not_empty`
* :func:`anom.conditions.is_none`
* :func:`anom.conditions.is_not_none`
* :func:`anom.conditions.is_true`
* :func:`anom.conditions.is_false`

But conditions are just functions that take an entity, a property and
the name of that property on the entity and return a boolean value so
you can easily write your own::

  def is_even(entity, prop, name):
    return getattr(entity, name) % 2 == 0

Queries
-------

anom provides a simple DSL for constructing Datastore queries::

  >>> admins_query = User.query().select(User.username).where(
  ...    User.is_admin.is_true,
  ...    User.is_enabled.is_true
  ... )

  >>> admins_query = admins_query.order_by(-User.created_at)

``admins_query`` is roughly equivalent to the following SQL query:

.. code-block:: sql

  SELECT username FROM User
   WHERE is_admin AND is_enabled
   ORDER BY created_at DESC

You can |Query_run| queries to get an iterable result set::

  >>> for admin in admins_query.run():
  ...   print(admin)

Or you can |Query_get| the first result from a query::

  >>> admin_bob = admins_query.and_where(User.username == "bob").get()

|Queries| are *immutable objects* and each instance method simply
returns a new object.  Queries themselves do not execute any calls to
Datastore until you call |Query_get|, |Query_run| or |Query_paginate|
on them.

Resultsets
^^^^^^^^^^

When you |Query_run| a |Query| you get back an iterable |Resultset|
object.  These objects let you efficiently iterate over query results
by fetching data in batches.

You may only iterate over a |Resultset| once.  If you need to keep
results around so you can iterate over them multiple times call
:func:`list` on the resultset.

Pagination
^^^^^^^^^^

When you paginate a |Query| you get back an iterable |Pages| object.
These objects let you iterate over query results in specific
page-sized chunks.  For example::

  >>> all_posts = Posts.query()
  >>> all_pages = all_posts.paginate(page_size=20)

  >>> for page_number, page in enumerate(all_pages, start=1):
  ...   print(f"Page {page_number}:")
  ...
  ...   for post in page:
  ...     print(f"  * {post.title}")

You can also fetch individual pages::

  >>> all_pages = all_posts.paginate(page_size=20)
  >>> page_1 = all_pages.fetch_next_page()
  >>> page_2 = all_pages.fetch_next_page()

Each |Page| object has a |Page_cursor| attribute that represents the
Datastore cursor for the next page of results::

  >>> pages = all_posts.paginate(page_size=20, cursor=page_2.cursor)
  >>> page_3 = pages.fetch_next_page()

Query Options
^^^^^^^^^^^^^

All of the methods that execute queries (i.e. |Query_get|, |Query_run|
and |Query_paginate|) take the following set of options as keyword
arguments:

==============  =========  =====================================================================================================
Option          Default    Description
==============  =========  =====================================================================================================
``batch_size``  ``300``    The number of results to fetch per batch.  If ``limit`` is less than this, ``limit`` is used instead.
``keys_only``   ``False``  Whether or not to fetch only the Keys of the entities that match the query.
``limit``       ``None``   The maximum number of entities to return.
``offset``      ``None``   The number of entities to skip.
``cursor``      ``None``   The start cursor for the query.
==============  =========  =====================================================================================================


Transactions
------------

The |transactional| decorator lets you run a batch of Datastore
operations atomically.

For example::

  from anom import transactional

  @transactional(retries=3)
  def transfer_money(source_account_key, target_account_key, amount):
    source_account, target_account = get_multi([source_account_key, target_account_key])
    source_account.balance -= amount
    target_account.balance += amount
    put_multi([source_account, target_account])

  transfer_money(bank_account_1.key, bank_account_2.key, 20)

If any of the operations in the above function were to fail at any
point, the entire transaction would be rolled back.  The same thing
would happen if the code were to raise an uncaught exception at any
point.

If there is too much contention over a set of entities, transactions
are retried up to ``retries`` amount of times, until the transaction
either succeeds or it runs out of retries.  The default number of
retries is ``3``.

By default, transactions are automatically nested underneath one
another so you can transparently call transactional functions inside
other transactional functions.  This code::

  @transactional()
  def inner(key):
    an_entity = key.get()
    an_entity.foo = 42
    an_entity.put()

  @transactional()
  def outer(key):
    parent = key.get()
    parent.n += 1
    inner(entity.child)
    parent.put()

is equivalent to this code in its behavior::

  @transactional()
  def outer(key):
    parent = key.get()
    parent.n += 1
    an_entity = key.get()
    an_entity.foo = 42
    an_entity.put()
    parent.put()

You can specify that certain transactions should always be run inside
an independent transaction::

  from anom import Transaction, transactional

  @transactional(propagation=Transaction.Propagation.Independent)
  def inner():
    ...

The above transaction will always run independently of any outer
transactions so it won't affect the outer transactions should it fail.


Adapters
--------

|Adapters| define how anom interacts with Datastore: all anom
operations eventually end up being performed by an adapter.

By default, anom creates a |DatastoreAdapter| instance that'll connect
to Datastore based on environment variables at runtime.  You can get
and set the current |Adapter| instance using |get_adapter| and
|set_adapter| respectively.

Read more about adapters in the :doc:`advanced` section.

Testing
-------

The recommended testing framework is pytest_ due to its fantastic
fixture mechanism.

Datastore Emulator
^^^^^^^^^^^^^^^^^^

anom provides the |Emulator| utility class which is able to spin up a
Datastore emulator in a subprocess via the `datastore emulator`_
command, wait for it to initialize and then inject its environment
variables into the current process so that adapters can connect to it
automatically.

Here's how you would use it in a `pytest fixture`_::

  import pytest

  from anom.testing import Emulator

  @pytest.fixture(scope="session")
  def datastore_emulator():
    emulator = Emulator()
    emulator.start(inject=True)
    yield
    emulator.stop()

You can then have tests that depend on it::

  def test_can_create_users(datastore_emulator):
    user = User(username="test").put()
    assert user.key
    user.delete()

Since starting and stopping the emulator takes on the order of a few
seconds, we recommend using a session-scoped emulator fixture and for
individual tests to clean up after themselves.


.. [#] Model instances are known as "entities".
