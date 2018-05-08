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


class Test(TestRailObject):

    _VERIFY_PARAMS = {'run_id': (int, None),
                      'title': (str, None)}

    def __init__(self, id=None, run_id=None, title=None, client=None, *args, **kwargs):
        """
        Testrail Test
        :param id: Id of the test
        :type id: int
        :param run_id: The id of the test run
        :type run_id: int
        :param title: The title of test
        :type title: str
        """

        self.title = title

        # Relation
        self.run_id = run_id

        super(Test, self).__init__(id=id, client=client, *args, **kwargs)

    def save(self):
        """
        Saves the current object on the backend
        :return: None
        :rtype: NoneType
        """
        raise NotImplemented('Tests cannot be created. Only listed')
