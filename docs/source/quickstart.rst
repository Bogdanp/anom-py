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

.. _gcloud: https://cloud.google.com/sdk/
.. _official docs:
.. _Datastore Emulator: https://cloud.google.com/datastore/docs/tools/datastore-emulator


Models
------

Models define how data is shaped in Datastore and where it should be
stored.  To get started, import :class:`Model<anom.Model>` and
:mod:`props<anom.properties>` from the :mod:`anom` module::

  >>> from anom import Model, props

.. note::

   ``anom.props`` is an alias for the :mod:`anom.properties` module
   for convenience.

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
   :class:`anom.Model` class.

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
instantiate models::

  >>> greeting = Greeting(email="someone@example.com", message="Hi!")

Every entity\ [#]_ has a :class:`Key<anom.Key>` that you can access via
its :attr:`key<anom.Model.key>` attribute.  Entities that have not yet
been saved have what are known as partial keys, keys without an id
assigned to them.

You can store the greeting by calling its :meth:`put<anom.Model.put>`
method.  Doing so will serialize the entity, store it in Datastore and
update its key to point to its location in Datastore.

You can get the greeting's automatically-assigned id by accessing
:attr:`int_id<anom.Key.int_id>` or :attr:`id_or_name<anom.Key.id_or_name>`
on its key::

  >>> greeting.key.int_id
  1001

You can fetch entities by id by calling :meth:`get<anom.Model.get>`::

  >>> same_greeting = Greeting.get_by_id(1001)  # Replace 1001 with whatever id your greeting was assigned
  >>> same_greeting
  Greeting(Key("Greeting", 1001, parent=None, namespace=None), email="someone@example.com", message="Hi!", created_at=..., updated_at=...)

Entities can be compared for equality::

  >>> same_greeting == greeting
  True

Finally, to delete an entity, you can call :meth:`delete<anom.Model.delete>`
on it::

  >>> greeting.delete()

Doing so will permanently remove it from Datastore.


Properties
----------

The following properties are built-in:

=================================  ============================================================
Property                           Description
=================================  ============================================================
:class:`anom.properties.Bool`      Stores :class:`bool` values.
:class:`anom.properties.Bytes`     Stores blobs of binary data (:class:`bytes`). Never indexed.
:class:`anom.properties.Computed`  Stores values computed by arbitrary functions.
:class:`anom.properties.DateTime`  Stores :class:`datetime.datetime` values.
:class:`anom.properties.Float`     Stores :class:`float` values.
:class:`anom.properties.Integer`   Stores :class:`int` values.
:class:`anom.properties.Json`      Stores JSON values. Never indexed.
:class:`anom.properties.Key`       Stores :class:`anom.Key` values.
:class:`anom.properties.String`    Stores :class:`str` values.
:class:`anom.properties.Text`      Stores long :class:`str` values. Never indexed.
=================================  ============================================================

All of these support the following options:

============  =========  ===============================================================================================================================
Option        Default    Description
============  =========  ===============================================================================================================================
``name``      ``None``   The name of the property on the stored entity in Datastore. Defaults to its name on the model.
``default``   ``None``   The default value to return when the property isn't populated with data.
``indexed``   ``False``  Whether or not the property should be indexed in Datastore. Bytes, Json and Text properties cannot be indexed.
``optional``  ``False``  Whether or not the property is optional. Required-but-empty values cause models to raise an exception before data is persisted.
``repeated``  ``False``  Whether or not the property is repeated.
============  =========  ===============================================================================================================================

Compressable Properties
^^^^^^^^^^^^^^^^^^^^^^^

The following properties can compress/decompress their values before
storing/loading them to/from Datastore:

* :class:`anom.properties.Bytes`
* :class:`anom.properties.Json`
* :class:`anom.properties.String`
* :class:`anom.properties.Text`

Compressable properties support the following additional options:

=====================  =========  ============================================================================================================================
Option                 Default    Description
=====================  =========  ============================================================================================================================
``compressed``         ``False``  Whether or not values assigned to this property should be compressed.
``compression_level``  ``-1``     The amount of compression to apply. This must be an integer between ``-1`` and ``9``. See :func:`zlib.compress` for details.
=====================  =========  ============================================================================================================================

Compression is applied as late as possible (on ``put``) to avoid
wasting CPU so assigning values to compressed properties has no
additional cost.

DateTime Properties
^^^^^^^^^^^^^^^^^^^

:class:`DateTimes<anom.properties.DateTime>` support the following
additional set of options:

================  =========  =========================================================================================================================================
Option            Default    Description
================  =========  =========================================================================================================================================
``auto_now_add``  ``False``  Whether or not this value should default to the current time the first time it's saved.  You'd use this for `created_at` type properties.
``auto_now``      ``False``  Whether or not this value should default to the current time every time it's saved.  You'd use this for `updated_at` type properties.
================  =========  =========================================================================================================================================

Encodable Properties
^^^^^^^^^^^^^^^^^^^^

:class:`String<anom.properties.String>` and :class:`Text<anom.properties.Text>`
properties have an ``encoding`` option which controls how their values
should be encoded/decoded before storing/loading them to/from
Datastore.  The default ``encoding`` is ``utf-8``.


Keys
----

:class:`Keys<anom.Key>` represent the locations of individual entities
inside Datastore.  They consist of a Datastore kind, an optional id,
an optional parent key and an optional namespace.  Keys are immutable
and they can be stored on individual entities via
:class:`Key<anom.properties.Key>` properties.

You can instantiate new keys::

  >>> greeting_key = Key("Greeting", 1001)

And you can use them to get entities::

  >>> greeting = greeting_key.get()

Or to delete them::

  >>> greeting_key.delete()

Keys can have ancestors::

  >>> jim_key = Key("Person", "Jim", parent=Key("Person", "John"))

And namespaces::

  >>> jim_key_in_ns = Key("Person", "Jim", namespace="people")


Indexes
-------

Writing a new single-property index requires two Datastore operations
and changing an existing single-property index requires *four*.  With
large Models this cost can add up quickly, increasing the time it takes
for data to become consistent across Datastore and increasing your
overall Datastore costs.

For this reason, all anom properties except for :class:`Computed<anom.properties.Computed>`
are *unindexed by default*.  This means that if you want to query a
property you must decide up front if it's going to be indexed or not.

Changing a property from unindexed to indexed (or vice-versa) on your
model **will not** affect the indexing schemes of previously-saved
data.  You must re-save individual entities in order to add or remove
indexes.

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

  # This query would return all admin users.
  all_admins = User.query().where(User.is_admin.is_true).run()

  # whereas this wouldn't return any users at all.
  no_users = User.query().where(User.is_admin.is_false).run()

If you only ever need to query for the (presumably small) subset of
admins based on the ``is_admin`` property, then it would be wasteful
to index all of the individual ``False`` values.

The following conditions are built-in:

* :func:`anom.conditions.is_default`
* :func:`anom.conditions.is_empty`
* :func:`anom.conditions.is_true`
* :func:`anom.conditions.is_false`
* :func:`anom.conditions.is_null`
* :func:`anom.conditions.is_not_null`


Queries
-------

anom provides a simple DSL for constructing Datastore queries::

  >>> admins_query = User.query().select(User.username).where(
  ...    User.is_admin.is_true,
  ...    User.is_enabled.is_true
  ... )

  >>> admins_query = admins_query.order_by(-User.created_at)

``admins_query`` is roughly equivalent to the following SQL query::

  SELECT username FROM User
   WHERE is_admin AND is_enabled
   ORDER BY created_at DESC

You can :meth:`run<anom.Query.run>` queries to get an iterable result
set::

  >>> for admin in admins_query.run():
  ...   print(admin)

Or you can :meth:`get<anom.Query.get>` the first result from a query::

  >>> admin_bob = admins_query.and_where(User.username == "bob").get()

:class:`Queries<anom.Query>` are *immutable objects* and each instance
method simply returns a new object.  Queries themselves do not execute
any calls to Datastore until you call :meth:`run<anom.Query.run>`,
:meth:`paginate<anom.Query.paginate>` or :meth:`get<anom.Query.get>`
on them.

Resultsets
^^^^^^^^^^

When you run a :class:`Query<anom.Query>` you get back an iterable
:class:`Resultset<anom.Resultset>` object.  They let you efficiently
iterate over query results by fetching result data in batches.  Each
resultset may only be iterated over once.

Pagination
^^^^^^^^^^

When you paginate a :class:`Query<anom.Query>` you get back an
iterable :class:`Pages<anom.Pages>` object.  These objects let you
iterate over query results in specific page-sized chunks.  For
example::

  >>> all_posts = Posts.query()
  >>> all_pages = all_posts.paginate(page_size=20)

  >>> for i, page in enumerate(all_pages):
  ...   print(f"Page {i + 1}:")
  ...
  ...   for post in page:
  ...     print(f"  * {post.title}")

You can also fetch individual pages::

  >>> all_pages = all_posts.paginate(page_size=20)
  >>> page_1 = all_pages.fetch_next_page()
  >>> page_2 = all_pages.fetch_next_page()

Each :class:`Page<anom.Page>` object has a :attr:`cursor<anom.Page.cursor>`
attribute that represents the Datastore cursor for the next page of results::

  >>> pages = all_posts.paginate(page_size=20, cursor=page_2.cursor)
  >>> page_3 = pages.fetch_next_page()

Query Options
^^^^^^^^^^^^^

FIXME


Transactions
------------

FIXME


Adapters
--------

FIXME


.. [#] Model instances are known as "entities".
