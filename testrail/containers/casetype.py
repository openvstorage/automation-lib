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
Case Module
"""
from ..testrailobject import TestRailObject


class CaseType(TestRailObject):

    _VERIFY_PARAMS = {'is_default': (bool, None),
                      'name': (str, None)}

    def __init__(self, id=None, is_default=None, name=None, client=None, *args, **kwargs):
        """
        Testrail Case
        :param id: ID of the CaseType
        :type id: int
        :param is_default: The ID of the section the test case should be added to (required)
        :type is_default: bool
        :param name: The name of the case type
        :type name: str
        """
        self.is_default = is_default
        self.name = name

        super(CaseType, self).__init__(id=id, client=client, load=False, *args, **kwargs)

    def save(self):
        """
        Saves the current object on the backend
        :return: None
        :rtype: NoneType
        """
        raise NotImplemented('CaseTypes cannot be created. Only listed')

