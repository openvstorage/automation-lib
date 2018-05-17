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
Project module
"""
from ..testrailobject import TestRailObject


class Result(TestRailObject):

    _VERIFY_PARAMS = {'status_id': (int, None),
                      'comment': (str, None, False),
                      'elapsed': (str, None, False),
                      'version': (str, None),
                      'defects': (str, None),
                      'assignedto_id': (int, None, False)}

    def __init__(self, id=None, test_id=None, status_id=None, comment=None, version=None, elapsed=None, defects=None, assignedto_id=None, client=None, *args, **kwargs):
        """
        Testrail Result
        :param id: id of the result
        :type id: int
        :param test_id: The id of the test the result should be added to
        :type test_id: int
        :param status_id: The id of test status: 1 passed, 2 blocked, 3 untested, 4 retest, 5 failed
        :type status_id: int
        :param comment: The comment/description of the test result
        :type comment: str
        :param version: The version or build you tested against
        :type version: str
        :param elapsed: The time it took to execute the test e.g. 30s or 1m 45s
        :type elapsed: str
        :param defects: A comma-separated list of defects to link to the test result
        :type defects: str
        :param assignedto_id: The id of a user the test should be assigned to
        :type assignedto_id: int
        """

        self.comment = comment
        self.version = version
        self.elapsed = elapsed
        self.defects = defects

        # Relation
        self.test_id = test_id
        self.status_id = status_id
        self.assignedto_id = assignedto_id

        super(Result, self).__init__(id=id, client=client, *args, **kwargs)

    def _get_url_add(self):
        return '{0}/{1}'.format(super(Result, self)._get_url_add(), self.test_id)

    def _validate_data_update(self, data):
        verify_params = dict(item for item in self._VERIFY_PARAMS.iteritems() if item[0] != 'test_id')
        return self._client.verify_params(data, verify_params)
