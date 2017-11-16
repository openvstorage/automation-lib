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
from ci.scenario_helpers.ci_constants import CIConstants
from ovs.extensions.generic.logger import Logger
from ..helpers.albanode import AlbaNodeHelper
from ..helpers.backend import BackendHelper
from ..validate.decorators import required_backend, required_preset


class BackendRemover(CIConstants):

    LOGGER = Logger("remove-ci_backend_remover")
    REMOVE_ASD_TIMEOUT = 60
    REMOVE_DISK_TIMEOUT = 60
    REMOVE_BACKEND_TIMEOUT = 60
    REMOVE_PRESET_TIMEOUT = 60
    UNLINK_BACKEND_TIMEOUT = 60

    def __init__(self):
        pass

    @classmethod
    def remove_claimed_disk(cls):
        pass

    @classmethod
    def remove_asds(cls, albabackend_name, target, disks):
        """
        Remove all asds from a backend

        :param target: target to add asds too
        :type target: str
        :param disks: dict with diskname as key and amount of osds as value
        :type disks: dict
        :param albabackend_name: Name of the AlbaBackend to configure
        :type albabackend_name: str
        :return: preset_name
        :rtype: str
        """

        albabackend_guid = BackendHelper.get_alba_backend_guid_by_name(albabackend_name)
        # target is a node
        node_mapping = AlbaNodeHelper._map_alba_nodes()

        local_stack = BackendHelper.get_backend_local_stack(albabackend_name=albabackend_name)
        for disk, amount_of_osds in disks.iteritems():
            disk_object = AlbaNodeHelper.get_disk_by_ip(ip=target, diskname=disk)
            # Get the name of the disk out of the path, only expecting one with ata-
            disk_path = BackendHelper.get_local_stack_alias(disk_object)
            for alba_node_id, alba_node_guid in node_mapping.iteritems():
                # Check if the alba_node_id has the disk
                if disk_path in local_stack['local_stack'][alba_node_id]:
                    # Remove asds
                    for asd_id, asd_info in local_stack['local_stack'][alba_node_id][disk_path]['osds'].iteritems():
                        BackendRemover.LOGGER.info('Removing asd {0} for disk {1}'.format(asd_id, disk_path))
                        asd_safety = BackendHelper.get_asd_safety(albabackend_guid=albabackend_guid, asd_id=asd_id)
                        BackendRemover._remove_asd(alba_node_guid=alba_node_guid, asd_id=asd_id, asd_safety=asd_safety)

        # Restarting iteration to avoid too many local stack calls:
        local_stack = BackendHelper.get_backend_local_stack(albabackend_name=albabackend_name)
        for disk, amount_of_osds in disks.iteritems():
            disk_object = AlbaNodeHelper.get_disk_by_ip(ip=target, diskname=disk)
            # Get the name of the disk out of the path, only expecting one with ata-
            disk_path = BackendHelper.get_local_stack_alias(disk_object)
            for alba_node_id, alba_node_guid in node_mapping.iteritems():
                # Check if the alba_node_id has the disk
                if disk_path in local_stack['local_stack'][alba_node_id]:
                    # Initialize disk:
                    BackendRemover.LOGGER.info('Removing {0}.'.format(disk_path))
                    BackendRemover._remove_disk(alba_node_guid=alba_node_guid, diskname=disk_path)

    @classmethod
    def _remove_asd(cls, alba_node_guid, asd_id, asd_safety, timeout=REMOVE_ASD_TIMEOUT):
        """
        Remove a asd from a backend

        :param alba_node_guid: guid of the alba node
        :type alba_node_guid: str
        :param asd_id: id of the asd
        :type asd_id: str
        :param asd_safety:
        :type asd_safety: dict
        :param timeout: max. time to wait for a task to complete
        :type timeout: int
        :return:
        """

        data = {
            'asd_id': asd_id,
            'safety': asd_safety
        }
        task_guid = cls.api.post(
            api='/alba/nodes/{0}/reset_asd/'.format(alba_node_guid),
            data=data
        )
        result = cls.api.wait_for_task(task_id=task_guid, timeout=timeout)
        if result[0] is False:
            error_msg = "Removal of ASD '{0}; failed with {1}".format(asd_id, result[1])
            BackendRemover.LOGGER.error(error_msg)
            raise RuntimeError(error_msg)
        return result[0]

    @classmethod
    def _remove_disk(cls, alba_node_guid, diskname, timeout=REMOVE_DISK_TIMEOUT):
        """
        Removes a an initiliazed disk from the model

        :param alba_node_guid: guid of the alba node
        :type alba_node_guid: str
        :param diskname: name of the disk
        :type diskname: str
        :param timeout: max. time to wait for the task to complete
        :type timeout: int
        :return:
        """
        data = {
            'disk': diskname,
        }
        task_guid = cls.api.post(
            api='/alba/nodes/{0}/remove_disk/'.format(alba_node_guid),
            data=data
        )
        result = cls.api.wait_for_task(task_id=task_guid, timeout=timeout)
        if result[0] is False:
            errormsg = "Removal of ASD '{0}' failed with '{1}'".format(diskname, result[1])
            BackendRemover.LOGGER.error(errormsg)
            raise RuntimeError(errormsg)
        return result[0]

    @classmethod
    @required_backend
    def remove_backend(cls, albabackend_name, timeout=REMOVE_BACKEND_TIMEOUT):
        """
        Removes a alba backend from the ovs cluster

        :param albabackend_name: the name of a existing alba backend
        :type albabackend_name: str
        :param timeout: max. time to wait for a task to complete
        :type timeout: int
        :return: task was succesfull or not
        :rtype: bool
        """

        alba_backend_guid = BackendHelper.get_alba_backend_guid_by_name(albabackend_name)
        task_guid = cls.api.delete(api='/alba/backends/{0}'.format(alba_backend_guid))

        result = cls.api.wait_for_task(task_id=task_guid, timeout=timeout)
        if result[0] is False:
            errormsg = "Removal of backend '{0}' failed with '{1}'".format(albabackend_name, result[1])
            BackendRemover.LOGGER.error(errormsg)
            raise RuntimeError(errormsg)
        return result[0]

    @classmethod
    @required_preset
    @required_backend
    def remove_preset(cls, preset_name, albabackend_name, timeout=REMOVE_PRESET_TIMEOUT):
        """
        Removes a alba backend from the ovs cluster

        :param preset_name: the name of a existing preset on existing backend
        :type preset_name: str
        :param albabackend_name: name of the albabackend
        :type albabackend_name: str
        :param timeout: max. time to wait for a task to complete
        :type timeout: int
        :return: task was succesfull or not
        :rtype: bool
        """

        alba_backend_guid = BackendHelper.get_alba_backend_guid_by_name(albabackend_name)
        data = {"name": preset_name}
        task_guid = cls.api.post(api='/alba/backends/{0}/delete_preset'.format(alba_backend_guid), data=data)

        result = cls.api.wait_for_task(task_id=task_guid, timeout=timeout)

        if result[0] is False:
            errormsg = "Removal of preset '{0}' for backend '{1}' failed with '{2}'".format(preset_name, albabackend_name, result[1])
            BackendRemover.LOGGER.error(errormsg)
            raise RuntimeError(errormsg)
        return result[0]


    @classmethod
    #@required_backend
    def unlink_backend(cls, globalbackend_name, albabackend_name, timeout=UNLINK_BACKEND_TIMEOUT):
        """
        Link a LOCAL backend to a GLOBAL backend

        :param globalbackend_name: name of a GLOBAL alba backend
        :type globalbackend_name: str
        :param albabackend_name: name of a backend to unlink
        :type albabackend_name: str
        :param timeout: timeout counter in seconds
        :type timeout: int
        :return:
        """
        data = {
            "linked_guid": BackendHelper.get_alba_backend_guid_by_name(albabackend_name)
        }

        task_guid = cls.api.post(
            api='/alba/backends/{0}/unlink_alba_backends'
                .format(BackendHelper.get_alba_backend_guid_by_name(globalbackend_name)),
            data=data
        )

        task_result = cls.api.wait_for_task(task_id=task_guid, timeout=timeout)
        if not task_result[0]:
            error_msg = "Unlinking backend `{0}` from global backend `{1}` has failed with error '{2}'".format(
                albabackend_name, globalbackend_name, task_result[1])
            BackendRemover.LOGGER.error(error_msg)
            raise RuntimeError(error_msg)
        else:
            BackendRemover.LOGGER.info("Unlinking backend `{0}` from global backend `{1}` should have succeeded"
                                     .format(albabackend_name, globalbackend_name))
            return task_result[0]


    @classmethod
    #@required_backend
    def unlink_backend(cls, globalbackend_name, albabackend_name, timeout=UNLINK_BACKEND_TIMEOUT):
        """
        Link a LOCAL backend to a GLOBAL backend

        :param globalbackend_name: name of a GLOBAL alba backend
        :type globalbackend_name: str
        :param albabackend_name: name of a backend to unlink
        :type albabackend_name: str
        :param timeout: timeout counter in seconds
        :type timeout: int
        :return:
        """
        data = {
            "linked_guid": BackendHelper.get_alba_backend_guid_by_name(albabackend_name)
        }

        task_guid = cls.api.post(
            api='/alba/backends/{0}/unlink_alba_backends'
                .format(BackendHelper.get_alba_backend_guid_by_name(globalbackend_name)),
            data=data
        )

        task_result = cls.api.wait_for_task(task_id=task_guid, timeout=timeout)
        if not task_result[0]:
            error_msg = "Unlinking backend `{0}` from global backend `{1}` has failed with error '{2}'".format(
                albabackend_name, globalbackend_name, task_result[1])
            BackendRemover.LOGGER.error(error_msg)
            raise RuntimeError(error_msg)
        else:
            BackendRemover.LOGGER.info("Unlinking backend `{0}` from global backend `{1}` should have succeeded"
                                     .format(albabackend_name, globalbackend_name))
            return task_result[0]


    @classmethod
    #@required_backend
    def unlink_backend(cls, globalbackend_name, albabackend_name, timeout=UNLINK_BACKEND_TIMEOUT):
        """
        Link a LOCAL backend to a GLOBAL backend

        :param globalbackend_name: name of a GLOBAL alba backend
        :type globalbackend_name: str
        :param albabackend_name: name of a backend to unlink
        :type albabackend_name: str
        :param timeout: timeout counter in seconds
        :type timeout: int
        :return:
        """
        data = {
            "linked_guid": BackendHelper.get_alba_backend_guid_by_name(albabackend_name)
        }

        task_guid = cls.api.post(
            api='/alba/backends/{0}/unlink_alba_backends'
                .format(BackendHelper.get_alba_backend_guid_by_name(globalbackend_name)),
            data=data
        )

        task_result = cls.api.wait_for_task(task_id=task_guid, timeout=timeout)
        if not task_result[0]:
            error_msg = "Unlinking backend `{0}` from global backend `{1}` has failed with error '{2}'".format(
                albabackend_name, globalbackend_name, task_result[1])
            BackendRemover.LOGGER.error(error_msg)
            raise RuntimeError(error_msg)
        else:
            BackendRemover.LOGGER.info("Unlinking backend `{0}` from global backend `{1}` should have succeeded"
                                     .format(albabackend_name, globalbackend_name))
            return task_result[0]


    @classmethod
    #@required_backend
    def unlink_backend(cls, globalbackend_name, albabackend_name, timeout=UNLINK_BACKEND_TIMEOUT):
        """
        Link a LOCAL backend to a GLOBAL backend

        :param globalbackend_name: name of a GLOBAL alba backend
        :type globalbackend_name: str
        :param albabackend_name: name of a backend to unlink
        :type albabackend_name: str
        :param timeout: timeout counter in seconds
        :type timeout: int
        :return:
        """
        data = {
            "linked_guid": BackendHelper.get_alba_backend_guid_by_name(albabackend_name)
        }

        task_guid = cls.api.post(
            api='/alba/backends/{0}/unlink_alba_backends'
                .format(BackendHelper.get_alba_backend_guid_by_name(globalbackend_name)),
            data=data
        )

        task_result = cls.api.wait_for_task(task_id=task_guid, timeout=timeout)
        if not task_result[0]:
            error_msg = "Unlinking backend `{0}` from global backend `{1}` has failed with error '{2}'".format(
                albabackend_name, globalbackend_name, task_result[1])
            BackendRemover.LOGGER.error(error_msg)
            raise RuntimeError(error_msg)
        else:
            BackendRemover.LOGGER.info("Unlinking backend `{0}` from global backend `{1}` should have succeeded"
                                     .format(albabackend_name, globalbackend_name))
            return task_result[0]
