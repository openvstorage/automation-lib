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
from ..containers.casetype import CaseType
from ..testraillist import TestRailList


class CaseTypeList(TestRailList):
    def __init__(self, client, *args, **kwargs):
        """
        Initializes a TestList
        :param run_id: ID of the Run to list tests for
        :type run_id: int
        """
        super(CaseTypeList, self).__init__(client=client, object_type=CaseType, plural='case_types', *args, **kwargs)

    def get_casetype_by_name(self, casetype_name):
        for casetype in self.load():
            if casetype.name.lower() == casetype_name.lower():
                return casetype

        raise LookupError('CaseType `{0}` not found.'.format(casetype_name))
