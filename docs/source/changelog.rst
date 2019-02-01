.. include:: global.rst

Changelog
=========

v0.9.0
------

* Updated `gcloud-requests` and `google-cloud-datastore` to versions
  2.0 and 1.7, respectively.

v0.8.0
------

* Added support for ``Unicode`` properties.  (`#13`_, `@JorinTielen`_)
* Repeated properties are now always stored as lists, regardless of
  whether ``None`` is assigned to them or not. (`#11`_)
* Fixed an issue with repeated key properties being returned as
  ``datastore.Key`` objects instead of ``anom.Key`` objects. (`#14`_)

.. _#11: https://github.com/Bogdanp/anom-py/pull/11
.. _#13: https://github.com/Bogdanp/anom-py/pull/13
.. _#14: https://github.com/Bogdanp/anom-py/pull/14
.. _@JorinTielen: https://github.com/JorinTielen

v0.7.1
------

* Fixed an issue that caused assigning ``None`` to optional indexed
  ``Strings`` to fail.  (`#10`_, `@JorinTielen`_)

.. _#10: https://github.com/Bogdanp/anom-py/pull/10
.. _@JorinTielen: https://github.com/JorinTielen

v0.7.0
------

* Added support for ``Embed`` properties.
* Fixed inconsistent internal usages of ``name_on_{entity,model}``.
* Fixed an issue that made ``indexed_if`` act like ``indexed_unless``.
* Fixed logger names.

v0.6.3
------

* Fixed an issue where ``TransactionFailed`` exceptions had
  unprintable messages.

v0.6.2
------

* Fixed an issue where setting entity keys inside `pre_put_hook` would
  not have an effect on where those entities were stored.

v0.6.0
------

* Added ``host`` and ``port`` params to ``Emulator``.
* Added ``count`` and ``delete`` to ``Query``.
* Refactored ``DatastoreAdapter`` to no longer use thread-local DS
  client instances.

v0.5.0
------

* Added support for managing namespaces.

v0.4.5
------

* Handle a potential race condition during Emulator shutdown.

v0.4.4
------

* Fixed an issue with repeated Key properties (`#5`_).

.. _#5: https://github.com/Bogdanp/anom-py/issues/5

v0.4.3
------

* Fixed an issue with filtering by Keys (`#4`_).

.. _#4: https://github.com/Bogdanp/anom-py/issues/4

v0.4.2
------

* Pinned ``gcloud-requests`` to version ``1.1.9``.

v0.4.1
------

* Pinned ``gcloud-requests`` to version ``1.1.8``.

v0.4.0
------

* Added support for declaring models' kinds.
* Added support for kindless Queries.

v0.3.1
------

* Updated google-cloud-datastore_ to version ``1.0.0``.

.. _google-cloud-datastore: https://github.com/GoogleCloudPlatform/google-cloud-python/releases/tag/datastore-1.0.0

v0.3.0
------

* Fixed late-bound keys inside transactions (`#3`_).
* **Breaking change:** changed the locked item value in
  |MemcacheAdapter|.

.. _#3: https://github.com/Bogdanp/anom-py/issues/3

v0.2.0
------

* Added |MemcacheAdapter|.
* Added support for |prop_Msgpack| properties.
* Added support for Json serialization of datetimes, Models and Keys.

v0.1.0
------

* Added support for |Transactions|.

v0.0.7
------

* Fixed handling of repeated values in |prop_Encodable| properties.
* Added support for model polymorphism.
* Added |Pages_cursor| to |Pages|.

v0.0.6
------

* Fixed |Model| inheritance.
* Split |Query_where| and |Query_and_where|.
* Renamed ``Emulator.terminate`` to |Emulator_stop|.

v0.0.5
------

* Added support for conditional indexes on properties.
* Replaced ``Key.is_complete`` with |Key_is_partial|.
* Dropped ``is_null`` from |Property|.
* Dropped ``__ne__`` from |Property|.

v0.0.4
------

* Added :meth:`fetch_next_page<anom.Pages.fetch_next_page>`.

v0.0.3
------

* Added support for |prop_Computed| properties.
