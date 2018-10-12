from __future__ import absolute_import
import logging
import time

import requests

logger = logging.getLogger(__name__)

requests_logger = logging.getLogger('requests.packages.urllib3')
requests_logger.setLevel(logging.WARNING)


class ItemSet(list):
    def __init__(self, *args, **kwargs):
        self._item_class = None
        return super(ItemSet, self).__init__(*args, **kwargs)

    def find_all(self, **kwargs):
        filtered = ItemSet(
            x for x in self
            if all(getattr(x, k) == v for k, v in kwargs.items()))
        filtered._item_class = self._item_class
        return filtered

    def find(self, **kwargs):
        items = self.find_all(**kwargs)
        if items:
            return items[0]
        else:
            raise NotFound(self._item_class, **kwargs)


class Collection(object):

    _list_url = 'get_{name}s'
    _add_url = 'add_{name}'

    def __init__(self, item_class=None, parent_id=None, **kwargs):
        self._item_class = item_class
        self._handler = self._item_class._handler
        self.parent_id = parent_id
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __call__(self, id=None):
        name = self._item_class._api_name()
        if id is None:
            items = self._list(name)
            if 'error' in items:
                raise Exception(items)
            items = ItemSet(self._to_object(x) for x in items)
            items._item_class = self._item_class
            return items

        else:
            return self._item_class.get(id)

    def __repr__(self):
        return '<Collection of {}>'.format(self._item_class.__name__)

    def _to_object(self, data):
        return self._item_class(**data)

    def _list(self, name, params=None):
        params = params or {}
        url = self._list_url.format(name=name)
        if self.parent_id is not None:
            url += '/{}'.format(self.parent_id)
        return self._handler('GET', url, params=params)

    def find_all(self, **kwargs):
        return self().find_all(**kwargs)

    def find(self, **kwargs):
        # if plan is searched perform an additional GET request to API
        # in order to return full its data including 'entries' field
        # see http://docs.gurock.com/testrail-api2/reference-plans#get_plans
        if self._item_class is Plan:
            return self.get(self().find(**kwargs).id)
        return self().find(**kwargs)

    def get(self, id):
        return self._item_class.get(id)

    def list(self):
        name = self._item_class._api_name()
        return ItemSet([self._item_class(**i) for i in self._list(name=name)])


class Item(object):
    _get_url = 'get_{name}/{id}'
    _update_url = 'update_{name}/{id}'
    _handler = None
    _repr_field = 'name'

    def __init__(self, id=None, **kwargs):
        self.id = id
        self._data = kwargs

    @classmethod
    def _api_name(cls):
        return cls.__name__.lower()

    def __getattr__(self, name):
        if name in self._data:
            return self._data[name]
        else:
            raise AttributeError

    def __setattr__(self, name, value):
        if '_data' in self.__dict__ and name not in self.__dict__:
            self.__dict__['_data'][name] = value
        else:
            self.__dict__[name] = value

    def __repr__(self):
        name = getattr(self, self._repr_field, '')
        name = repr(name)
        return '<{c.__name__}({s.id}) {name} at 0x{id:x}>'.format(
            s=self, c=self.__class__, id=id(self), name=name)

    @classmethod
    def get(cls, id):
        name = cls._api_name()
        url = cls._get_url.format(name=name, id=id)
        result = cls._handler('GET', url)
        if 'error' in result:
            raise Exception(result)
        return cls(**result)

    def update(self):
        url = self._update_url.format(name=self._api_name(), id=self.id)
        self._handler('POST', url, json=self.data)

    @property
    def data(self):
        return self._data


class Project(Item):
    @property
    def suites(self):
        return Collection(Suite, parent_id=self.id)


class Suite(Item):
    @property
    def cases(self):
        return CaseCollection(
            Case,
            _list_url='get_cases/{}&suite_id={}'.format(self.project_id,
                                                        self.id))


class CaseCollection(Collection):
    pass


class Case(Item):
    pass


class Plan(Item):
    def __init__(self,
                 name,
                 description=None,
                 milestone_id=None,
                 entries=None,
                 id=None,
                 **kwargs):
        add_kwargs = {
            'name': name,
            'description': description,
            'milestone_id': milestone_id,
            'entries': entries or [],
        }
        kwargs.update(add_kwargs)
        return super(self.__class__, self).__init__(id, **kwargs)


class Client(object):
    def __init__(self, base_url, username, password):
        self.username = username
        self.password = password
        self.base_url = base_url.rstrip('/') + '/index.php?/api/v2/'

        Item._handler = self._query

    def _query(self, method, url, **kwargs):
        url = self.base_url + url
        headers = {'Content-type': 'application/json'}
        logger.debug('Make {} request to {}'.format(method, url))
        for _ in range(5):
            response = requests.request(
                method,
                url,
                allow_redirects=False,
                auth=(self.username, self.password),
                headers=headers,
                **kwargs)
            # To many requests
            if response.status_code == 429:
                time.sleep(60)
                continue
            else:
                break
        # Redirect or error
        if response.status_code >= 300:
            raise requests.HTTPError("Wrong response:\n"
                                     "status_code: {0.status_code}\n"
                                     "headers: {0.headers}\n"
                                     "content: '{0.content}'".format(response),
                                     response=response)
        result = response.json()
        if 'error' in result:
            logger.warning(result)
        return result

    @property
    def projects(self):
        return Collection(Project)


class NotFound(Exception):
    def __init__(self, item_class, **conditions):
        self.item_class = item_class
        self.conditions = conditions

    def __str__(self):
        conditions = ', '.join(['{}="{}"'.format(x, y)
                               for (x, y) in self.conditions.items()])
        return u'{type} with {conditions}'.format(
            type=self.item_class._api_name().title(),
            conditions=conditions)