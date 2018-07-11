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

from ovs.dal.hybrids.service import Service
from ovs.extensions.generic.sshclient import SSHClient
from ovs.extensions.services.servicefactory import ServiceFactory
from ovs.log.log_handler import LogHandler
from ..helpers.ci_constants import CIConstants


class ServiceHelper(CIConstants):
    """
    ServiceHelper class
    """

    LOGGER = LogHandler.get(source="setup", name="ci_service_setup")
    SERVICE_MANAGER = ServiceFactory.get_manager()

    @staticmethod
    def get_service(guid):
        """
        Fetch Service object by service guid
        :param guid: guid of the service
        :return: a Service object
        """
        return Service(guid)

    @staticmethod
    def restart_service(guid, storagerouter):
        """
        Restart a service based on the guid located on storagerouter
        :param guid: guid of the service
        :param storagerouter: storagerouter where the service is running
        :type storagerouter: StorageRouter
        :return:
        """
        client = SSHClient(storagerouter, username='root')
        service = ServiceHelper.get_service(guid)
        return ServiceHelper.SERVICE_MANAGER.restart_service(service.name, client=client)
