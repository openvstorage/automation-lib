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
import os
import json
from ci.autotests import AutoTests
from ovs.dal.hybrids.albabackend import AlbaBackend
from ovs.dal.hybrids.diskpartition import DiskPartition
from ovs.extensions.storageserver.storagedriver import StorageDriverClient
from ovs.lib.helpers.toolbox import Toolbox


class SetupJsonGenerator(object):
    """
    This provides class provides code to automate construction of a setup.json file.
    Addition and removal of several components of the setup.json is provided
    """
    HYPERV_KVM = 'KVM'
    VPOOL_COUNTER = 1

    def __init__(self):
        self._json_dict = {}
        self._presets = []
        self._domains = []
        self._backends = []
        self._ips = []

    @property
    def config(self):
        """
        Property containing the currently modelled config dict
        :return: return the currently modelled config dict
        :rtype: dict
        """
        return self._json_dict

    def dump_json_to_file(self, path):
        """
        Write current setup dict to a json file in the provided path.
        :param path: path to dump json file to
        :type path: str
        """
        with open(path, 'w') as fp:
            json.dump(self.config, indent=4, sort_keys=True, fp=fp)

    def update_scenarios(self, scenarios=None):
        """
        Add scenarios to be scheduled in the setup.
        :param scenarios: scenarios to add to the 'scenarios' section of the setup.json.
                            If left blank, by default all scenarios will be scheduled.
        :type scenarios: list
        """
        if not isinstance(scenarios, list) and scenarios is not None:
            raise ValueError('Scenarios should be passed in a list format, not {}'.format(type(scenarios)))

        if scenarios is None:
            self.config['scenarios'] = ['ALL']
        else:
            for scenario in scenarios:
                if isinstance(scenario, str) and scenario not in AutoTests.list_tests():
                    raise ValueError('Scenario {0} is not a valid scenario path.'.format(scenario))

            self.config['scenarios'] = scenarios

    def update_ci(self, ci_params):
        """
        Set the ci constants of the setup file accordign to the passed parameters.
        :param passed_required_params: obligatory parameters for the setup file
        :type passed_required_params: dict
        :param passed_optional_params: optional parameters
        :type passed_optional_params: dict
        """
        params_layout = {'setup': (bool, None, True),
                         'grid_ip': (str, Toolbox.regex_ip, True),
                         'validation': (bool, None, False),
                         'cleanup': (bool, None, False),
                         'send_to_testrail': (bool, None, False),
                         'fail_on_failed_scenario': (bool, None, False),
                         'scenarios': (bool, None, False),
                         'scenario_retries': (int, {'min': 1}, False),
                         'version': (str, ['andes', 'unstable', 'fargo', 'develop'], False),
                         'config_manager': (str, 'arakoon', False)}

        all_params = {'validation': False,
                      'cleanup': False,
                      'send_to_testrail': True,
                      'fail_on_failed_scenario': True,
                      'scenarios': True,
                      'scenario_retries': 1,
                      'version': 'andes',
                      'config_manager': 'arakoon'}

        all_params.update(ci_params)
        Toolbox.verify_required_params(required_params=params_layout, actual_params=all_params, verify_keys=True)

        if os.system('ping -c 1 {}'.format(all_params['grid_ip'])) != 0:
            raise ValueError('No response from ip {0}'.format(all_params['grid_ip']))

        ci = {'setup': all_params['setup'],
              'cleanup': all_params['cleanup'],
              'send_to_testrail': all_params['send_to_testrail'],
              'fail_on_failed_scenario': all_params['fail_on_failed_scenario'],
              'version': all_params['version'],
              'scenarios': all_params['scenarios'],
              'local_hypervisor': {'type': SetupJsonGenerator.HYPERV_KVM,
                                   'user': 'root',
                                   'password': 'rooter'},
              'config_manager': all_params['config_manager'],
              'user': {'shell': {'username': 'root',
                                 'password': 'rooter'},
                       'api': {'username': 'admin',
                               'password': 'admin'}},
              'grid_ip': all_params['grid_ip']}
        self._json_dict['ci'] = ci

    def add_hypervisor(self, hypervisor_ip, hypervisor_type=HYPERV_KVM, username='root', password='rooter', virtual_machines=None):
        """
        Add hypervisor information to the model
        :param hypervisor_type:
        :param hypervisor_ip: ip of the hypervisor itself
        :type hypervisor_ip: str
        :param virtual_machines: dict containing the virtual machine ip with their name and according role
        :type virtual_machines: dict
                    example: {1.1.1.1: {'name': 'name1','role': 'VOLDRV'}}
        :param username: username to be used in the hypervisor setup
        :type username: str
        :param password: password to be used in the hypervisor setup
        :type password: str

        """
        if 'ci' not in self._json_dict:
            raise ValueError('CI constants have to be set before adding hypervisors')
        self._validate_ip(hypervisor_ip)

        if virtual_machines is None:
            vm_ip = self.config['ci']['grid_ip']
            name = 'ubuntu_node_'+str(vm_ip.split('.', 2)[-1]).strip()
            virtual_machines = {vm_ip: {'name': name, 'role': 'COMPUTE'}}

        if not isinstance(virtual_machines, dict):
            raise ValueError('Dict of virtual machines should contain entries like { ip: { `name`: `role`}}')
        for key, value in virtual_machines.iteritems():
            self._validate_ip(key)

        hypervisor_dict = {'type': hypervisor_type,
                           'user': username,
                           'password': password,
                           'ip': hypervisor_ip,
                           'vms': virtual_machines}

        self._ips.extend(virtual_machines.keys())
        if 'hypervisor' not in self.config['ci']:
            self.config['ci']['hypervisor'] = {}
        self.config['ci']['hypervisor'] = hypervisor_dict

    def remove_hypervisor(self, hypervisor_ip):
        """
        remove the hypervisor with the given ip, if present
        :param hypervisor_ip: ip address of the hypervisor to remove
        :type hypervisor_ip: str
        """
        if self.config['ci']['hypervisor']['ip'] == hypervisor_ip:
            self.config['ci'].pop('hypervisor')

    def add_domain(self, domain):
        """
        Add available domains to the model.
        :param domain: domainname to add
        :type domain: str
        """
        if not isinstance(domain, str):
            raise ValueError('domain is no string')
        self._domains.append(domain)
        if 'setup' not in self.config.keys():
            self.config['setup'] = {}
        if 'domains' not in self.config['setup'].keys():
            self.config['setup']['domains'] = []
        self.config['setup']['domains'].append(domain)

    def remove_domain(self, domain):
        """
        Remove a domain from the model
        :param domain: domain to be removed
        :type domain: str
        """
        try:
            self.config['setup']['domains'].remove(domain)
            if self.config['setup']['domains'] == []:
                self.config['setup'].pop('domains')
        except KeyError:
            pass

    def add_storagerouter(self, storagerouter_ip, hostname):
        """
        Add a storagerouter to the model given the provided ip and hostname.
        :param storagerouter_ip: ip address of the storage router
        :type storagerouter_ip: str
        :param hostname: hostname of the storagerouter
        :type hostname: str
        """
        self._validate_ip(storagerouter_ip)
        required_params = {'hostname': (str, None, True)}
        Toolbox.verify_required_params(required_params=required_params, actual_params={'hostname': hostname}, verify_keys=True)
        if 'setup' not in self.config.keys():
            self.config['setup'] = {}
        if 'storagerouters' in self.config['setup'].keys():
            if storagerouter_ip in self.config['setup']['storagerouters']:
                raise ValueError('Storagerouter with given ip {0} already defined.'.format(storagerouter_ip))
        else:
            if 'storagerouters' not in self.config['setup']:
                self.config['setup']['storagerouters'] = {}
        self.config['setup']['storagerouters'][storagerouter_ip] = {'hostname': hostname}

    def remove_storagerouter(self, storagerouter_ip):
        """
        If a storagerouter with the given ip is present in the model, remove it.
        :param storagerouter_ip: ip to remove
        :type storagerouter_ip: str
        """
        try:
            self.config['setup']['storagerouters'].pop(storagerouter_ip)
        except Exception:
            pass

    def add_disk_to_sr(self, storagerouter_ip, name, roles):
        """
        Add disk with given name and roles to a storagerouter in the model.
        :param storagerouter_ip:
        :type storagerouter_ip: str
        :param name: name of the disk
        :type name: str
        :param roles: roles to assign to the disk
        :type roles: list
        """
        self._valid_storagerouter(storagerouter_ip)
        required_params = {'name': (str, None, True), 'roles': (list, None, True)}
        Toolbox.verify_required_params(required_params=required_params, actual_params={'name': name, 'roles': roles}, verify_keys=True)
        for role in roles:
            if role not in DiskPartition.ROLES:
                raise ValueError('Provided role {0} is not an allowed role for disk {1}.'.format(role, name))
        disk_dict = {name: {'roles': roles}}
        if 'disks' not in self.config['setup']['storagerouters'][storagerouter_ip]:
            self.config['setup']['storagerouters'][storagerouter_ip]['disks'] = {}
        self.config['setup']['storagerouters'][storagerouter_ip]['disks'].update(disk_dict)

    def remove_disk_from_sr(self, storagerouter_ip, name):
        """
        Remove given disk from the specified storagerouter
        :param storagerouter_ip: storagerouter to remove disk from
        :type storagerouter_ip: str
        :param name: name of the disk to be removed
        :type name: str
        """
        try:
            self.config['setup']['storagerouters'][storagerouter_ip]['disks'].pop(name)
        except Exception:
            pass

    def add_domain_to_sr(self, storagerouter_ip, name, recovery=False):
        """
        Add domains, present in the model, to a storage router.
        :param storagerouter_ip: ip of the storage router
        :type storagerouter_ip: str
        :param name: name of the domain to add to the storagerouter
        :type name: str
        :param recovery: true or false whether the domain is a recovery domain or not
        :type recovery: bool
        """
        self._valid_storagerouter(storagerouter_ip)
        Toolbox.verify_required_params(required_params={'name': (str, None, True)}, actual_params={'name': name}, verify_keys=True)

        if name not in self._domains:
            raise ValueError('Invalid domain passed: {0}'.format(name))

        path = self.config['setup']['storagerouters'][storagerouter_ip]
        if 'domains' not in path.keys():
            path['domains'] = {}
        path = path['domains']
        config_key = 'domain_guids' if recovery is False else 'recovery_domain_guids'
        if config_key not in path:
            path[config_key] = []
        path[config_key].append(name)

    def remove_domain_from_sr(self, storagerouter_ip, name):
        """
        Remove the given domain from the storagerouter
        :param storagerouter_ip: storagerouter to remove the domains from
        :type storagerouter_ip: str
        :param name: name of the domain to remove
        :type name: str
        """
        try:
            self.config['setup']['storagerouters'][storagerouter_ip]['domains']['domain_guids'].remove(name)
        except Exception:
            pass

    def add_backend(self, backend_name, domains=None, scaling='LOCAL'):
        """
        Add a backend with provided domains and scaling to the model.
        :param backend_name: name of the backend
        :type backend_name: str
        :param domains: domains the backend is linked to
        :type domains: {}
        :param scaling:
        :type scaling: str
        """
        if domains is None:
            domains = []
        else:
            for domain_name in domains:
                if domain_name not in self._domains:
                    raise ValueError('Invalid domain passed: {0}'.format(domain_name))

        Toolbox.verify_required_params(required_params={'backend_name': (str, Toolbox.regex_backend, True),
                                                        'domains': (list, self._domains, True),
                                                        'scaling': (str, AlbaBackend.SCALINGS, True)},
                                       actual_params={'backend_name': backend_name,
                                                      'domains': domains,
                                                      'scaling': scaling}, verify_keys=True)
        be_dict = {'name': backend_name,
                   'domains': {'domain_guids': domains},
                   'scaling': scaling}
        if 'setup' not in self.config.keys():
            self.config['setup'] = {}
        self._backends.append(be_dict['name'])
        if 'backends' not in self.config['setup']:
            self.config['setup']['backends'] = []
        self.config['setup']['backends'].append(be_dict)

    def remove_backend(self, backend_name):
        """
        Remove backend with given name from model
        :param backend_name: name of the backend to remove
        :type backend_name: str
        """
        for index, backend in enumerate(self.config['setup']['backends']):
            if backend['name'] == backend_name:
                self.config['setup']['backends'].pop(index)

    def add_preset_to_backend(self, backend_name, preset_name, policies, compression='snappy', encryption='none', fragment_size=2097152):
        """
        Add a preset with provided parameters to given backend.
        :param backend_name: name of the backend to which the preset should be added
        :type backend_name: str
        :param preset_name: name of the preset that should be added
        :type preset_name: str
        :param policies: nested list of policies
        :type policies: list
        :param compression: compression level
        :type compression: str
        :param encryption: encryption level
        :type encryption: str
        :param fragment_size:
        :type fragment_size: int
        """
        if backend_name not in self._backends:
            raise ValueError('Invalid backend passed as argument: {0}'.format(backend_name))

        self._check_policies(policies)

        compression_options = ['snappy', 'bz2', 'none']
        if compression not in compression_options:
            raise ValueError('Invalid compression format specified, please choose from: "{0}"'.format('', ''.join(compression_options)))

        encryption_options = ['aes-cbc-256', 'aes-ctr-256', 'none']
        if encryption not in encryption_options:
            raise ValueError('Invalid encryption format specified, please choose from: "{0}"'.format('', ''.join(encryption_options)))

        if fragment_size is not None and (not isinstance(fragment_size, int) or not 16 <= fragment_size <= 1024 ** 3):
            raise ValueError('Fragment size should be a positive integer smaller than 1 GiB')

        Toolbox.verify_required_params(required_params={'backend_name': (str, Toolbox.regex_backend, True),
                                                        'preset_name': (str, Toolbox.regex_preset, True),
                                                        'policies': (list, None, True),
                                                        'fragment_size': (int, None, False)},
                                       actual_params={'backend_name': backend_name,
                                                      'preset_name': preset_name,
                                                      'policies': policies,
                                                      'fragment_size': fragment_size},
                                       verify_keys=True)

        if encryption is None:
            encryption = 'none'
        preset_dict = {
            'name': preset_name,
            'compression': compression,
            'encryption': encryption,
            'policies': policies,
            'fragment_size': fragment_size,
        }
        self._presets.append(preset_dict['name'])
        for index, backend in enumerate(self.config['setup']['backends']):
            if backend['name'] == backend_name:
                if 'presets' not in backend:
                    self.config['setup']['backends'][index]['presets'] = []
                self.config['setup']['backends'][index]['presets'].append(preset_dict)

    def remove_preset_from_backend(self, backend_name, preset_name):
        """
        Remove the preset from given backend
        :param backend_name: name of the backend in which to search
        :type backend_name: str
        :param preset_name: preset name to remove
        :type preset_name: str
        """
        try:
            for index, backend in enumerate(self.config['setup']['backends']):
                if backend['name'] == backend_name:
                    if 'presets' in backend:
                        for jndex, preset in enumerate(self.config['backends'][index]['presets']):
                            if preset['name'] == preset_name:
                                self.config['setup']['backends'][index]['presets'].pop(jndex)
        except Exception:
            pass

    def add_osd_to_backend(self, backend_name, osds_on_disks=None, linked_backend=None, linked_preset=None):
        """
        Add an osd to given backend.
        :param backend_name:
        :type backend_name: str
        :param osds_on_disks:
        :type osds_on_disks: dict
            example: {'1.1.1.1': {'disk1': 2, 'disk2': 2}
        :param linked_backend:
        :type linked_backend: str
        :param linked_preset:
        :type linked_preset: str
        """
        if osds_on_disks is None:
            osds_on_disks = {}
        if backend_name not in self._backends:
            raise ValueError('Invalid backend passed as argument: {0}'.format(backend_name))
        required_params = {'backend_name': (str, None, True),
                           'osds_on_disk': (dict, None, False),
                           'linked_backend': (str, Toolbox.regex_backend, False),
                           'linked_preset': (str, Toolbox.regex_preset, False)}
        actual_params = {'backend_name': backend_name,
                         'osds_on_disk': osds_on_disks,
                         'linked_backend': linked_backend,
                         'linked_preset': linked_preset}
        Toolbox.verify_required_params(required_params=required_params, actual_params=actual_params, verify_keys=True)

        osd_dict = {}
        for index, backend in enumerate(self.config['setup']['backends']):
            if backend['name'] == backend_name:
                scaling = backend['scaling']
                if scaling == 'LOCAL':
                    if osds_on_disks is None:
                        raise ValueError('Osd dictionary required')
                    osd_dict = osds_on_disks
                elif scaling == 'GLOBAL':
                    if linked_backend not in self._backends:
                        raise ValueError('Provided backend {0} not in known backends'.format(linked_backend))
                    if linked_preset not in self._presets:
                        raise ValueError('Provided preset {0} not in known presets'.format(linked_preset))
                    osd_dict = {linked_backend: linked_preset}

                else:
                    raise ValueError('invalid scaling ({0}) passed'.format(scaling))
            if 'osds' not in backend:
                self.config['setup']['backends'][index]['osds'] = {}
            self.config['setup']['backends'][index]['osds'].update(osd_dict)

    def remove_osd_from_backend(self, osd_identifier, backend_name):
        """
        Remove the osd from given backend
        :param backend_name: name of the backend in which to search
        :type backend_name: str
        :param osd_identifier: osd name to remove
        :type osd_identifier: str
        """
        try:
            for index, backend in enumerate(self.config['setup']['backends']):
                if backend['name'] == backend_name:
                    self.config['setup']['backends'][index]['osds'].pop(osd_identifier)
        except Exception:
            pass

    def add_vpool(self, storagerouter_ip, backend_name, preset_name, storage_ip, vpool_name=None):
        """
        Add a vpool to given storagerouter
        :param storagerouter_ip
        :type storagerouter_ip: str
        :param vpool_name: name of the vpool to add
        :type vpool_name: str
        :param backend_name: name of the backend to link to the vpool
        :type backend_name: str
        :param preset_name: name of the preste to link to the vpool
        :type preset_name: str
        :param storage_ip:
        :type storage_ip: str
        """

        if vpool_name is None:
            vpool_name = 'myvpool{0}'.format(self.VPOOL_COUNTER)
            SetupJsonGenerator.VPOOL_COUNTER += 1

        required_params = {'storagerouter_ip': (str, Toolbox.regex_ip, True),
                           'vpool_name': (str, None, False),
                           'backend_name': (str, None, True),
                           'preset_name': (str, None, True),
                           'storage_ip': (str, Toolbox.regex_ip, True)}

        actual_params = {'storagerouter_ip': storagerouter_ip,
                         'vpool_name': vpool_name,
                         'backend_name': backend_name,
                         'preset_name': preset_name,
                         'storage_ip': storage_ip}

        Toolbox.verify_required_params(required_params=required_params, actual_params=actual_params, verify_keys=True)
        self._valid_storagerouter(storagerouter_ip=storagerouter_ip)
        self._validate_ip(ip=storage_ip)
        if backend_name not in self._backends:
            raise ValueError('Provided backend {0} not in known backends'.format(backend_name))
        if preset_name not in self._presets:
            raise ValueError('Provided preset not in known presets'.format(preset_name))
        vpool_dict = {'backend_name': backend_name,
                      'preset': preset_name,
                      'storage_ip': storage_ip,
                      'proxies': 1,
                      'fragment_cache': {'strategy': {'cache_on_read': False, 'cache_on_write': False},
                                         'location': 'disk'},
                      'block_cache': {'strategy': {'cache_on_read': False, 'cache_on_write': False},
                                      'location': 'disk'}
                      }
        if 'vpools' not in self.config['setup']['storagerouters'][storagerouter_ip]:
            self.config['setup']['storagerouters'][storagerouter_ip]['vpools'] = {}
        self.config['setup']['storagerouters'][storagerouter_ip]['vpools'][vpool_name] = vpool_dict

    def remove_vpool(self, storagerouter_ip, vpool_name):
        """
        Try to remove a vpool on storagerouter with given ip
        :param storagerouter_ip: search for vpool on given storagerouter
        :type storagerouter_ip: str
        :param vpool_name: remove vpool with this name
        :type vpool_name: str
        """
        try:
            self.config['setup']['storagerouters'][storagerouter_ip]['vpools'].pop(vpool_name)
        except Exception:
            pass

    def change_cache(self, storagerouter_ip, vpool, block_cache=True, fragment_cache=True, on_read=True, on_write=True):
        """
        Change the caching parameters of a given vpool on a given storagerouter. By default, change parameters of both block chache and fragment cache.
        :param storagerouter_ip: search for vpool on this storagerouter
        :type storagerouter_ip: str
        :param vpool: change cache options of given vpool
        :type vpool: str
        :param block_cache: change block cache parameters, default True
        :type block_cache: bool
        :param fragment_cache: change fragment cache parameters, default True
        :type fragment_cache: bool
        :param on_read: change onread parameters, default True
        :type on_read: bool
        :param on_write: chance onwrite parameters, default True
        :type on_write: bool
        """
        self._valid_storagerouter(storagerouter_ip=storagerouter_ip)

        required_params = {'vpool': (str, None, True),
                           'block_cache': (bool, None, False),
                           'fragment_cache': (bool, None, False),
                           'on_read': (bool, None, False),
                           'on_write': (bool, None, False)}
        actual_params = {'vpool': vpool,
                         'block_cache': block_cache,
                         'fragment_cache': fragment_cache,
                         'on_read': on_read,
                         'on_write': on_write}
        Toolbox.verify_required_params(required_params=required_params, actual_params=actual_params, verify_keys=True)
        try:
            vpool = self.config['setup']['storagerouters'][storagerouter_ip]['vpools'][vpool]
        except KeyError:
            raise ValueError('Vpool {0} not found'.format(vpool))
        if block_cache is True:
            vpool['block_cache']['strategy']['cache_on_read'] = on_read
            vpool['block_cache']['strategy']['cache_on_write'] = on_write
        if fragment_cache is True:
            vpool['fragment_cache']['strategy']['cache_on_read'] = on_read
            vpool['fragment_cache']['strategy']['cache_on_write'] = on_write

    def update_storagedriver_of_vpool(self, sr_ip, vpool_name, sr_params=None):
        '''
        Update all or some data of a storagedriver, assigned to a vpool on a specific storagerouter.
        :param sr_ip: ip of the storagerouter on which the vpool is located
        :type sr_ip: str
        :param vpool_name: name of the vpool of which to update the storagedriver data
        :type vpool_name: str
        :param sr_params: parameters to update of the referenced storagedriver
        :type sr_params: dict
        '''
        required_params = {'sco_size': (int, StorageDriverClient.TLOG_MULTIPLIER_MAP.keys()),
                           'cluster_size': (int, StorageDriverClient.CLUSTER_SIZES),
                           'volume_write_buffer': (int, {'min': 128, 'max': 10240}, False),
                           'global_read_buffer': (int, {'min': 128, 'max': 10240}, False),
                           'strategy': (str, None, False),
                           'deduplication': (str, None, False),
                           'dtl_transport': (str, StorageDriverClient.VPOOL_DTL_TRANSPORT_MAP.keys()),
                           'dtl_mode': (str, StorageDriverClient.VPOOL_DTL_MODE_MAP.keys())}

        default_params = {'sco_size': 4,
                          'cluster_size': 4,
                          'volume_write_buffer': 512,
                          'strategy': 'none',
                          'global_write_buffer': 128,
                          'global_read_buffer': 128,
                          'deduplication': 'non_dedupe',
                          'dtl_transport': 'tcp',
                          'dtl_mode': 'sync'}

        if sr_params is None:
            sr_params = {}
        default_params.update(sr_params)
        if not isinstance(default_params, dict):
            raise ValueError('Parameters should be of type "dict"')
        Toolbox.verify_required_params(required_params, default_params)
        if sr_ip not in self.config['setup']['storagerouters'].keys():
            raise KeyError('Storagerouter with ip is not defined')
        if vpool_name not in self.config['setup']['storagerouters'][sr_ip]['vpools']:
            raise KeyError('Vpool with name {0} is not defined on storagerouter with ip {1}'.format(vpool_name, sr_ip))
        self.config['setup']['storagerouters'][sr_ip]['vpools'][vpool_name]['storagedriver'] = default_params

    def remove_storagedriver_from_vpool(self, sr_ip, vpool_name):
        '''
        Remove the storagedriver details on given vpool of given storagerouter.
        :param sr_ip: ip of the storagerouter on which the vpool is located
        :type sr_ip: str
        :param vpool_name: name of the vpool of which to update the storagedriver data
        :type vpool_name: str
        '''
        try:
            self.config['setup']['storagerouters'][sr_ip]['vpools'][vpool_name].pop('storagedriver')
        except Exception:
            pass

    def _valid_storagerouter(self, storagerouter_ip):
        self._validate_ip(storagerouter_ip)
        if storagerouter_ip not in self.config['setup']['storagerouters']:
            raise ValueError('Storagerouter with ip {0} not found in json'.format(storagerouter_ip))

    def _validate_ip(self, ip):
        required_params = {'storagerouter_ip': (str, Toolbox.regex_ip, True)}
        try:
            Toolbox.verify_required_params(required_params=required_params, actual_params={'storagerouter_ip': ip}, verify_keys=True)
        except RuntimeError as e:
            raise ValueError(e)
        if os.system('ping -c 1 {0}'.format(ip)) != 0:
            raise ValueError('No response from ip {0}'.format(ip))

    def _check_policies(self, policies):
        class _Policy(object):
            def __init__(self, policy):
                if not isinstance(policy, list) or len(policy) != 4:
                    raise ValueError('Policy {0} must be of type list with length = 4'.format(policy))
                self.k, self.c, self.m, self.x = policy
                if all(isinstance(entry, int) for entry in policy) is False:
                    raise ValueError('All policy entries should be integers')

            def get_policy_as_dict(self):
                return {'k': self.k, 'c': self.c, 'm': self.m, 'x': self.x}

            def get_policy_as_list(self):
                return [self.k, self.c, self.x, self.m]

            def check_policy(self):
                if self.k > self.c:
                    raise ValueError('Invalid policy: k({0}) < c({1}) is required'.format(self.k, self.c))
                if self.c > self.k + self.m:
                    raise ValueError('Invalid policy: c({0}) < k + m ({1} + {2}) is required'.format(self.c, self.k, self.m))
                clone = self.get_policy_as_dict()
                clone.pop('m')
                if 0 in clone.values():
                    raise ValueError('Policy: {0}: {1} cannot be equal to zero'.format(self.get_policy_as_list(), ''.join([i[0] for i in clone.items() if i[1] == 0])))

        for p in policies:
            _Policy(p).check_policy()
