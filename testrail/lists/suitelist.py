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
from ..containers.suite import Suite


class SuiteList(TestRailList):
    def __init__(self, project_id, client, *args, **kwargs):
        """
        Initializes a SuitesList
        :param project_id: ID of the Project to list suites for
        :type project_id: int
        """
        super(SuiteList, self).__init__(client=client, object_type=Suite, plural='suites', *args, **kwargs)
        self.load_url = self._generate_url(project_id)

    def get_suite_by_name(self, suite_name):
        for suite in self.load():
            if suite.name == suite_name:
                return suite

        raise LookupError('Suite `{0}` not found.'.format(suite_name))
