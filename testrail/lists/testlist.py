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
from ..containers.test import Test


class TestList(TestRailList):
    def __init__(self, run_id, client, *args, **kwargs):
        """
        Initializes a TestList
        :param run_id: ID of the Run to list tests for
        :type run_id: int
        """
        super(TestList, self).__init__(client=client, object_type=Test, plural='tests', *args, **kwargs)
        self.load_url = self._generate_url(run_id)
