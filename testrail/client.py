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
API client module.
- APIClient: An API client. The client has been changed to work with testrail auth keys
- APIError: Exception thrown by the API client
"""
import base64
import json
import re
import sys
import urllib2


class APIError(Exception):
    pass


class APIClient(object):
    def __init__(self, base_url, username=None, password=None, key=None):
        assert (username and password) or key, "Credentials are needed for testrail connection, specify either user/password or basic auth key."
        self.user = username
        self.password = password
        self.key = key
        if not base_url.endswith('/'):
            base_url += '/'
        if not base_url.startswith('http://'):
            base_url = 'http://{0}'.format(base_url)
        self._url = base_url + 'index.php?/api/v2/'

    def send_get(self, uri):
        """
        Issues a GET request (read) against the API and returns the result
        :param uri: The API method to call including parameters (e.g. get_case/1)
        :return: result of the get
        :rtype: dict
        """
        return self._send_request('GET', uri, None)

    def send_post(self, uri, data):
        """
        Issues a POST request (write) against the API and returns the result
        :param uri: The API method to call including parameters (e.g. add_case/1)
        :type uri: str
        :param data: The data to submit as part of the request (as Python dict, strings must be UTF-8 encoded)
        :type data: dict
        :return: result of the post
        :rtype: dict
        """
        return self._send_request('POST', uri, data)

    def _send_request(self, method, uri, data):
        """
        Sends a request to the uri
        :param method: request method (eg GET)
        :param uri: The API method to call including parameters (e.g. add_case/1)
        :param data:
        :return: Result of the call
        :rtype: dict
        """
        url = self._url + uri
        request = urllib2.Request(url)
        if method == 'POST':
            request.add_data(json.dumps(data))
        if self.key is not None:
            auth = self.key
        else:
            auth = base64.b64encode('{0}:{1}'.format(self.user, self.password))
        request.add_header('Authorization', 'Basic {0}'.format(auth))
        request.add_header('Content-Type', 'application/json')
        error = None
        try:
            response = urllib2.urlopen(request).read()
        except urllib2.HTTPError as error:
            response = error.read()
        if response:
            result = json.loads(response)
        else:
            result = {}
        if error is not None:
            if result and 'error' in result:
                error_message = '"' + result['error'] + '"'
            else:
                error_message = 'No additional error message received'
            raise APIError('TestRail API returned HTTP {0} ({1})'.format(error.code, error_message))
        return result

    @staticmethod
    def _check_type(value, required_type):
        """
        Validates whether a certain value is of a given type. Some types are treated as special
        case:
          - A 'str' type accepts 'str', 'unicode' and 'basestring'
          - A 'float' type accepts 'float', 'int'
          - A list instance acts like an enum
        """
        given_type = type(value)
        if required_type is str:
            correct = isinstance(value, basestring) or value is None
            allowed_types = ['str', 'unicode', 'basestring']
        elif required_type is float:
            correct = isinstance(value, float) or isinstance(value, int) or value is None
            allowed_types = ['float', 'int']
        elif required_type is int or required_type is long:
            correct = isinstance(value, int) or isinstance(value, long) or value is None
            allowed_types = ['int', 'long']
        elif isinstance(required_type, list):
            # We're in an enum scenario. Field_type isn't a real type, but a list containing
            # all possible enum values. Here as well, we need to do some str/unicode/basestring
            # checking.
            if isinstance(required_type[0], basestring):
                value = str(value)
            correct = value in required_type
            allowed_types = required_type
            given_type = value
        else:
            correct = isinstance(value, required_type) or value is None
            allowed_types = [required_type.__name__]
        return correct, allowed_types, given_type

    @classmethod
    def verify_params(cls, given_params, param_mapping):
        """
        Verifies parameters based on a given mapping
        :param given_params: given params
        :type given_params: dict
        :param param_mapping: param mapping
        :type param_mapping: dict
        :return: None
        :rtype: NoneType
        """
        # @TODO replace with toolbox verify params after testing
        if not isinstance(given_params, dict) or not isinstance(param_mapping, dict):
            raise ValueError('Arguments are incorrect. Both arguments need to be of type {0}'.format(dict))
        error_messages = []
        compiled_regex_type = type(re.compile('some_regex'))
        for required_key, key_info in param_mapping.iteritems():
            expected_type = key_info[0]
            expected_value = key_info[1]
            optional = len(key_info) == 3 and key_info[2] is False

            if optional is True and (required_key not in given_params or given_params[required_key] in ('', None)):
                continue

            if required_key not in given_params:
                error_messages.append('Missing required param "{0}" in actual parameters'.format(required_key))
                continue

            mandatory_or_optional = 'Optional' if optional is True else 'Mandatory'
            actual_value = given_params[required_key]
            if cls._check_type(actual_value, expected_type)[0] is False:
                error_messages.append(
                    '{0} param "{1}" is of type "{2}" but we expected type "{3}"'.format(mandatory_or_optional, required_key, type(actual_value), expected_type))
                continue
            if expected_value is None:
                continue

            if expected_type == list:
                if type(expected_value) == compiled_regex_type:  # List of strings which need to match regex
                    for item in actual_value:
                        if not re.match(expected_value, item):
                            error_messages.append(
                                '{0} param "{1}" has an item "{2}" which does not match regex "{3}"'.format(
                                    mandatory_or_optional, required_key, item, expected_value.pattern))
            elif expected_type == dict:
                cls.verify_params(expected_value, given_params[required_key])
            elif expected_type == int or expected_type == float:
                if isinstance(expected_value, list) and actual_value not in expected_value:
                    error_messages.append('{0} param "{1}" with value "{2}" should be 1 of the following: {3}'.format(mandatory_or_optional, required_key, actual_value, expected_value))
                if isinstance(expected_value, dict):
                    minimum = expected_value.get('min', sys.maxint * -1)
                    maximum = expected_value.get('max', sys.maxint)
                    if not minimum <= actual_value <= maximum:
                        error_messages.append('{0} param "{1}" with value "{2}" should be in range: {3} - {4}'.format(mandatory_or_optional, required_key, actual_value, minimum, maximum))
            else:
                if cls._check_type(expected_value, list)[0] is True and actual_value not in expected_value:
                    error_messages.append('{0} param "{1}" with value "{2}" should be 1 of the following: {3}'
                                          .format(mandatory_or_optional, required_key, actual_value, expected_value))
                elif cls._check_type(expected_value, compiled_regex_type)[0] is True and not re.match(expected_value, actual_value):
                    error_messages.append('{0} param "{1}" with value "{2}" does not match regex "{3}"'.format(mandatory_or_optional, required_key, actual_value, expected_value.pattern))
        if error_messages:
            raise RuntimeError('\n' + '\n'.join(error_messages))
