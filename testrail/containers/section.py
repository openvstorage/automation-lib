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
Section Module
"""
from ..testrailobject import TestRailObject


class Section(TestRailObject):

    _VERIFY_PARAMS = {'description': (str, None, False),
                      'suite_id': (int, None, False),
                      'parent_id': (int, None, False),
                      'project_id': (int, None),
                      'name': (str, None)}

    def __init__(self, id=None, project_id=None, description=None, suite_id=None, parent_id=None, name=None, client=None, *args, **kwargs):
        """
        Testrail Suite
        :param id: ID of the Section
        :type id: int
        :param project_id: The ID of the project
        :param description: The description of the section (added with TestRail 4.0)
        :type description: str
        :param suite_id: The ID of the test suite (ignored if the project is operating in single suite mode, required otherwise)
        :type suite_id: int
        :param parent_id: The ID of the parent section (to build section hierarchies)
        :type parent_id: int
        :param name: The name of the Section (required)
        :type name: str
        """
        self.name = name
        self.description = description

        # Relation
        self.project_id = project_id
        self.suite_id = suite_id
        self.parent_id = parent_id

        super(Section, self).__init__(id=id, client=client, *args, **kwargs)

    def _get_url_add(self):
        return '{0}/{1}'.format(super(Section, self)._get_url_add(), self.project_id)

    def _validate_data_update(self, data):
        verify_params = dict(item for item in self._VERIFY_PARAMS.iteritems() if item[0] in ['name', 'description'])
        return self._client.verify_params(data, verify_params)
