.. include:: global.rst

Changelog
=========

v0.0.6
------

* Renamed ``Emulator.terminate`` to |Emulator_stop|.
* Split |Query_where| and |Query_and_where|.

v0.0.5
------

* Added support for conditional indexes on properties.
* Replaced ``Key.is_complete`` with :attr:`anom.Key.is_partial`.
* Dropped ``is_null`` from |Property|.
* Dropped ``__ne__`` from |Property|.

v0.0.4
------

* Added :meth:`fetch_next_page<anom.Pages.fetch_next_page>`.

v0.0.3
------

* Added support for |prop_Computed| properties.
