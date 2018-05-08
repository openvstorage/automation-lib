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


class Milestone(TestRailObject):

    _VERIFY_PARAMS = {'description': (str, None, False),
                      'name': (str, None),
                      'due_on': (int, None, False),
                      'parent_id': (int, None, False),
                      'start_on': (int, None, False)}

    def __init__(self, id=None, name=None, description=None, project_id=None, parent_id=None, due_on=None, start_on=None, client=None, *args, **kwargs):
        """
        Testrail Milestone
        :param id: id of the milestone
        :type id: int
        :param name: The name of the milestone
        :type name: str
        :param description: The description of the milestone
        :type description: str
        :param project_id: The ID of the project
        :type project_id: int
        :param parent_id: The ID of the parent milestone
        :type parent_id: int
        :param due_on: The due date of the milestone (as Unix timestamp)
        :type due_on: int
        :param start_on: The scheduled start date of the milestone (as Unix timestamp)
        :type start_on: int
        """
        self.name = name
        self.description = description
        self.due_on = due_on
        self.start_on = start_on

        # Relation
        self.project_id = project_id
        self.parent_id = parent_id

        super(Milestone, self).__init__(id=id, client=client, *args, **kwargs)

    def _get_url_add(self):
        return '{0}/{1}'.format(super(Milestone, self)._get_url_add(), self.project_id)

    def _validate_data_update(self, data):
        verify_params = dict(item for item in self._VERIFY_PARAMS.iteritems() if item[0] != 'project_id')
        return self._client.verify_params(data, verify_params)
