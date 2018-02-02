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
from ovs.lib.generic import GenericController
from ovs.extensions.generic.logger import Logger
from ..helpers.backend import BackendHelper
from ..helpers.storagedriver import StoragedriverHelper
from ..helpers.storagerouter import StoragerouterHelper
from ..helpers.vpool import VPoolHelper
from ..validate.decorators import required_roles, check_vpool


class VPoolSetup(object):

    LOGGER = Logger('setup-ci_vpool_setup')
    ADD_VPOOL_TIMEOUT = 500
    REQUIRED_VPOOL_ROLES = ['DB', 'WRITE', 'DTL']

    def __init__(self):
        pass

    @staticmethod
    @check_vpool
    @required_roles(REQUIRED_VPOOL_ROLES, 'LOCAL')
    def add_vpool(vpool_name, vpool_details, api, storagerouter_ip, proxy_amount=2, timeout=ADD_VPOOL_TIMEOUT, *args, **kwargs):
        """
        Adds a VPool to a storagerouter

        :param vpool_name: name of the new vpool
        :type vpool_name: str
        :param vpool_details: dictionary with storagedriver settings
        :type vpool_details: dict
        :param timeout: specify a timeout
        :type timeout: int
        :param api: specify a valid api connection to the setup
        :type api: helpers.api.OVSClient
        :param storagerouter_ip: ip of the storagerouter to add the vpool too
        :type storagerouter_ip: str
        :param proxy_amount: amount of proxies for this vpool
        :type proxy_amount: int
        :return: (storagerouter_ip, vpool_mountpoint)
        :rtype: tuple
        """

        # Build ADD_VPOOL parameters
        call_parameters = {
            'vpool_name': vpool_name,
            'backend_info': {'alba_backend_guid': BackendHelper.get_albabackend_by_name(vpool_details['backend_name']).guid,
                             'preset': vpool_details['preset']},
            'connection_info': {'host': '', 'port': '', 'client_id': '', 'client_secret': ''},
            'storage_ip': vpool_details['storage_ip'],
            'storagerouter_ip': storagerouter_ip,
            'writecache_size': int(vpool_details['storagedriver']['global_write_buffer']),
            'fragment_cache_on_read': vpool_details['fragment_cache']['strategy']['cache_on_read'],
            'fragment_cache_on_write': vpool_details['fragment_cache']['strategy']['cache_on_write'],
            'config_params': {'dtl_mode': vpool_details['storagedriver']['dtl_mode'],
                              'sco_size': int(vpool_details['storagedriver']['sco_size']),
                              'cluster_size': int(vpool_details['storagedriver']['cluster_size']),
                              'write_buffer': int(vpool_details['storagedriver']['volume_write_buffer']),
                              'dtl_transport': vpool_details['storagedriver']['dtl_transport']},
            'parallelism': {'proxies': proxy_amount}
        }
        api_data = {'call_parameters': call_parameters}

        # Setting for mds_safety
        if vpool_details.get('mds_safety') is not None:
            call_parameters['mds_config_params'] = {'mds_safety': vpool_details['mds_safety']}

        # Setting possible alba accelerated alba
        if vpool_details['fragment_cache']['location'] == 'backend':
            call_parameters['backend_info_aa'] = {'alba_backend_guid': BackendHelper.get_albabackend_by_name(vpool_details['fragment_cache']['backend']['name']).guid,
                                                  'preset': vpool_details['fragment_cache']['backend']['preset']}
            call_parameters['connection_info_aa'] = {'host': '', 'port': '', 'client_id': '', 'client_secret': ''}
        elif vpool_details['fragment_cache']['location'] == 'disk':
            pass
        else:
            error_msg = 'Wrong `fragment_cache->location` in vPool configuration, it should be `disk` or `backend`'
            VPoolSetup.LOGGER.error(error_msg)
            raise RuntimeError(error_msg)

        # Optional param
        if vpool_details.get('block_cache') is not None:
            call_parameters['block_cache_on_read'] = vpool_details['block_cache']['strategy']['cache_on_read']
            call_parameters['block_cache_on_write'] = vpool_details['block_cache']['strategy']['cache_on_write']
            if vpool_details['block_cache']['location'] == 'backend':
                call_parameters['backend_info_bc'] = {'alba_backend_guid': BackendHelper.get_albabackend_by_name(vpool_details['block_cache']['backend']['name']).guid,
                                                      'preset': vpool_details['block_cache']['backend']['preset']}
                call_parameters['connection_info_bc'] = {'host': '', 'port': '', 'client_id': '', 'client_secret': ''}
            elif vpool_details['block_cache']['location'] == 'disk':  # Ignore disk
                pass
            else:
                # @ Todo has to be removed for development version
                error_msg = 'Wrong `block_cache->location` in vPool configuration, it should be `disk` or `backend`'
                VPoolSetup.LOGGER.error(error_msg)
                raise RuntimeError(error_msg)
        
        task_guid = api.post(
            api='/storagerouters/{0}/add_vpool/'.format(
                    StoragerouterHelper.get_storagerouter_guid_by_ip(storagerouter_ip)),
            data=api_data
        )
        task_result = api.wait_for_task(task_id=task_guid, timeout=timeout)
        if not task_result[0]:
            error_msg = 'vPool {0} has failed to create on storagerouter {1} because: {2}'.format(vpool_name, storagerouter_ip, task_result[1])
            VPoolSetup.LOGGER.error(error_msg)
            raise RuntimeError(error_msg)
        else:
            VPoolSetup.LOGGER.info('Creation of vPool `{0}` should have succeeded on storagerouter `{1}`'.format(vpool_name, storagerouter_ip))

        # Settings volumedriver
        storagedriver_config = {}
        if vpool_details.get('storagedriver').get('volume_manager') is not None:
            storagedriver_config['volume_manager'] = vpool_details['storagedriver']['volume_manager']
        if vpool_details.get('storagedriver').get('backend_connection_manager') is not None:
            storagedriver_config['backend_connection_manager'] = vpool_details['storagedriver']['backend_connection_manager']

        if storagedriver_config:
            VPoolSetup.LOGGER.info('Updating volumedriver configuration of vPool `{0}` on storagerouter `{1}`.'.format(vpool_name, storagerouter_ip))
            vpool = VPoolHelper.get_vpool_by_name(vpool_name)
            storagedriver = [sd for sd in vpool.storagedrivers if sd.storagerouter.ip == storagerouter_ip][0]
            if not storagedriver:
                error_msg = 'Unable to find the storagedriver of vPool {0} on storagerouter {1}'.format(vpool_name, storagerouter_ip)
                raise RuntimeError(error_msg)
            StoragedriverHelper.change_config(storagedriver, storagedriver_config)
            VPoolSetup.LOGGER.info('Updating volumedriver config of vPool `{0}` should have succeeded on storagerouter `{1}`'.format(vpool_name, storagerouter_ip))

        return storagerouter_ip, '/mnt/{0}'.format(vpool_name)

    @staticmethod
    def execute_scrubbing():
        """
        Execute scrubbing on the cluster

        :return:
        """

        return GenericController.execute_scrub()
