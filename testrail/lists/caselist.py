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
from ..testraillist import TestRailList
from ..containers.case import Case


class CaseList(TestRailList):
    def __init__(self, project_id, suite_id, section_id, client, *args, **kwargs):
        """
        Initializes a CaseList
        :param project_id: ID of the Project to list cases for
        :type project_id: int
        :param suite_id: ID of the Suite to list cases for
        :type suite_id: int
        :param section_id: ID of the Section to list cases for
        :type section_id: int
        """
        super(CaseList, self).__init__(client=client, object_type=Case, plural='cases', *args, **kwargs)
        self.load_url = self._generate_url(project_id, 'suite_id={0}'.format(suite_id), 'section_id={0}'.format(section_id))

    def get_case_by_name(self, case_name):
        for case in self.load():
            if case.title == case_name:
                return case

        raise LookupError('Case `{0}` not found.'.format(case_name))
