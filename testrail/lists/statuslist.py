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


class StatusList(TestRailList):
    def __init__(self, client, *args, **kwargs):
        """
        Initializes a StatusList
        """
        # Status is a bit special. It has no single-get API. Data can only be loaded through the list
        super(StatusList, self).__init__(client=client, object_type=Status, plural='statuses', *args, **kwargs)

    def get_status_by_name(self, status_name):
        for status in self.load():
            if status.name == status_name:
                return status

        raise LookupError('Status `{0}` not found.'.format(status_name))
