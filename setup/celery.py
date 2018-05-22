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

from ovs.extensions.generic.configuration import Configuration
from ovs.log.log_handler import LogHandler
from ovs.extensions.generic.sshclient import SSHClient
from ovs.extensions.services.servicefactory import ServiceFactory
from ..helpers.storagerouter import StoragerouterHelper


class CelerySetup(object):

    LOGGER = LogHandler.get(source="setup", name="ci_celery_setup")
    SCHEDULED_TASK_CFG = "/ovs/framework/scheduling/celery"

    def __init__(self):
        pass

    @staticmethod
    def override_scheduletasks(configuration):
        """
        Override the scheduled tasks crontab with your own confguration
        :param configuration: configuration to override scheduled tasks
        :type configuration: dict
        :return:
        """
        service_name = 'ovs-watcher-framework'
        Configuration.set(CelerySetup.SCHEDULED_TASK_CFG, configuration)
        fetched_cfg = Configuration.get(CelerySetup.SCHEDULED_TASK_CFG, configuration)
        if cmp(fetched_cfg, configuration) == 0:
            # restart ovs-watcher-framework on all nodes
            for sr_ip in StoragerouterHelper.get_storagerouter_ips():
                client = SSHClient(sr_ip, username='root')
                service_manager = ServiceFactory.get_manager()
                try:

                    service_manager.restart_service(service_name, client)
                except:
                    return False
            CelerySetup.LOGGER.info("Successfully restarted all `{0}` services!".format(service_name))
            return True
        else:
            CelerySetup.LOGGER.warning("`{0}` config is `{1}` but should be `{2}`".format(CelerySetup.SCHEDULED_TASK_CFG, fetched_cfg, configuration))
            return False
