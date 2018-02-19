.. include:: global.rst

Changelog
=========

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
