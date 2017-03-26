.. include:: global.rst

Changelog
=========

v0.0.7
------

* Fixed handling of repeated values in |prop_Encodable| properties.
* Added support for model polymorphism.

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
