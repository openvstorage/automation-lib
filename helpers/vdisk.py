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

from ovs.dal.hybrids.vdisk import VDisk
from ovs.dal.lists.vdisklist import VDiskList
from ovs.dal.lists.vpoollist import VPoolList
from ovs.extensions.generic.logger import Logger
from ..helpers.ci_constants import CIConstants
from ..helpers.exceptions import VPoolNotFoundError, VDiskNotFoundError


class VDiskHelper(CIConstants):
    """
    vDiskHelper class
    """

    GET_CONFIG_PARAMS_TIMEOUT = 60
    LOGGER = Logger("helpers-ci_vdisk_setup")

    class DtlStatus(object):
        """
        DTL ENUM class for a vDisk
        """

        SYNC = "ok_sync"
        STANDALONE = "ok_standalone"
        CHECKUP = "checkup_required"
        DEGRADED = "degraded"
        DISABLED = "disabled"

    def __init__(self):
        pass

    @staticmethod
    def get_vdisk_by_name(vdisk_name, vpool_name):
        """
        Fetch disk partitions by disk guid

        :param vdisk_name: location of a vdisk on a vpool
                           (e.g. /mnt/vpool/test.raw = test.raw, /mnt/vpool/volumes/test.raw = volumes/test.raw )
        :type vdisk_name: str
        :param vpool_name: name of a existing vpool
        :type vpool_name: str
        :return: a vdisk object
        :rtype: ovs.dal.hybrids.vdisk
        """

        vpool = VPoolList.get_vpool_by_name(vpool_name)
        if vpool:
            if not vdisk_name.startswith("/"):
                vdisk_name = "/{0}".format(vdisk_name)
            if not vdisk_name.endswith('.raw'):
                vdisk_name = '{0}.raw'.format(vdisk_name)
            vdisk = VDiskList.get_by_devicename_and_vpool(vdisk_name, vpool)
            if vdisk:
                return vdisk
            else:
                raise VDiskNotFoundError("VDisk with name `{0}` not found on vPool `{1}`!".format(vdisk_name, vpool_name))
        else:
            raise VPoolNotFoundError("vPool with name `{0}` cannot be found!".format(vpool_name))

    @staticmethod
    def get_vdisk_by_guid(vdisk_guid):
        """
        Fetch vdisk object by vdisk guid

        :param vdisk_guid: guid of a existing vdisk
        :type vdisk_guid: str
        :return: a vdisk object
        :rtype: ovs.dal.hybrids.vdisk.VDISK
        """

        return VDisk(vdisk_guid)

    @staticmethod
    def get_snapshot_by_guid(snapshot_guid, vdisk_name, vpool_name):
        """
        Fetch vdisk object by vdisk guid

        :param snapshot_guid: guid of a existing snapshot
        :type snapshot_guid: str
        :param vdisk_name: name of a existing vdisk
        :type vdisk_name: str
        :param vpool_name: name of a existing vpool
        :type vpool_name: str
        :return: a vdisk object
        :rtype: ovs.dal.hybrids.vdisk
        """

        vdisk = VDiskHelper.get_vdisk_by_name(vdisk_name=vdisk_name, vpool_name=vpool_name)
        try:
            return next((snapshot for snapshot in vdisk.snapshots if snapshot['guid'] == snapshot_guid))
        except StopIteration:
            raise RuntimeError("Did not find snapshot with guid `{0}` on vdisk `{1}` on vpool `{2}`"
                               .format(snapshot_guid, vdisk_name, vpool_name))


    @classmethod
    def get_config_params(cls, vdisk_name, vpool_name, timeout=GET_CONFIG_PARAMS_TIMEOUT, *args, **kwargs):
        """
        Fetch the config parameters of a vDisk

        :param vdisk_name: location of a vdisk on a vpool
                           (e.g. /mnt/vpool/test.raw = test.raw, /mnt/vpool/volumes/test.raw = volumes/test.raw )
        :type vdisk_name: str
        :param vpool_name: name of a existing vpool
        :type vpool_name: str
        :param timeout: time to wait for the task to complete
        :type timeout: int
        :return: a dict with config parameters, e.g.
        {
           'dtl_mode':u'a_sync',
           'dtl_target':[
              u'24f94196-13e8-43c1-afa7-4c44fa8b11ea'
           ],
           'pagecache_ratio':1.0,
           'sco_size':4,
           'write_buffer':512
        }
        :rtype: dict
        """

        vdisk = VDiskHelper.get_vdisk_by_name(vdisk_name=vdisk_name, vpool_name=vpool_name)
        task_guid = cls.api.get(api='/vdisks/{0}/get_config_params'.format(vdisk.guid))
        task_result = cls.api.wait_for_task(task_id=task_guid, timeout=timeout)

        if not task_result[0]:
            error_msg = "Setting config vDisk `{0}` has failed with error {1}".format(vdisk_name, task_result[1])
            VDiskHelper.LOGGER.error(error_msg)
            raise RuntimeError(error_msg)
        else:
            VDiskHelper.LOGGER.info("Setting config vDisk `{0}` should have succeeded".format(vdisk_name))
            return task_result[1]


    @classmethod
    def scrub_vdisk(cls, vdisk_guid, timeout=15 * 60, wait=True, *args, **kwargs):
        """
        Scrub a specific vdisk
        :param vdisk_guid: guid of the vdisk to scrub
        :type vdisk_guid: str
        :param timeout: time to wait for the task to complete
        :type timeout: int
        :param wait: wait for task to finish or not
        :type wait: bool
        :return: 
        """
        task_guid = cls.api.post(api='/vdisks/{0}/scrub/'.format(vdisk_guid), data={})
        if wait is True:
            task_result = cls.api.wait_for_task(task_id=task_guid, timeout=timeout)
            if not task_result[0]:
                error_msg = "Scrubbing vDisk `{0}` has failed with error {1}".format(vdisk_guid, task_result[1])
                VDiskHelper.LOGGER.error(error_msg)
                raise RuntimeError(error_msg)
            else:
                VDiskHelper.LOGGER.info("Scrubbing vDisk `{0}` should have succeeded".format(vdisk_guid))
                return task_result[1]
        else:
            return task_guid
