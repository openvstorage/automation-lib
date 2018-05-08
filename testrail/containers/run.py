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
from ci.testrail.testrailobject import TestRailObject


class Run(TestRailObject):

    _VERIFY_PARAMS = {'description': (str, None, False),
                      'name': (str, None),
                      'suite_id': (int, None, False),
                      'milestone_id': (int, None),
                      'assignedto_on': (int, None, False),
                      'include_all': (bool, None, False),
                      'case_ids': (list, None, False)}

    def __init__(self, id=None, name=None, description=None, suite_id=None, project_id=None, milestone_id=None, assignedto_on=None, include_all=None, case_ids=None, client=None, *args, **kwargs):
        """
        Testrail Run
        :param id: id of the run
        :type id: int
        :param name: The name of the run
        :type name: str
        :param description: The description of the run
        :type description: str
        :param suite_id: The id of the test suite
        :type suite_id: int
        :param project_id: The id of the project
        :type project_id: int
        :param milestone_id: The id of the milestone
        :type milestone_id: int
        :param assignedto_on: The id of the user the test run should be assigned to
        :type assignedto_on: int
        :param include_all: True for including all test cases of the test suite and false for a custom case selection
        :type include_all: bool
        :param case_ids: An array of case ID of the custom case selection
        :type case_ids: list
        """
        self.name = name
        self.description = description
        self.assignedto_on = assignedto_on
        self.include_all = include_all

        # Relation
        self.project_id = project_id
        self.suite_id = suite_id
        self.milestone_id = milestone_id
        self.case_ids = case_ids

        super(Run, self).__init__(id=id, client=client, *args, **kwargs)

    def _get_url_add(self):
        return '{0}/{1}'.format(super(Run, self)._get_url_add(), self.project_id)

    def _validate_data_update(self, data):
        verify_params = dict(item for item in self._VERIFY_PARAMS.iteritems() if item[0] != 'project_id')
        return self._client.verify_params(data, verify_params)
