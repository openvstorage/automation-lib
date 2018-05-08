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
ProjectList module
"""
from ci.testrail.testraillist import TestRailList
from ci.testrail.containers.section import Section


class SectionList(TestRailList):
    def __init__(self, project_id, suite_id, client, *args, **kwargs):
        """
        Initializes a SuitesList
        :param project_id: ID of the Project to list sections for
        :type project_id: int
        :param suite_id: ID of the Suite to list sections for
        :type suite_id: int
        """
        super(SectionList, self).__init__(client=client, object_type=Section, plural='sections', *args, **kwargs)
        self.load_url = self._generate_url(project_id, 'suite_id={0}'.format(suite_id))

    def get_section_by_name(self, section_name):
        for section in self.load():
            if section.name == section_name:
                return section

        raise LookupError('Section `{0}` not found.'.format(section_name))
