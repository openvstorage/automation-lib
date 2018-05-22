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
from ovs.dal.hybrids.storagerouter import StorageRouter
from ovs.dal.lists.storagerouterlist import StorageRouterList
from ovs.log.log_handler import LogHandler
from ..helpers.ci_constants import CIConstants


class StoragerouterHelper(CIConstants):

    """
    StoragerouterHelper class
    """
    LOGGER = LogHandler.get(source="helpers", name="ci_storagerouter_helper")

    cache_timeout = 60
    disk_map_cache = {}

    def __init__(self):
        pass

    @staticmethod
    def get_storagerouter_by_guid(storagerouter_guid):
        """
        :param storagerouter_guid: guid of a storagerouter
        :type storagerouter_guid: str
        :return: storagerouter guid
        :rtype: ovs.dal.hybrids.storagerouter.StorageRouter
        """
        return StorageRouter(storagerouter_guid)

    @staticmethod
    def get_storagerouter_by_ip(storagerouter_ip):
        """
        :param storagerouter_ip: ip of a storagerouter
        :type storagerouter_ip: str
        :return: storagerouter
        :rtype: ovs.dal.hybrids.storagerouter.StorageRouter
        """
        return StorageRouterList.get_by_ip(storagerouter_ip)

    @staticmethod
    def get_storagerouter_ip(storagerouter_guid):
        """
        :param storagerouter_guid: guid of a storagerouter
        :type storagerouter_guid: str
        :return: storagerouter ip
        :rtype: str
        """
        return StorageRouter(storagerouter_guid).ip

    @staticmethod
    def get_disk_by_name(guid, diskname):
        """
        Fetch a disk by its guid and name

        :param guid: guid of a storagerouter
        :type guid: str
        :param diskname: shortname of a disk (e.g. sdb)
        :return: Disk Object
        :rtype: ovs.dal.hybrids.disk.disk
        """
        disks = StoragerouterHelper.get_storagerouter_by_guid(guid).disks
        for d in disks:
            if d.name == diskname:
                return d

    @staticmethod
    def get_storagerouter_ips():
         """
         Fetch all the ip addresses in this cluster

         :return: list with storagerouter ips
         :rtype: list
         """
         return [storagerouter.ip for storagerouter in StorageRouterList.get_storagerouters()]

    @staticmethod
    def get_storagerouters():
        """
        Fetch the storagerouters

        :return: list with storagerouters
        :rtype: list
        """
        return StorageRouterList.get_storagerouters()

    @classmethod
    def sync_disk_with_reality(cls, guid=None, ip=None, timeout=None, *args, **kwargs):
        """
        :param guid: guid of the storagerouter
        :type guid: str
        :param ip: ip of the storagerouter
        :type ip: str
        :param timeout: timeout time in seconds
        :type timeout: int
        """
        if guid is not None:
            if ip is not None:
                Logger.warning('Both storagerouter guid and ip passed, using guid for sync.')
            storagerouter_guid = guid
        elif ip is not None:
            storagerouter_guid = StoragerouterHelper.get_storagerouter_by_ip(ip).guid
        else:
            raise ValueError('No guid or ip passed.')
        task_id = cls.api.post(api='/storagerouters/{0}/rescan_disks/'.format(storagerouter_guid), data=None)
        return cls.api.wait_for_task(task_id=task_id, timeout=timeout)

    @classmethod
    def get_storagerouters_by_role(cls):
        """
        Gets storagerouters based on roles
        :return:
        """
        voldr_str_1 = None  # Will act as volumedriver node
        voldr_str_2 = None  # Will act as volumedriver node
        compute_str = None  # Will act as compute node
        if isinstance(cls.HYPERVISOR_INFO, dict):  # Hypervisor section is filled in -> VM environment
            nodes_info = {}
            for hv_ip, hv_info in cls.HYPERVISOR_INFO['vms'].iteritems():
                nodes_info[hv_ip] = hv_info
        elif cls.SETUP_CFG['ci'].get('nodes') is not None:  # Physical node section -> Physical environment
            nodes_info = cls.SETUP_CFG['ci']['nodes']
        else:
            raise RuntimeError('Unable to fetch node information. Either hypervisor section or node section is missing!')
        for node_ip, node_details in nodes_info.iteritems():
            if node_details['role'] == "VOLDRV":
                if voldr_str_1 is None:
                    voldr_str_1 = StoragerouterHelper.get_storagerouter_by_ip(node_ip)
                elif voldr_str_2 is None:
                    voldr_str_2 = StoragerouterHelper.get_storagerouter_by_ip(node_ip)
            elif node_details['role'] == "COMPUTE" and compute_str is None:
                compute_str = StoragerouterHelper.get_storagerouter_by_ip(node_ip)
        assert voldr_str_1 is not None and voldr_str_2 is not None and compute_str is not None,\
            'Could not fetch 2 storagedriver nodes and 1 compute node based on the setup.json config.'
        return voldr_str_1, voldr_str_2, compute_str
