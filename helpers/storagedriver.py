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

from ovs.dal.hybrids.storagedriver import StorageDriver
from ovs.dal.lists.storagedriverlist import StorageDriverList
from ovs.extensions.generic.configuration import Configuration
from ovs.extensions.generic.logger import Logger
from ovs.extensions.generic.sshclient import SSHClient
from ovs.extensions.services.servicefactory import ServiceFactory


class StoragedriverHelper(object):

    """
    StoragedriverHelper class
    """
    LOGGER = Logger("helpers-ci_storagedriver_helper")

    def __init__(self):
        pass

    @staticmethod
    def get_storagedrivers_by_storagerouterguid(storagerouter_guid):
        """
        Get the storagedriver connected to a storagerouter by its guid

        :param storagerouter_guid: guid of a storagerouter
        :type storagerouter_guid: str
        :return: collection of available storagedrivers on the storagerouter
        :rtype: list
        """

        return StorageDriverList.get_storagedrivers_by_storagerouter(storagerouter_guid)

    @staticmethod
    def get_storagedriver_by_guid(storagedriver_guid):
        """
        Fetches the storagedriver with its guid

        :param storagedriver_guid: guid of the storagedriver
        :type storagedriver_guid: str
        :return: The storagedriver DAL object
        :rtype: ovs.dal.hybrids.storagedriver.STORAGEDRIVER
        """
        return StorageDriver(storagedriver_guid)

    @staticmethod
    def get_storagedriver_by_id(storagedriver_id):
        """
        Fetches the storagedriver with its storagedriver_id

        :param storagedriver_id: id of the storagedriver
        :type storagedriver_id: str
        :return: The storagedriver DAL object
        :rtype: ovs.dal.hybrids.storagedriver.STORAGEDRIVER
        """
        return StorageDriverList.get_by_storagedriver_id(storagedriver_id)

    @staticmethod
    def get_storagedrivers():
        """
        Fetches all storagedrivers
        :return: list of all storagedrivers
        :rtype: (ovs.dal.hybrids.storagedriver.STORAGEDRIVER)
        """
        return StorageDriverList.get_storagedrivers()

    @staticmethod
    def change_config(storagedriver, config):
        """
        Change the config of the volumedriver and reload the config.
        Restart will be triggered if no vDisk are running on the volumedriver.
        :param storagedriver: StorageDriver object
        :type storagedriver: StorageDriver
        :param config: Volumedriver config
        :type config: dict
        :return:
        """
        service_manager = ServiceFactory.get_manager()
        config_key = '/ovs/vpools/{0}/hosts/{1}/config'.format(storagedriver.vpool.guid, storagedriver.name)
        current_config = Configuration.get(config_key)

        if 'volume_manager' in config:
            volume_manager = current_config['volume_manager']
            for key, value in config['volume_manager'].iteritems():
                volume_manager[key] = value

        if 'backend_connection_manager' in config:
            backend_connection_manager = current_config['backend_connection_manager']
            for key, value in config['backend_connection_manager'].iteritems():
                if key == 'proxy':
                    for current_config_key, current_config_value in backend_connection_manager.iteritems():
                        if current_config_key.isdigit():
                            for proxy_key, proxy_config in config['backend_connection_manager']['proxy'].iteritems():
                                current_config_value[proxy_key] = proxy_config

                else:
                    backend_connection_manager[key] = value
        StoragedriverHelper.LOGGER.info("New config: {0}".format(json.dumps(current_config, indent=4)))
        Configuration.set(config_key, json.dumps(current_config, indent=4), raw=True)
        client = SSHClient(storagedriver.storagerouter, 'root')
        service_name = 'ovs-volumedriver_{0}'.format(storagedriver.vpool.name)

        if len(storagedriver.vdisks_guids) == 0:
            StoragedriverHelper.LOGGER.info("Restarting service: {0}".format(service_name))
            service_manager.restart_service(service_name, client)
        else:
            StoragedriverHelper.LOGGER.info("Not restarting service: {0}, amount of vdisks: {1}".format(service_name, len(storagedriver.vdisks_guids)))
