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
from ..helpers.vdisk import VDiskHelper
from ..validate.decorators import required_vtemplate


class VDiskRemover(CIConstants):

    LOGGER = Logger("remove-ci_vdisk_remover")
    REMOVE_SNAPSHOT_TIMEOUT = 60
    REMOVE_VTEMPLATE_TIMEOUT = 60
    REMOVE_VDISK_TIMEOUT = 5 * 60

    def __init__(self):
        pass

    @classmethod
    def remove_vdisks_with_structure(cls, vdisks, timeout=REMOVE_VDISK_TIMEOUT):
        """
        Remove many vdisks at once. Will keep the parent structure in mind
        :param vdisks: list of vdisks
        :param timeout: seconds to elapse before raising a timeout error (for each volume)
        :return: 
        """
        removed_guids = []
        for vdisk in vdisks:
            if vdisk.guid in removed_guids:
                continue
            if len(vdisk.child_vdisks_guids) > 0:
                for vdisk_child_guid in vdisk.child_vdisks_guids:
                    VDiskRemover.remove_vdisk(vdisk_child_guid)
                    removed_guids.append(vdisk_child_guid)
            VDiskRemover.remove_vdisk(vdisk.guid, timeout)
            removed_guids.append(vdisk.guid)

    @classmethod
    def remove_snapshot(cls, snapshot_guid, vdisk_name, vpool_name, timeout=REMOVE_SNAPSHOT_TIMEOUT):
        """
        Remove a existing snapshot from a existing vdisk
        :param vdisk_name: location of a vdisk on a vpool
                           (e.g. /mnt/vpool/test.raw = test.raw, /mnt/vpool/volumes/test.raw = volumes/test.raw )
        :type vdisk_name: str
        :param snapshot_guid: unique guid of a snapshot
        :type snapshot_guid: str
        :param timeout: time to wait for the task to complete
        :type timeout: int
        :param vpool_name: name of a existing vpool
        :type vpool_name: str
        :return: if success
        :rtype: bool
        """
        vdisk_guid = VDiskHelper.get_vdisk_by_name(vdisk_name, vpool_name).guid

        data = {"snapshot_id": snapshot_guid}
        task_guid = cls.api.post(
            api='/vdisks/{0}/remove_snapshot/'.format(vdisk_guid),
            data=data
        )
        task_result = cls.api.wait_for_task(task_id=task_guid, timeout=timeout)

        if not task_result[0]:
            error_msg = "Deleting snapshot `{0}` for vdisk `{1}` has failed".format(snapshot_guid, vdisk_name)
            VDiskRemover.LOGGER.error(error_msg)
            raise RuntimeError(error_msg)
        else:
            VDiskRemover.LOGGER.info("Deleting snapshot `{0}` for vdisk `{1}` should have succeeded"
                                     .format(snapshot_guid, vdisk_name))
            return True

    @classmethod
    def remove_vdisk(cls, vdisk_guid, timeout=REMOVE_VDISK_TIMEOUT):
        """
        Remove a vdisk from a vPool
        :param vdisk_guid: guid of a existing vdisk
        :type vdisk_guid: str
        :param timeout: time to wait for the task to complete
        :type timeout: int
        :return: if success
        :rtype: bool
        """
        task_guid = cls.api.post(api='vdisks/{0}/delete'.format(vdisk_guid))
        task_result = cls.api.wait_for_task(task_id=task_guid, timeout=timeout)
        if not task_result[0]:
            error_msg = "Deleting vDisk `{0}` has failed".format(vdisk_guid)
            VDiskRemover.LOGGER.error(error_msg)
            raise RuntimeError(error_msg)
        else:
            VDiskRemover.LOGGER.info("Deleting vDisk `{0}` should have succeeded".format(vdisk_guid))
            return True

    @classmethod
    def remove_vdisk_by_name(cls, vdisk_name, vpool_name, timeout=REMOVE_VDISK_TIMEOUT):
        """
        Remove a vdisk from a vPool
        :param vdisk_name: name of a existing vdisk (e.g. test.raw)
        :type vdisk_name: str
        :param vpool_name: name of a existing vpool
        :type vpool_name: str
        :return: if success
        :rtype: bool
        """
        vdisk_guid = VDiskHelper.get_vdisk_by_name(vdisk_name, vpool_name).guid
        return VDiskRemover.remove_vdisk(vdisk_guid, timeout)

    @classmethod
    @required_vtemplate
    def remove_vtemplate_by_name(cls, vdisk_name, vpool_name, timeout=REMOVE_VTEMPLATE_TIMEOUT):
        """
        Remove a vTemplate from a cluster
        :param vdisk_name: name of a existing vdisk (e.g. test.raw)
        :type vdisk_name: str
        :param vpool_name: name of a existing vpool
        :type vpool_name: str
        :param timeout: time to wait for the task to complete
        :type timeout: int
        :return: if success
        :rtype: bool
        """
        vdisk_guid = VDiskHelper.get_vdisk_by_name(vdisk_name, vpool_name).guid
        task_guid = cls.api.post(
            api='/vdisks/{0}/delete_vtemplate/'.format(vdisk_guid)
        )
        task_result = cls.api.wait_for_task(task_id=task_guid, timeout=timeout)

        if not task_result[0]:
            error_msg = "Deleting vTemplate `{0}` has failed".format(vdisk_name)
            VDiskRemover.LOGGER.error(error_msg)
            raise RuntimeError(error_msg)
        else:
            VDiskRemover.LOGGER.info("Deleting vTemplate `{0}` should have succeeded".format(vdisk_name))
            return True
