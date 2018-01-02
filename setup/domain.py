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
from ..helpers.backend import BackendHelper
from ..helpers.ci_constants import CIConstants
from ..helpers.domain import DomainHelper
from ..helpers.storagerouter import StoragerouterHelper
from ..validate.decorators import required_backend


class DomainSetup(CIConstants):

    LOGGER = Logger("setup-ci_domain_setup")

    def __init__(self):
        pass

    @classmethod
    def add_domain(cls, domain_name):
        """
        Add a new (recovery) domain to the cluster

        :param domain_name: name of a new domain to add
        :type domain_name: str
        :return:
        """
        # check if domain already exists
        if not DomainHelper.get_domain_by_name(domain_name):
            data = {"name": domain_name}
            cls.api.post(
                api='/domains/',
                data=data
            )

            if not DomainHelper.get_domain_by_name(domain_name):
                error_msg = "Failed to add domain `{0}`".format(domain_name)
                DomainSetup.LOGGER.error(error_msg)
                raise RuntimeError(error_msg)
            else:
                DomainSetup.LOGGER.info("Successfully added domain `{0}`".format(domain_name))
                return
        else:
            return

    @classmethod
    def link_domains_to_storagerouter(cls, domain_details, storagerouter_ip):
        """
        Link a existing domain(s) and/or recovery (domains) to a storagerouter
        :param domain_details: domain details of a storagerouter
            example: {"domain_guids":["Gravelines"],"recovery_domain_guids":["Roubaix", "Strasbourg"]}
        :type domain_details: dict
        :param storagerouter_ip: ip address of a storage router
        :type storagerouter_ip: str
        :return:
        """

        domain_guids = []
        recovery_domain_guids = []
        # translate domain names to domain guids
        for domain_name in domain_details['domain_guids']:
            domain_guids.append(DomainHelper.get_domainguid_by_name(domain_name))

        # translate recovery domain names to recovery domain guids
        for recovery_domain_name in domain_details['recovery_domain_guids']:
            recovery_domain_guids.append(DomainHelper.get_domainguid_by_name(recovery_domain_name))

        data = {"domain_guids": domain_guids,
                "recovery_domain_guids": recovery_domain_guids}

        storagerouter_guid = StoragerouterHelper.get_storagerouter_by_ip(storagerouter_ip).guid
        cls.api.post(
            api='/storagerouters/{0}/set_domains/'.format(storagerouter_guid),
            data=data
        )

        storagerouter = StoragerouterHelper.get_storagerouter_by_guid(storagerouter_guid=storagerouter_guid)
        if len(set(domain_guids) - set(storagerouter.regular_domains)) != 0 or \
           len(set(recovery_domain_guids) - set(storagerouter.recovery_domains)) != 0:
            error_msg = "Failed to link (recovery) domain(s) to storagerouter `{0}`".format(storagerouter_guid)
            DomainSetup.LOGGER.error(error_msg)
            raise RuntimeError(error_msg)
        else:
            DomainSetup.LOGGER.info("Successfully linked domain (recovery) domain(s) to storagerouter `{0}`"
                                    .format(storagerouter_guid))
            return

    @classmethod
    @required_backend
    def link_domains_to_backend(cls, domain_details, albabackend_name):
        """
        Link a existing domain(s) and/or recovery (domains) to a storagerouter

        :param domain_details: domain details of a storagerouter
            example: {"domain_guids":["Gravelines","Strasbourg"]}
        :type domain_details: dict
        :param albabackend_name: name of a existing alba backend
        :type albabackend_name: str
        """

        albabackend_guid = BackendHelper.get_backend_guid_by_name(albabackend_name)
        domain_guids = []

        # translate domain names to domain guids
        for domain_name in domain_details['domain_guids']:
            domain_guids.append(DomainHelper.get_domainguid_by_name(domain_name))

        data = {"domain_guids": domain_guids}
        cls.api.post(
            api='/backends/{0}/set_domains/'.format(albabackend_guid),
            data=data
        )

        backend = BackendHelper.get_backend_by_name(albabackend_name)
        if len(set(domain_guids) - set(backend.regular_domains)) != 0:
            error_msg = "Failed to link domain(s) to albabackend `{0}`".format(albabackend_name)
            DomainSetup.LOGGER.error(error_msg)
            raise RuntimeError(error_msg)
        else:
            DomainSetup.LOGGER.info("Successfully linked domain domain(s) to albabackend `{0}`"
                                    .format(albabackend_name))
            return
