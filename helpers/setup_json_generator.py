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
import socket
from ovs.lib.helpers.toolbox import Toolbox
import difflib


class Setup_json_generator(object):
    def __init__(self):
        self.json = {
            'ci': {},
            'scenarios': [],
            'setup': {
                "domains": [], "backends": [], "storagerouters": {}
            }
        }

        self._presets = []
        self._domains = []
        self._backends = []
        self._ips = []

    def get_dict(self):
        return self.json

    def write_to_json(self, path):
        with open(path, 'w') as fp:
            json.dump(self.get_dict(), indent=4, sort_keys=True, fp=fp)

    def model_scenarios(self, scenarios=None):
        if not isinstance(scenarios,list) and scenarios is not None:
            raise ValueError('Scenarios should be passed in a list format, not {}'.format(type(scenarios)))
        if scenarios == None:
            self.json['scenarios'] = ["ALL"]
        else:
            self.json['scenarios'] = scenarios

    def model_ci(self, grid_ip, optional_params=None):
        if optional_params is None:
            optional_params = {}

        try:
            socket.inet_aton(grid_ip)
        except TypeError:
            raise ValueError('Invalid ip adress provided: {}'.format(grid_ip))

        bool_options = {'setup': True, 'validation': True, 'scenarios': True, 'cleanup': False, 'send_to_testrail': True,
                        'fail_on_failed_scenario': True}
        int_options = {'setup_retries': 1, 'scenario_retries': 1}
        str_options = {'version': 'fargo', 'config_manager': 'arakoon'}

        for key, value in optional_params:
            if key in bool_options.keys() and isinstance(value, bool):
                bool_options[key] = value
            elif key in int_options.keys() and isinstance(value, int):
                int_options[key] = value
            elif key in str_options.keys() and isinstance(value, str):
                str_options[key] = value

        ci = {
            "setup": bool_options['setup'],  # Required
            "validation": bool_options['validation'],  # Not even used
            "scenarios": bool_options['scenarios'],  # Optional
            "cleanup": bool_options['cleanup'],  # optional
            "send_to_testrail": bool_options['send_to_testrail'],  # Optional
            "fail_on_failed_scenario": bool_options['fail_on_failed_scenario'],  # Optional
            "setup_retries": int_options['setup_retries'],  # Optional
            "scenario_retries": int_options['scenario_retries'],  # Optional
            "version": str_options['version'],
            "local_hypervisor": {  # enkel voor testen, niet voor setup
                "type": "KVM",
                "user": "root",
                "password": "rooter"
            },

            "hypervisor": {},
            "config_manager": str_options['config_manager'],
            "user": {
                "shell": {
                    "username": "root",
                    "password": "rooter"
                },
                "api": {
                    "username": "admin",
                    "password": "admin"
                }
            },
            "grid_ip": grid_ip
        }
        self.json['ci'] = ci

    def _add_hypervisor(self, machine_ip, vms=None):
        if vms is None:
            vms = {'vm_ip': {'name': '_name', 'role': '_role'}}
        hypervisor_dict = {
            "type": "KVM",
            'ip': machine_ip,
            'user': 'root',
            'password': 'rooter',
            'vms': vms
        }
        for i in vms.keys():
            self._ips.append(i)
        self.json['ci']['hypervisor'] = hypervisor_dict

    def add_storagerouter(self, storagerouter_ip, hostname):
        try:
            socket.inet_aton(storagerouter_ip)
        except TypeError:
            raise ValueError('Invalid ip adress provided: {0}'.format(storagerouter_ip))
        if not isinstance(hostname,str):
            raise ValueError('Invalid hostname provided: {0} must be a string, not {1}'.format(hostname,type(hostname)))
        sr_dict = {}
        sr_dict[storagerouter_ip] = {"hostname": hostname,
                                     "domains": {},
                                     "disks": {},
                                     "vpools": {}
                                     }
        self.json['setup']['storagerouters'].update(sr_dict)

    def _add_disk_to_sr(self, storagerouter_ip, name, roles):
        if not storagerouter_ip in self.json['setup']['storagerouters'].keys():
            raise ValueError('Storagerouter with IP {0} not found in json'.format(storagerouter_ip))
        d_dict = {}
        d_dict[name] = {"roles": roles}
        self.json['setup']['storagerouters'][storagerouter_ip]['disks'].update(d_dict)

    def _add_domain_to_sr(self, storagerouter_ip, name, recovery=False):
        if not storagerouter_ip in self.json['setup']['storagerouters'].keys():
            raise ValueError('Storagerouter with ip {0} not found in json'.format(storagerouter_ip))
        if not name in self._domains:
            raise ValueError('Invalid domain passed: {}'.format(name))
        path = self.json['setup']['storagerouters'][storagerouter_ip]['domains']

        if recovery is False:
            if 'domain_guids' not in path.keys():
                path['domain_guids'] = [name]
            else:
                path['domain_guids'].append(name)
        else:
            if 'recovery_domain_guids' not in path.keys():
                path['recovery_domain_guids'] = [name]
            else:
                path['recovery_domain_guids'].append(name)

    def add_domain(self, domain):
        if not isinstance(domain, str):
            raise ValueError("domain is no string")
        self._domains.append(domain)
        self.json['setup']['domains'].append(domain)

    def add_backend(self, name, domains=None, scaling='LOCAL'):
        if domains is None:
            domains = []
        for domain_name in domains:
            if domain_name not in self._domains:
                raise ValueError('Invalid domain passed: {}'.format(domain_name))

        be_dict = {'name': name,
                   'domains': {'domain_guids': domains},
                   'scaling': scaling,
                   'presets': [],
                   'osds': {}
                   }
        self._backends.append(be_dict['name'])
        self.json['setup']['backends'].append(be_dict)

    def _add_preset_to_backend(self, backend_name, preset_name, policies, compression='snappy', encryption=None, fragment_size=2097152):
        if backend_name not in self._backends:
            raise ValueError('Invalid backend passed as argument: {}'.format(backend_name))
        if encryption == None:
            encryption = 'none'
        preset_dict = {
            'name': preset_name,
            'compression': compression,
            'encryption': encryption,
            'policies': policies,
            'fragment_size': fragment_size,
        }
        self._presets.append(preset_dict['name'])
        for i in range(len(self.json['setup']['backends'])):
            if self.json['setup']['backends'][i]['name'] == backend_name:
                self.json['setup']['backends'][i]['presets'].append(preset_dict)
                # 'presets'].append(preset_dict)

    def _add_osd_to_backend(self, backend_name, osds_on_disks=None, linked_backend=None, linked_preset=None):
        if backend_name not in self._backends:
            raise ValueError('Invalid backend passed as argument: {}'.format(backend_name))

        osd_dict = {}
        for i in range(len(self.json['setup']['backends'])):
            if self.json['setup']['backends'][i]['name'] == backend_name:
                scaling = self.json['setup']['backends'][i]['scaling']
                if scaling == 'LOCAL':
                    if osds_on_disks is None:
                        raise ValueError('Osd dictionairy required')
                    osd_dict = osds_on_disks
                elif scaling == 'GLOBAL':
                    if linked_backend not in self._backends:
                        raise ValueError("Provided backend {} not in known backends".format(linked_backend))
                    if linked_preset not in self._presets:
                        raise ValueError("Provided preset {} not in known presets".format(linked_preset))
                    osd_dict = {linked_backend: linked_preset}

                else:
                    print ValueError('invalid scaling ({0}) passed'.format(scaling))
            self.json['setup']['backends'][i]['osds'].update(osd_dict)

    def add_vpool(self, storagerouter_ip, vpool_name, backend_name, preset, storage_ip):
        if backend_name not in self._backends:
            raise ValueError("Provided backend {} not in known backends".format(backend_name))
        if preset not in self._presets:
            raise ValueError('Provided preset not in known presets'.format(preset))

        vpool_dict = {'backend_name': backend_name,
                      'preset': preset,
                      'storage_ip': storage_ip,
                      'proxies':1,
                      'fragment_cache': {
                          'strategy': {'cache_on_read': False, 'cache_on_write': False},
                          'location': "disk"
                      },
                      'block_cache': {
                          'strategy': {'cache_on_read': False, 'cache_on_write': False},
                          'location': "disk"
                      },
                      'storagedriver':
                          {
                              "sco_size": 4,
                              "cluster_size": 4,
                              "volume_write_buffer": 512,
                              "strategy": "none",
                              "global_write_buffer": 20,
                              "global_read_buffer": 0,
                              "deduplication": "non_dedupe",
                              "dtl_transport": "tcp",
                              "dtl_mode": "sync"
                          }
                      }
        self.json['setup']['storagerouters'][storagerouter_ip]['vpools'][vpool_name] = vpool_dict

    def _change_cache(self, storagerouter_ip, vpool, block_cache=True, fragment_cache=True, on_read=True, on_write=True):
        try:
            vpool = self.json['setup']['storagerouters'][storagerouter_ip]['vpools'][vpool]
            if block_cache is True:
                vpool['block_cache']['strategy']['cache_on_read'] = on_read
                vpool['block_cache']['strategy']['cache_on_write'] = on_write
            if fragment_cache is True:
                vpool['fragment_cache']['strategy']['cache_on_read'] = on_read
                vpool['fragment_cache']['strategy']['cache_on_write'] = on_write

        except KeyError as e:
            raise ValueError('Vpool not found with exception {0}'.format(e))

    @classmethod
    def reformat_json(cls, in_path, out_path=None):
        if not isinstance(in_path, str) or (out_path is not None and not isinstance(out_path, str)):
            raise ValueError('path should be string type, got {}'.format(type(in_path)))
        if out_path is None:
            out_path = in_path.rstrip('.json') + '_reformatted.json'

        with open(in_path) as json_data:
            d = json.load(json_data)
        with open(out_path, 'w') as fp:
            json.dump(d, fp=fp, indent=4, sort_keys=True)

    @classmethod
    def compare_files(cls, file1, file2):
        print 'comparing {} and {}'.format(file1, file2)
        with open(file1) as fh1, open(file2) as fh2:
            lines_file1 = fh1.readlines()
            lines_file2 = fh2.readlines()

        d = difflib.Differ()
        diff = d.compare(lines_file1, lines_file2)
        for i in diff:
            if i[0] != ' ':
                print i




