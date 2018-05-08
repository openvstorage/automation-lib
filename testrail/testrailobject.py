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
Testrail object module
- TestRailObject: An inheritable object which uses to API
"""

import copy
import json
from itertools import chain


class ChangeTracker(object):
    """
    Tracks changes
    """
    def __init__(self):
        self.changed = False


class TestRailBase(object):
    """
    Base class for TestRail related objects
    """
    def __init__(self):
        super(TestRailBase, self).__init__()
        # self._change_tracker = ChangeTracker()
        # Needs to be set by inheritors
        self.plural = None

    def _assert_key(self, keyname):
        error = RuntimeError('Unable to fetch the object without the identifier.')
        if hasattr(self, keyname):
            if getattr(self, keyname) is None:
                raise error
            return
        raise error

    def _generate_url(self, method, *args, **kwargs):
        """
        Generates a URL to fetch the object
        :param method: Method to generate for
        :param args: Extra arguments to get passed. Will be separated by /
        :param kwargs: Extra arguments to get passed. Values will be separated by /
        :return: The generated url
        """
        supported_methods = ['update', 'add', 'delete', 'get', 'get_all']
        if method not in supported_methods:
            raise RuntimeError('Unsupported method {0}. Supported methods are: {1}'.format(method, ', '.join(supported_methods)))
        if method == 'get_all':  # Special case
            self._assert_key('plural')
            extra_args = list(chain((str(a) for a in args), (str(k) for k in kwargs.itervalues())))
            url = 'get_{1}'.format(method, self.plural.lower())
            if len(extra_args) > 0:
                extra = '/{0}'.format('&'.join(extra_args))
                url += extra
            return url
        return '{0}_{1}'.format(method, self.__class__.__name__.lower())

    @classmethod
    def _compare_dicts(cls, dict1, dict2, strict_key_checking=False, excluded_keys=None, should_raise=True):
        """
        Compare two dicts and their values
        :param dict1: Dicts to base keys off
        :param dict2: Dicts to equals based on keys
        :param strict_key_checking: Check all keys
        :param excluded_keys: Exclude certain keys from checking
        :param should_raise: Choice between raising errors or returning the errors
        :return: List of errors when no errors is found or should_raise is True
        :rtype: list
        :raises: RuntimeError when not-matching keys are detected
        """
        if excluded_keys is None:
            excluded_keys = []
        d1_keys = set(dict1.iterkeys()) - set(excluded_keys)
        d2_keys = set(dict2.iterkeys()) - set(excluded_keys)
        errors = []
        if d1_keys != d2_keys:
            if strict_key_checking is True:
                errors.append('The dicts do not have the same keys!')
        intersect_keys = set(d1_keys).intersection(set(d2_keys))
        for key in intersect_keys:
            if dict1[key] != dict2[key]:
                if isinstance(dict1[key], dict) and isinstance(dict1[key], dict):
                    errors.extend(cls._compare_dicts(dict1[key], dict2[key],
                                                     strict_key_checking=strict_key_checking,
                                                     should_raise=False))
                else:
                    errors.append('Keys \'{0}\' are different'.format(key))
        if should_raise is True and len(errors) > 0:
            raise RuntimeError('Dicts are not equal: {0}'.format('\n -'.join(errors)))
        return errors


class Serializable(object):
    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


class TestRailObject(TestRailBase, Serializable):

    # Keys on which tracking should not be done
    _EXCLUDED_KEYS_TRACKING = ['_change_tracker', '_client', '_data_api', '_data_original', 'id', '_loaded', '_loading']
    # Mapping of parameters - type - required or not
    # @Todo base full property/doc generation on this variable (might need a rename then though) as the current code makes a bit repetitive
    _VERIFY_PARAMS = {}

    def __init__(self, id=None, client=None, load=True,*args, **kwargs):
        """
        Initialize a testrail object
        :param id: Identifier of the object
        :param client: api client pointer
        :param load: Auto load the object when an ID is specified
        """
        super(TestRailObject, self).__init__()
        self.id = id
        self._client = client

        # Keep track of api data when loading the object
        self._data_api = {}

        self._loaded = False
        self._loading = False

        if self.id is not None and load is True:
            self.load()

    def _assert_key(self, keyname):
        error = RuntimeError('Unable to fetch the object without the identifier.')
        if hasattr(self, keyname):
            if getattr(self, keyname) is None:
                raise error
            return
        raise error

    def has_changed(self):
        """
        Has this object changed
        :return: True when changed, False when not
        :rtype bool
        """
        # Experimental
        # return self._change_tracker.changed
        # Old
        excluded_keys = self._EXCLUDED_KEYS_TRACKING[:]
        excluded_keys.remove('id')
        if self._loaded is True:
            # Compare API data
            data_to_compare = self._data_api
        else:
            # Compare to an empty object (the excluded keys will filter out the object-bound stuff)
            data_to_compare = self.__class__().__dict__
        return len(self._compare_dicts(self.__dict__, data_to_compare, excluded_keys=excluded_keys, should_raise=False)) > 0

    def delete(self):
        """
        Deletes the given object
        :return: None
        :rtype: NoneType
        """
        self._assert_key('id')
        response = self._client.send_post('{0}/{1}'.format(self._generate_url('delete'), self.id), {})
        # Clear current instance
        new_obj = self.__class__(client=self._client)
        for key, value in new_obj.__dict__.items():
            if key in ['_change_tracker', '_client', '_data_original']:
                continue
            self.__dict__[key] = copy.deepcopy(value)

    def load(self):
        """
        Loads the given object
        :return: None
        :rtype: NoneType
        """
        self._assert_key('id')
        self._loading = True
        data = self._client.send_get('{0}/{1}'.format(self._generate_url('get'), self.id))
        self._data_api = data
        self._set_attributes(data)
        self._loaded = True
        self._loading = False

    def _set_attributes(self, kwargs):
        """
        Sets a number of attributes on the model
        :param kwargs: Dict of attributes to add
        :return: None
        :rtype: NoneType
        """
        for key, value in kwargs.iteritems():
            if hasattr(self, key):
                setattr(self, key, value)

    # Hooks for update
    def _get_data_update(self):
        """
        Return data to update the update
        Defaults to returning all data from the create
        :return: Returns the data to update the object on the backend
        :rtype: dict
        """
        return self._get_data_create()

    def _validate_data_update(self, data):
        """
        Validates the data to update
        Defaults to the same validation as the add
        :param data: Data to update
        :return: None
        """
        return self._validate_data_create(data)

    def _update(self):
        """
        Update the given object on the API
        :return: None
        :rtype: NoneType
        """
        self._assert_key('id')
        data = self._get_data_update()
        self._validate_data_update(data)
        return self._client.send_post('{0}/{1}'.format(self._generate_url('update'), self.id), data)

    # Hooks for add
    def _get_data_create(self):
        """
        Returns all data required for adding
        The data it returns is based on the _VERIFY_PARAMS
        :return: Data required to add the object
        :rtype: dict
        """
        return dict((key, getattr(self, key)) for key in self._VERIFY_PARAMS.iterkeys())

    def _validate_data_create(self, data):
        """
        Validates the passed in data given.
        Defaults to checking the keys given in _VERIFY_PARAMS
        :return:
        """
        self._client.verify_params(data, self._VERIFY_PARAMS)

    def _get_url_add(self):
        """
        Returns the URL to post for registering the object to the backend
        :return:
        """
        return self._generate_url('add')

    def _add(self):
        """
        Adds a new object on the backend
        :return: None
        :rtype: NoneType
        """
        data = self._get_data_create()
        self._validate_data_create(data)
        response = self._client.send_post(self._get_url_add(), data)
        self._data_api = response
        self._set_attributes(response)
        self._loaded = True
        self._loading = False

    def save(self):
        """
        Saves the current object on the backend
        :return: None
        :rtype: NoneType
        """
        if self.has_changed() is False:
            return
        if self._loaded is True:
            return self._update()
        else:
            return self._add()
