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
Case Module
"""
from ci.testrail.testrailobject import TestRailObject


class Case(TestRailObject):

    _VERIFY_PARAMS = {'section_id': (int, None),
                      'title': (str, None),
                      'template_id': (int, None, False),
                      'type_id': (int, None, False),
                      'priority_id': (int, None, False),
                      'estimate': (str, None, False),
                      'milestone_id': (int, None, False),
                      'refs': (str, None, False)}

    def __init__(self, id=None, section_id=None, title=None, template_id=None, type_id=None, priority_id=None, estimate=None,
                 milestone_id=None, refs=None, client=None, *args, **kwargs):
        """
        Testrail Case
        :param id: ID of the Section
        :type id: int
        :param section_id: The ID of the section the test case should be added to (required)
        :type section_id: int
        :param title: The title of the test case (required)
        :type title: str
        :param template_id: The ID of the template (field layout) (requires TestRail 5.2 or later)
        :type template_id: int
        :param type_id: The ID of the case type
        :type type_id: int
        :param priority_id: The ID of the case priority
        :type priority_id: int
        :param estimate: The estimate, e.g. "30s" or "1m 45s"
        :type estimate: str
        :param milestone_id: The ID of the milestone to link to the test case
        :type milestone_id: int
        :param refs: A comma-separated list of references/requirements
        :type refs: str
        """
        self.title = title
        self.estimate = estimate
        self.refs = refs

        # Relation
        self.section_id = section_id
        self.milestone_id = milestone_id
        self.priority_id = priority_id
        self.type_id = type_id
        self.template_id = template_id

        super(Case, self).__init__(id=id, client=client, *args, **kwargs)

    def _get_url_add(self):
        return '{0}/{1}'.format(super(Case, self)._get_url_add(), self.section_id)
