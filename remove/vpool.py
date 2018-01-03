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
from ..helpers.ci_constants import CIConstants
from ..helpers.storagerouter import StoragerouterHelper
from ..helpers.vpool import VPoolHelper


class VPoolRemover(CIConstants):

    LOGGER = Logger("remove-ci_vpool_remover")
    REMOVE_VPOOL_TIMEOUT = 500

    @classmethod
    def remove_vpool(cls, vpool_name, storagerouter_ip, timeout=REMOVE_VPOOL_TIMEOUT, *args, **kwargs):
        """
        Removes a existing vpool from a storagerouter
        :param vpool_name: the name of a existing vpool
        :type vpool_name: str
        :param storagerouter_ip: the ip address of a existing storagerouter
        :type storagerouter_ip: str
        :param timeout: max. time to wait for a task to complete
        :type timeout: int
        :return: None
        :rtype: NoneType
        """
        vpool_guid = VPoolHelper.get_vpool_by_name(vpool_name).guid
        storagerouter_guid = StoragerouterHelper.get_storagerouter_by_ip(storagerouter_ip).guid
        data = {"storagerouter_guid": storagerouter_guid}
        task_guid = cls.api.post(api='/vpools/{0}/shrink_vpool/'.format(vpool_guid), data=data)
        task_result = cls.api.wait_for_task(task_id=task_guid, timeout=timeout)

        if not task_result[0]:
            error_msg = "Deleting vPool `{0}` on storagerouter `{1}` has failed with error {2}".format(vpool_name, storagerouter_ip, task_result[1])
            VPoolRemover.LOGGER.error(error_msg)
            raise RuntimeError(error_msg)
        else:
            VPoolRemover.LOGGER.info("Deleting vPool `{0}` on storagerouter `{1}` should have succeeded".format(vpool_name, storagerouter_ip))
