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
from ci.testrail.containers.project import Project


class ProjectList(TestRailList):
    def __init__(self, client, *args, **kwargs):
        super(ProjectList, self).__init__(client=client, object_type=Project, plural='projects', *args, **kwargs)

    def get_project_by_name(self, project_name):
        for project in self.load():
            if project.name == project_name:
                return project

        raise LookupError('Project `{0}` not found.'.format(project_name))
