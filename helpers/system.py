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
import time
from ovs.log.log_handler import LogHandler
from ovs.extensions.services.service import ServiceManager
from ovs.extensions.generic.sshclient import SSHClient
from ovs.extensions.generic.system import System


class SystemHelper(object):
    """
    BackendHelper class
    """
    LOGGER = LogHandler.get(source='helpers', name="ci_system")

    def __init__(self):
        pass

    @staticmethod
    def get_non_running_ovs_services(client):
        """
        get all non-running ovs services
        :param client: sshclient instance
        :return: list of non running ovs services
        :rtype: list
        """
        non_running_ovs_services = []
        for service in ServiceManager.list_services(client):
            if not service.startswith('ovs-'):
                continue
            if ServiceManager.get_service_status(service, client) != 'active':
                non_running_ovs_services.append(service)
        return non_running_ovs_services

    @staticmethod
    def get_local_storagerouter():
        """
        Fetches the details of a local storagerouter
        :return: a StorageRouter
        :rtype: ovs.dal.hybrids.storagerouter.StorageRouter
        """
        return System.get_my_storagerouter()

    @classmethod
    def get_ovs_version(cls, storagerouter=None):
        """
        Gets the installed ovs version
        :param storagerouter: Storagerouter to fetch info from
        :return: ovs version identifier. Either ee or ose
        :rtype: str
        """
        if storagerouter is None:
            storagerouter = cls.get_local_storagerouter()
        if storagerouter.features['alba']['edition'] == 'community':
            return 'ose'
        else:
            return 'ee'

    @staticmethod
    def idle_till_ovs_is_up(ip, username, password=None, connection_timeout=300, service_timeout=60, logger=LOGGER):
        """
        wait until a node is back up and all ovs related are running (or potentially stuck)
        :param ip: ip of the node
        :param username: username to login with
        :param password: password to login with
        :param connection_timeout: raise when not online after these seconds
        :param service_timeout: poll for x seconds when checking services
        :param logger: logging instance
        :raise RuntimeError: when the timeout has been reached
        :return: dict with services mapped by their state
        """
        # neutral_states = ['inactive', 'deactivating']
        failed_states = ['failed', 'error']
        active_states = ['active', 'reloading']
        activating_state = 'activating'
        start_time = time.time()
        client = None
        while client is None:
            delta = time.time() - start_time
            if delta > connection_timeout:
                raise RuntimeError('Idling has timed out after {0}s'.format(delta))
            try:
                client = SSHClient(ip, username=username, password=password)
            except:
                logger.debug('Could not establish a connection yet to {0} after {1}s'.format(ip, delta))
            time.sleep(1)
        ovs_services = [service for service in ServiceManager.list_services(client) if service.startswith('ovs-')]
        active_services = []
        failed_service = []
        activating_services = []
        # Initially class these services
        for service in ovs_services:
            logger.debug('Initially classifying {0}'.format(service))
            service_state = ServiceManager.get_service_status(service, client)
            logger.debug('Service {0} - State {1}'.format(service, service_state))
            if service_state in failed_states:
                failed_service.append(service)
            elif service_state in active_states:
                active_services.append(service)
            elif service_state == activating_state:
                activating_services.append(service)
            else:
                logger.error('Unable to process service state {0}'.format(service_state))
        start_time = time.time()
        while len(activating_services) > 0:
            if time.time() - start_time > service_timeout:
                break
            service = activating_services.pop()
            service_state = ServiceManager.get_service_status(service, client)
            if service_state in failed_states:
                failed_service.append(service)
            elif service_state in active_states:
                active_services.append(service)
            elif service_state == activating_state:
                activating_services.append(service)
        return {'active': active_services, 'failed': failed_service, 'activating': activating_services}
