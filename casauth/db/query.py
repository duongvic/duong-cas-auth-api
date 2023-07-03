from math import ceil

from oslo_utils import importutils
from casauth.common import cfg
from casauth.common import exceptions as cas_exc
from casauth.db.sqlalchemy import api as md_api

CONF = cfg.CONF


class Query(object):
    """Mimics sqlalchemy query object.

    This class allows us to store query conditions and use them with
    bulk updates and deletes just like sqlalchemy query object.
    Using this class makes the models independent of sqlalchemy

    """

    def __init__(self, model, query_func=None, **conditions):
        self._query_func = query_func
        self._model = model
        self._conditions = conditions

    def all(self):
        return md_api.list_all(self._query_func, self._model,
                               **self._conditions)

    def count(self):
        return md_api.count(self._query_func, self._model,
                            **self._conditions)

    def first(self):
        return md_api.first(self._query_func, self._model,
                            **self._conditions)

    def join(self, *args):
        return md_api.join(self._query_func, self._model, *args)

    def __iter__(self):
        return iter(self.all())

    def update(self, **values):
        md_api.update_all(self._query_func, self._model, self._conditions,
                          values)

    def delete(self):
        md_api.delete_all(self._query_func, self._model,
                          **self._conditions)

    def limit(self, limit=200, marker=None, marker_column=None):
        return md_api.find_all_by_limit(
            self._query_func,
            self._model,
            self._conditions,
            limit=limit,
            marker=marker,
            marker_column=marker_column)

    def paginated_collection(self, limit=200, marker=None, marker_column=None):
        collection = self.limit(int(limit) + 1, marker, marker_column)
        if len(collection) > int(limit):
            return (collection[0:-1], collection[-2]['id'])
        return (collection, None)

    def paginate(self, page=None, per_page=None, error_out=True, max_per_page=None):
        args = self._conditions.pop('args', None)
        order_by = self._conditions.pop('order_by', None)
        if args:
            query = md_api.query(self._model, *args, order_by=order_by, **self._conditions)
        else:
            query = md_api.query(self._model, order_by=order_by, **self._conditions)
        if page is None:
            page = 1

        if per_page is None:
            per_page = 20

        if max_per_page is not None:
            per_page = min(per_page, max_per_page)

        if page < 1:
            if error_out:
                pass
            else:
                page = 1

        if per_page < 0:
            if error_out:
                pass
            else:
                per_page = 20

        items = query.limit(per_page).offset((page - 1) * per_page).all()
        if not items and page != 1 and error_out:
            pass

        total = query.order_by(None).count()

        return Pagination(self, page, per_page, total, items)


class Pagination(object):
    """Internal helper class returned by :meth:`BaseQuery.paginate`.  You
    can also construct it from any other SQLAlchemy query object if you are
    working with other libraries.  Additionally it is possible to pass `None`
    as query object in which case the :meth:`prev` and :meth:`next` will
    no longer work.
    """

    def __init__(self, query, page, per_page, total, items):
        #: the unlimited query object that was used to create this
        #: pagination object.
        self.query = query
        #: the current page number (1 indexed)
        self.page = page
        #: the number of items to be displayed on a page.
        self.per_page = per_page
        #: the total number of items matching the query
        self.total = total
        #: the items for the current page
        self.items = items

    @property
    def pages(self):
        """The total number of pages"""
        if self.per_page == 0:
            pages = 0
        else:
            pages = int(ceil(self.total / float(self.per_page)))
        return pages

    def prev(self, error_out=False):
        """Returns a :class:`Pagination` object for the previous page."""
        assert self.query is not None, 'a query object is required ' \
                                       'for this method to work'
        return self.query.paginate(self.page - 1, self.per_page, error_out)

    @property
    def prev_num(self):
        """Number of the previous page."""
        if not self.has_prev:
            return None
        return self.page - 1

    @property
    def has_prev(self):
        """True if a previous page exists"""
        return self.page > 1

    def next(self, error_out=False):
        """Returns a :class:`Pagination` object for the next page."""
        assert self.query is not None, 'a query object is required ' \
                                       'for this method to work'
        return self.query.paginate(self.page + 1, self.per_page, error_out)

    @property
    def has_next(self):
        """True if a next page exists."""
        return self.page < self.pages

    @property
    def next_num(self):
        """Number of the next page"""
        if not self.has_next:
            return None
        return self.page + 1

    def iter_pages(self, left_edge=2, left_current=2,
                   right_current=5, right_edge=2):
        """Iterates over the page numbers in the pagination.  The four
        parameters control the thresholds how many numbers should be produced
        from the sides.  Skipped page numbers are represented as `None`.
        This is how you could render such a pagination in the templates:

        .. sourcecode:: html+jinja

            {% macro render_pagination(pagination, endpoint) %}
              <div class=pagination>
              {%- for page in pagination.iter_pages() %}
                {% if page %}
                  {% if page != pagination.page %}
                    <a href="{{ url_for(endpoint, page=page) }}">{{ page }}</a>
                  {% else %}
                    <strong>{{ page }}</strong>
                  {% endif %}
                {% else %}
                  <span class=ellipsis>…</span>
                {% endif %}
              {%- endfor %}
              </div>
            {% endmacro %}
        """
        last = 0
        for num in range(1, self.pages + 1):
            if num <= left_edge or \
                    (num > self.page - left_current - 1 and
                     num < self.page + right_current) or \
                    num > self.pages - right_edge:
                if last + 1 != num:
                    yield None
                yield num
                last = num


class Queryable(object):

    def __getattr__(self, item):
        return lambda model, **conditions: Query(
            model, query_func=getattr(md_api, item), **conditions)


db_query = Queryable()
