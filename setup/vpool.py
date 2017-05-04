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
from ovs.log.log_handler import LogHandler
from ..helpers.backend import BackendHelper
from ..helpers.storagerouter import StoragerouterHelper
from ..helpers.storagedriver import StoragedriverHelper
from ..validate.decorators import required_roles, required_backend, check_vpool


class VPoolSetup(object):

    LOGGER = LogHandler.get(source='setup', name='ci_vpool_setup')
    ADD_VPOOL_TIMEOUT = 500
    REQUIRED_VPOOL_ROLES = ['DB', 'WRITE']

    def __init__(self):
        pass

    @staticmethod
    @check_vpool
    @required_backend
    @required_roles(REQUIRED_VPOOL_ROLES, 'LOCAL')
    def add_vpool(vpool_name, vpool_details, api, storagerouter_ip, albabackend_name, proxy_amount=2, timeout=ADD_VPOOL_TIMEOUT):
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
        :param albabackend_name: name(s) of backend(s). Used to validate the backend
        :type albabackend_name: str or list
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

        # Optional param - required for unstable at the moment
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
        else:
            call_parameters['block_cache_on_read'] = False
            call_parameters['block_cache_on_write'] = False

        print api_data
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
            return storagerouter_ip, '/mnt/{0}'.format(vpool_name)

    @staticmethod
    def execute_scrubbing():
        """
        Execute scrubbing on the cluster

        :return:
        """

        return GenericController.execute_scrub()
