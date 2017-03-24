Changelog
=========

v0.0.5
------

* Added support for conditional indexes on properties
* Replaced ``Key.is_complete`` with :attr:`anom.Key.is_partial`.
* Dropped ``is_null`` from :class:`anom.Property`
* Dropped ``__ne__`` from :class:`anom.Property` as it's not natively
  supported.


v0.0.4
------

* Added :meth:`fetch_next_page<anom.Pages.fetch_next_page>`.

v0.0.3
------

* Added support for :class:`Computed<anom.properties.Computed>` properties.
