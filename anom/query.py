from collections import namedtuple


class PropertyFilter(namedtuple("PropertyFilter", ("name", "operator", "value"))):
    """Represents an individual filter on a Property within a Query.
    """


class QueryOptions(dict):
    """Options that determine how data is fetched from the Datastore
    on a per Query basis.

    Parameters:
      batch_size(int, optional): The number of results to fetch per batch.
      keys_only(bool, optional): Whether or not the results should be
        Keys or Entities.
      limit(int, optional): The maximum number of results to return.
      offset(int, optional): The number of results to skip.
      cursor(str, optional): A url-safe cursor representing where in
        the result set the query should start.
    """

    def __init__(self, query, **options):
        super().__init__(**options)

        self.query = query

    def replace(self, **options):
        """Update this options object in place.

        Parameters:
          \**options(QueryOptions)

        Returns:
          QueryOptions: The updated instance.
        """
        self.update(options)
        return self

    @property
    def batch_size(self):
        """int: The number of results to fetch per batch.  Clamped to
        limit if limit is set and is smaller than the given batch
        size.
        """
        batch_size = self.get("batch_size", 300)
        if self.limit is not None:
            return min(self.limit, batch_size)
        return batch_size

    @property
    def keys_only(self):
        "bool: Whether or not the results should be Keys or Entities."
        return self.get("keys_only", False)

    @property
    def limit(self):
        "int: The maximum number of results to return."
        return self.get("limit", self.query.limit)

    @property
    def offset(self):
        "int: The number of results to skip."
        return self.get("offset", self.query.offset)

    @property
    def cursor(self):
        "bytes: The url-safe cursor for a query."
        return self.get("cursor", b"")

    @cursor.setter
    def cursor(self, value):
        self["cursor"] = value


class Resultset:
    """An iterator for datastore query results.

    Parameters:
     query(Query): The query that was run to create this resultset.
     options(QueryOptions): Options that determine how entities are
       fetched from Datastore.
    """

    def __init__(self, query, options):
        self._query = query
        self._options = options
        self._complete = False
        self._entities = self._get_entities()

    @property
    def cursor(self):
        "str: The url-safe cursor for the next batch of results."
        return self._options.cursor

    @property
    def has_more(self):
        "bool: Whether or not there are more results."
        return not self._complete

    def __iter__(self):
        return self

    def __next__(self):
        return next(self._entities)

    def _get_batches(self):
        from .adapter import get_adapter

        remaining = self._options.limit
        while True:
            adapter = self._query.model._adapter if self._query.model else get_adapter()
            entities, self._options.cursor = adapter.query(self._query, self._options)
            if remaining is not None:
                remaining -= len(entities)
                if remaining < 0:
                    entities = entities[:remaining]

            if not entities:
                break

            # If we received fewer entities than we asked for then we
            # can safely say that we've finished iterating.  We have
            # to do this before yielding, however.
            if len(entities) < self._options.batch_size:
                self._complete = True

            if self._options.keys_only:
                yield (key for key, _ in entities)
            else:
                yield (key.get_model()._load(key, data) for key, data in entities)

            if remaining is not None and remaining <= 0:
                break

        self._complete = True

    def _get_entities(self):
        for batch in self._get_batches():
            yield from batch


class Page:
    """An iterator that represents a single page of entities or keys.

    Parameters:
      cursor(str): The url-safe cursor for the next page of results.
      batch(iterator[Model or anom.Key]): The batch of results backing
        this Page.
    """

    def __init__(self, cursor, batch):
        self._cursor = cursor
        self._batch = batch

    @property
    def cursor(self):
        "str: The url-safe cursor for the next page of results."
        return self._cursor

    def __iter__(self):
        return self

    def __next__(self):
        return next(self._batch)


class Pages:
    """An iterator for :class:`Pages<Page>` of results.

    Parameters:
     query(Query): The query that was run to create this resultset.
     options(QueryOptions): Options that determine how entities are
       fetched from Datastore.
    """

    def __init__(self, query, page_size, options):
        options = QueryOptions(query, **options)
        options.update(batch_size=page_size)

        self._resultset = Resultset(query, options)
        self._pages = self._get_pages()

    @property
    def has_more(self):
        "bool: Whether or not there are more pages."
        return self._resultset.has_more

    @property
    def cursor(self):
        "str: The url-safe cursor for the next page of results."
        return self._resultset.cursor

    def fetch_next_page(self):
        """Fetch the next Page of results.

        Returns:
          Page: The next page of results.
        """
        for page in self:
            return page
        else:
            return Page(self._resultset.cursor, iter(()))

    def __iter__(self):
        return self

    def __next__(self):
        return next(self._pages)

    def _get_pages(self):
        for batch in self._resultset._get_batches():
            yield Page(self._resultset.cursor, batch)


class Query(namedtuple("Query", (
    "model", "kind", "ancestor", "namespace", "projection", "filters", "orders", "offset", "limit",
))):
    """An immutable Datastore query.

    Parameters:
      kind(str or model): The Datastore kind to query.
      ancestor(anom.Key, optional): The ancestor to which this query should be scoped.
      namespace(str, optional): The namespace to which this query should be scoped.
      projection(tuple[str], optional): The tuple or tuple of fields to project.
      filters(tuple[PropertyFilter], optional): The tuple of filters to apply.
      orders(tuple[str], optional): The tuple of sort orders to apply.
      offset(int, optional): The number of query results to skip.
      limit(int, optional): The maximum number of results to return.

    Example:

      You can construct queries declaratively::

        people_query = Query(Person)
          .where(Person.email == "test@example.com")
          .and_where(Person.enabled.is_true)
          .with_limit(10)

      Then run them to iterate over all the results::

        all_people = people_query.run()
        for person in all_people:
          print(person)

      Or paginate over them::

        for page in people_query.paginate(page_size=10):
          print("Cursor: ", page.cursor)
          for person in page:
            print(person)

      Or get individual pages of results::

        page_1 = people_query.paginate(page_size=10).fetch_next_page()
        page_2 = people_query.paginate(page_size=10, cursor=page_1.cursor).fetch_next_page()

    """

    def __new__(
            cls, kind=None, *, ancestor=None, namespace=None,
            projection=(), filters=(), orders=(), offset=0, limit=None,
    ):
        from .model import lookup_model_by_kind

        if kind is None:
            model = None

        elif isinstance(kind, str):
            model = lookup_model_by_kind(kind)

        else:
            model, kind = kind, kind._kind

        return super().__new__(
            cls, model=model, kind=kind, ancestor=ancestor, namespace=namespace,
            projection=_prepare_projection(projection), filters=tuple(filters), orders=tuple(orders),
            offset=offset, limit=limit,
        )

    def select(self, *projection):
        """Return a new query with its projection replaced.

        Parameters:
          \*projection(str): The fields to project.

        Returns:
          Query: The derived Query.
        """
        return self._replace(projection=_prepare_projection(projection))

    def where(self, *filters):
        """Return a new query, replacing the current set of filters.

        Parameters:
          \*filters(PropertyFilter): The filters to add.

        Returns:
          Query: The derived Query.
        """
        return self._replace(filters=filters)

    def and_where(self, *filters):
        """Return a new query, adding joining the given filters with
        the current query's filters to form an "and".

        Parameters:
          \*filters(PropertyFilter): The filters to add.

        Returns:
          Query: The derived Query.
        """
        return self._replace(filters=self.filters + filters)

    def order_by(self, *orders):
        """Returns a new query containing an additional set of orders.

        Parameters:
          \*orders(str): The sort orders to add.

        Returns:
          Query: The derived Query.
        """
        return self._replace(orders=self.orders + orders)

    def with_ancestor(self, ancestor):
        """Returns a new query with its ancestor updated.

        Parameters:
          ancestor(anom.Key): The new ancestor.

        Returns:
          Query: The derived Query.
        """
        return self._replace(ancestor=ancestor)

    def with_namespace(self, namespace):
        """Returns a new query with its namespace updated.

        Parameters:
          namespace(str): The new namespace.

        Returns:
          Query: The derived Query.
        """
        return self._replace(namespace=namespace)

    def with_offset(self, offset):
        """Returns a new query with its offset updated.

        Parameters:
          offset(int): The new offset.

        Returns:
          Query: The derived Query.
        """
        return self._replace(offset=offset)

    def with_limit(self, limit):
        """Returns a new query with its limit updated.

        Parameters:
          limit(int): The new limit.

        Returns:
          Query: The derived Query.
        """
        return self._replace(limit=limit)

    def get(self, **options):
        """Run this query and get the first result.

        Parameters:
          \**options(QueryOptions, optional)

        Returns:
          Model: An entity or None if there were no results.
        """
        sub_query = self.with_limit(1)
        options = QueryOptions(sub_query).replace(batch_size=1)
        for result in sub_query.run(**options):
            return result
        return None

    def run(self, **options):
        """Run this query and return a result iterator.

        Parameters:
          \**options(QueryOptions, optional)

        Returns:
          Resultset: An iterator for this query's results.
        """
        return Resultset(self._prepare(), QueryOptions(self, **options))

    def paginate(self, *, page_size, **options):
        """Run this query and return a page iterator.

        Parameters:
          page_size(int): The number of entities to fetch per page.
          \**options(QueryOptions, optional)

        Returns:
          Pages: An iterator for this query's pages of results.
        """
        return Pages(self._prepare(), page_size, QueryOptions(self, **options))

    def _prepare(self):
        # Polymorphic children need to be able to query for themselves
        # and their subclasses.
        if self.model and self.model._is_child:
            kind_filter = (self.model._kinds_name, "=", self.model._kinds[0])
            return self._replace(filters=(kind_filter,) + self.filters)

        return self


def _prepare_projection(projection):
    return tuple(f if isinstance(f, str) else f.name_on_entity for f in projection)
