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
Project module
"""

from ci.testrail.testrailobject import TestRailObject


class Project(TestRailObject):
    _VERIFY_PARAMS = {'name': (str, None),
                      'announcement': (str, None, False),
                      'show_announcement': (bool, None, False),
                      'is_completed': (bool, None, False)}

    def __init__(self, id=None, name=None, announcement=None, show_announcement=None, suite_mode=None, is_completed=None, client=None, *args, **kwargs):
        """
        Testrail project
        :param id: id of the project
        :type id: int
        :param name: The name of the project
        :type name: str
        :param announcement: The description of the project
        :type announcement: str
        :param show_announcement: True if the announcement should be displayed on the project's overview page and false otherwise
        :type show_announcement: bool
        :param is_completed: Specifies whether a project is considered completed or not
        :type is_completed: bool
        :param suite_mode: The suite mode of the project (1 for single suite mode, 2 for single suite + baselines, 3 for multiple suites) (added with TestRail 4.0)
        :type suite_mode: int
        """
        self.name = name
        self.announcement = announcement
        self.show_announcement = show_announcement
        self.suite_mode = suite_mode
        self.is_completed = is_completed

        super(Project, self).__init__(id=id, client=client, *args, **kwargs)

