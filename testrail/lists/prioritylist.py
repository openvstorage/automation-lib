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
from ci.testrail.containers.status import Status


class PriorityList(TestRailList):
    def __init__(self, client, *args, **kwargs):
        """
        Initializes a StatusList
        """
        # Status is a bit special. It has no single-get API. Data can only be loaded through the list
        super(PriorityList, self).__init__(client=client, object_type=Status, plural='priorities', *args, **kwargs)

    def get_priority_by_name(self, priority_name):
        for priority in self.load():
            if priority_name in priority.name:
                return priority

        raise LookupError('Priority `{0}` not found.'.format(priority_name))
