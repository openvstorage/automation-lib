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
from ..testrailobject import TestRailObject


class Priority(TestRailObject):

    _VERIFY_PARAMS = {'name': (str, None),
                      'shot_name': (str, None),
                      'priority': (int, None)}

    def __init__(self, id=None, name=None, short_name=None, priority=None, client=None, *args, **kwargs):
        """
        Testrail Priority
        :param id: Id of the priority
        :type id: int
        :param name: The name of the priority
        :type name: str
        :param short_name: The short name of the priority
        :type short_name: str
        :param priority: Determines the priority
        :type priority: int
        """

        self.name = name
        self.short_name = short_name
        self.priority = priority

        # Status is a bit special. It has no single-get API. Data can only be loaded through the list
        super(Priority, self).__init__(id=id, client=client, load=False, *args, **kwargs)

    def save(self):
        """
        Saves the current object on the backend
        :return: None
        :rtype: NoneType
        """
        raise NotImplemented('Statuses cannot be created. Only listed')
