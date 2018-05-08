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
from ci.testrail.containers.milestone import Milestone


class MilestoneList(TestRailList):
    def __init__(self, project_id, client, *args, **kwargs):
        """
        Initializes a MilestoneLilst
        :param project_id: ID of the Project to list milstones for
        :type project_id: int
        """
        super(MilestoneList, self).__init__(client=client, object_type=Milestone, plural='milestones', *args, **kwargs)
        self.load_url = self._generate_url(project_id)

    def get_milestone_by_name(self, milestone_name):
        for milestone in self.load():
            if milestone.name == milestone_name:
                return milestone

        raise LookupError('Milestone `{0}` not found.'.format(milestone_name))
