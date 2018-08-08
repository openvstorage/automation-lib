# Copyright (C) 2017 iNuron NV
#
# This file is part of Open vStorage Open Source Edition (OSE),
# as available from
#
#      http://www.openvstorage.org and
#      http://www.openvstorage.com.
#
# This file is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License v3 (GNU AGPLv3)
# as published by the Free Software Foundation, in version 3 as it comes
# in the LICENSE.txt file of the Open vStorage OSE distribution.
#
# Open vStorage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY of any kind.

"""
TestRailList Module
"""
import operator
from .testrailobject import TestRailBase


class OperatorsMeta(type):
    """
    Metaclass to allow Operators to remain fully static
    """
    def __getattr__(cls, key):
        """
        Overrule getattr to return the string represented in the map
        """
        if key not in cls._map:
            raise AttributeError('{0} does not have attribute \'{1}\''.format(str(cls), key))
        return key


class TestRailList(TestRailBase):
    """
    TestRailList object. Serves as inheritable list which can load TestRailObjects
    """
    # Embedding these inside the list for easier access
    class Operators(object):
        __metaclass__ = OperatorsMeta
        # Map operators to functions for easier evaluation
        _map = {'LT': operator.lt,
                'LE': operator.le,
                'EQ': operator.eq,
                'NE': operator.ne,
                'GE': operator.ge,
                'GT': operator.gt,
                'IN': lambda a, b: a in b}

        @classmethod
        def get_operator(cls, key):
            if key not in cls._map:
                raise RuntimeError('Requested operator could not be found')
            return cls._map[key]

    class WhereOperators(object):
        AND = 'AND'
        OR = 'OR'

    def __init__(self, object_type, client, plural, load_url=None, *args, **kwargs):
        """
        :param object_type: Object Type to load (Example: ..containers.project)
        :param client: API Client
        :param plural: Plural form of the object to load (used in url generation) (Eg. project -> projects)
        :param load_url: The url to load the object from (Could differ when other ids need to be specified)
        """
        super(TestRailList, self).__init__()
        self._client = client
        self._objects_data = []
        self.object_type = object_type
        self.plural = plural

        # Could be set by inheritors (when project_id needs to be linked)
        self.load_url = load_url or self._generate_url('get_all')

    def load(self):
        """
        Loads all given object type items
        :return: A list of instantiated objects (type is the same as the given object type)
        :rtype list
        """
        self._objects_data = self._client.send_get(self.load_url)
        return self._generate_objects(self._objects_data)

    def _generate_objects(self, data):
        """
        Return a generator which yields object instances of the loaded object type
        :param data: List of dicts which represent the to-load object instance
        :return: Generator
        """
        return (self.object_type(client=self._client, **d) for d in data)

    def query(self, query, data=None):
        """
        Perform a query on the current data list
        :param query: Items describing the query
        Definitions:
        * <query>: Should be a dictionary:
                   {'type' : WhereOperator.XYZ,
                    'items': <items>}
        * <filter>: A tuple defining a single expression:
                    (<field>, Operator.XYZ, <value>)
                    The field is any property you would also find on the given object
        * <items>: A list of one or more <query> or <filter> items. This means the query structure is recursive and
                   complex queries are possible
        :param data: Data list to use (default to all fetched data)
        :return: Result of the query
        :rtype: list
        """
        if data is None:
            if len(self._objects_data) == 0:
                self.load()
            data = self._objects_data

        query_items = query['items']
        query_type = query['type']
        results = []
        for data_item in data:
            result, data_item = self._filter(query_items, query_type, data_item)
            if result is True:
                results.append(data_item)
        return self._generate_objects(results)

    def _filter(self, query_items, where_operator, data_item):
        """
        Filter the list
        :param query_items: The query items
        :param where_operator: The WHERE operator
        :param data_item: The data to apply the query on
        This object is passed along for future use (might load in an object based on certain properties)
        :return: The result of the query (success not), the queried items
        :rtype: tuple(bool, any)
        """
        if where_operator not in [self.WhereOperators.AND, self.WhereOperators.OR]:
            raise NotImplementedError('Invalid where operator specified')
        if len(query_items) == 0:
            return True, data_item
        return_value = where_operator == self.WhereOperators.OR
        for query_item in query_items:
            if isinstance(query_item, dict):
                # Nested
                result, data_item = self._filter(query_item['items'], query_item['type'], data_item)
                if result == return_value:
                    return return_value, data_item
            else:
                key = query_item[0]
                op = query_item[1]
                value = query_item[2]
                result, data_item = self._evaluate(key, value, op, data_item)
                if result == return_value:
                    return return_value, data_item
        return not return_value, data_item

    def _evaluate(self, key, value, op, data_item):
        """
        Evaluate a given query on a set of data
        :param key: Key to check on
        :param value: Value to look for
        :param op: Operator to use
        :param data_item: List of data
        :return: The result of the query (success not), the queried items
        :rtype: tuple(bool, list)
        """
        if isinstance(data_item, self.object_type):
            key_value = getattr(data_item, key)
        elif isinstance(data_item, dict):
            key_value = data_item[key]
        else:
            raise RuntimeError('Unable to apply query. Item is not a dict or the given object type')

        return self.Operators.get_operator(op)(key_value, value), data_item

    def _generate_url(self, *args, **kwargs):
        """
        Generates a URL to fetch the object
        :param args: Extra arguments to get passed. Will be separated by /
        :param kwargs: Extra arguments to get passed. Values will be separated by /
        :return: The generated url
        """
        return super(TestRailList, self)._generate_url('get_all', *args, **kwargs)
