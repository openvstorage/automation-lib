# Copyright (C) 2016 iNuron NV
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
import json
from ci.api_lib.helpers.api import OVSClient


class CIConstants(object):
    """
    Collection of multiple constants and constant related instances
    """

    CONFIG_LOC = "/opt/OpenvStorage/ci/config/setup.json"
    TEST_SCENARIO_LOC = "/opt/OpenvStorage/ci/scenarios/"
    TESTRAIL_LOC = "/opt/OpenvStorage/ci/config/testrail.json"

    with open(CONFIG_LOC, 'r') as JSON_CONFIG:
        SETUP_CFG = json.load(JSON_CONFIG)

    HYPERVISOR_INFO = SETUP_CFG['ci'].get('hypervisor')
    DOMAIN_INFO = SETUP_CFG['setup']['domains']
    BACKEND_INFO = SETUP_CFG['setup']['backends']
    STORAGEROUTER_INFO = SETUP_CFG['setup']['storagerouters']

    class classproperty(property):
        def __get__(self, cls, owner):
            return classmethod(self.fget).__get__(None, owner)()

    @classproperty
    def api(cls):
        return OVSClient(cls.SETUP_CFG['ci']['grid_ip'],
                         cls.SETUP_CFG['ci']['user']['api']['username'],
                         cls.SETUP_CFG['ci']['user']['api']['password'])
