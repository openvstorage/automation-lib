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
from ovs.extensions.generic.logger import Logger
from ovs_extensions.generic.toolbox import ExtensionsToolbox

from ..helpers.storagedriver import StoragedriverHelper
from ..helpers.vpool import VPoolHelper


class StoragedriverSetup(object):
    LOGGER = Logger('setup-ci_storagedriver_setup')

    # These will be all possible settings for the StorageDriver. Messing them up is their own responsibility (they should not bypass the API by default!!)
    STORAGEDRIVER_PARAMS = {"volume_manager": (dict, None, False),
                            "backend_connection_manager": (dict, None, False)}

    @staticmethod
    def change_config(vpool_name, vpool_details, storagerouter_ip, *args, **kwargs):

        # Settings volumedriver
        storagedriver_config = vpool_details.get('storagedriver')
        if storagedriver_config is not None:
            ExtensionsToolbox.verify_required_params(StoragedriverSetup.STORAGEDRIVER_PARAMS, storagedriver_config)
            StoragedriverSetup.LOGGER.info('Updating volumedriver configuration of vPool `{0}` on storagerouter `{1}`.'.format(vpool_name, storagerouter_ip))
            vpool = VPoolHelper.get_vpool_by_name(vpool_name)
            storagedriver = [sd for sd in vpool.storagedrivers if sd.storagerouter.ip == storagerouter_ip][0]
            if not storagedriver:
                error_msg = 'Unable to find the storagedriver of vPool {0} on storagerouter {1}'.format(vpool_name, storagerouter_ip)
                raise RuntimeError(error_msg)
            StoragedriverHelper.change_config(storagedriver, storagedriver_config)
            vpool.invalidate_dynamics('configuration')
            StoragedriverSetup.LOGGER.info('Updating volumedriver config of vPool `{0}` should have succeeded on storagerouter `{1}`'.format(vpool_name, storagerouter_ip))
