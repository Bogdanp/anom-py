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

and then access their properties as if they were normal class
attributes (under the hood, that's more or less what they are!)::

  >>> greeting.email = "someone@example.com"
  >>> print(greeting.email)
  someone@example.com
  >>> print(greeting.message)
  None

You can also specify which properties should be populated when you
instantiate models::

  >>> greeting = Greeting(email="someone@example.com", message="Hi!")

Every model has a :class:`Key<anom.Key>` that you can access via
its :attr:`key<anom.Model.key>` attribute. Models that have not yet
been saved have what are known as partial keys, keys without an id
assigned to them. You can store the greeting by calling its
:meth:`put<anom.Model.put>` method. Doing so will serialize the
entity, store it in Datastore and update its key to point to its
Datastore location.  The Keys_ section offers more information on
keys.

You can get the greeting's automatically-assigned id by accessing
:attr:`int_id<anom.Key.int_id>` or :attr:`id_or_name<anom.Key.id_or_name>`
on its key::

  >>> print(greeting.key.int_id)
  1001

You can load entities by id by calling :meth:`get<anom.Model.get>`::

  >>> same_greeting = Greeting.get_by_id(1001)  # Replace 1001 with whatever id your greeting was assigned
  >>> same_greeting
  Greeting(Key("Greeting", 1001, parent=None, namespace=None), email="someone@example.com", message="Hi!", created_at=..., updated_at=...)

Entities can be compared for equality::

  >>> same_greeting == greeting
  True

To delete an entity, you can call :meth:`delete<anom.Model.delete>` on it::

  >>> greeting.delete()

Doing so will permanently remove it from Datastore.


Properties
^^^^^^^^^^

The following properties are built-in:

=================================  ============================================================
Property                              Description
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

Keys
^^^^

FIXME


Queries
-------

FIXME


Transactions
------------

FIXME


Adapters
--------

FIXME
