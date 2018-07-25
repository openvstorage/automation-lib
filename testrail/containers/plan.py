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


class Plan(TestRailObject):

    _VERIFY_PARAMS = {'description': (str, None, False),
                      'name': (str, None),
                      'milestone_id': (int, None),
                      'entries': (list, None, False)}

    def __init__(self, id=None, name=None, description=None, project_id=None, milestone_id=None, entries=None, client=None, *args, **kwargs):
        """
        Testrail Plan
        :param id: id of the plan
        :type id: int
        :param name: The name of the plan
        :type name: str
        :param description: The description of the plan
        :type description: str
        :param project_id: The id of the project
        :type project_id: int
        :param milestone_id: The id of the milestone
        :type milestone_id: int
        :param entries: An array of objects describing the test runs of the plan
        :type entries: list
        """
        self.name = name
        self.description = description

        # Relation
        self.project_id = project_id
        self.milestone_id = milestone_id
        self.entries = entries

        super(Plan, self).__init__(id=id, client=client, *args, **kwargs)

    def _get_url_add(self):
        return '{0}/{1}'.format(super(Plan, self)._get_url_add(), self.project_id)

    def _validate_data_update(self, data):
        verify_params = dict(item for item in self._VERIFY_PARAMS.iteritems() if item[0] != 'project_id')
        return self._client.verify_params(data, verify_params)
