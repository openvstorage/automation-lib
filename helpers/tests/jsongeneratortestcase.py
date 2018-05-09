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
import unittest
from ci.api_lib.helpers.setupjsongenerator import SetupJsonGenerator


class JsonGeneratorTestcase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(JsonGeneratorTestcase, self).__init__(*args, **kwargs)
        self.generator = SetupJsonGenerator()
        self.ip_1 = '127.0.0.1'
        self.ip_2 = '127.0.0.2'
        self.ip_3 = '127.0.0.3'
        self.ip_4 = '127.0.0.4'

    def test_structure(self):
        self.assertEquals(len(self.generator.config.keys()), 0)
        self.assertTrue(isinstance(self.generator.config, dict))

    def test_model_ci(self):
        self.generator.update_ci(ci_params={'setup': True, 'grid_ip': self.ip_1})
        self.assertTrue(isinstance(self.generator.config['ci']['setup'], bool))
        self.assertEquals(len(self.generator.config['ci']), 10)

    def test_add_hypervisor(self):
        self.generator.update_ci(ci_params={'setup': True, 'grid_ip': self.ip_1})
        with self.assertRaises(ValueError):
            self.generator.add_hypervisor(hypervisor_ip='5')
        self.generator.add_hypervisor(hypervisor_ip=self.ip_1)
        self.assertEquals(len(self.generator.config['ci']), 11)
        self.assertTrue('vms' in self.generator.config['ci']['hypervisor'].keys())
        self.assertTrue('ubuntu_node_0.1' in self.generator.config['ci']['hypervisor']['vms'][self.ip_1]['name'])


    def test_remove_hypervisor(self):
        self.generator.update_ci(ci_params={'setup': True, 'grid_ip': self.ip_1})
        self.generator.add_hypervisor(hypervisor_ip=self.ip_1)
        self.generator.remove_hypervisor(hypervisor_ip=self.ip_2)
        self.generator.add_hypervisor(hypervisor_ip=self.ip_1)
        self.assertEquals(len(self.generator.config['ci']['hypervisor']), 5)

    def test_model_scenarios(self):
        self.generator.update_scenarios()
        self.assertEquals(self.generator.config['scenarios'], ['ALL'])
        with self.assertRaises(ValueError):
            self.generator.update_scenarios(['ABC', 'def'])

    def test_add_domain(self):
        self.generator.add_domain('domain1')
        self.generator.add_domain('domain2')
        self.assertEquals(len(self.generator.config['setup']['domains']), 2)
        with self.assertRaises(ValueError):
            self.generator.add_domain(7)

    def test_remove_domain(self):
        self.generator.add_domain('domain1')
        self.generator.add_domain('domain2')
        self.generator.remove_domain('domain1')
        self.assertEquals(len(self.generator.config['setup']['domains']), 1)

    def test_storagerouter_addition_removal(self):
        self.generator.add_domain('domain1')
        self.generator.add_domain('domain2')
        with self.assertRaises(ValueError):
            self.generator.add_storagerouter(storagerouter_ip='100', hostname='hostname')
        self.generator.add_storagerouter(storagerouter_ip=self.ip_1, hostname='hostname')
        self.assertTrue(self.ip_1 in self.generator.config['setup']['storagerouters'].keys())
        self.generator.add_storagerouter(storagerouter_ip=self.ip_2, hostname='hostname')
        self.generator.remove_storagerouter(storagerouter_ip=self.ip_2)
        self.assertFalse(self.ip_2 in self.generator.config['setup']['storagerouters'].keys())

        with self.assertRaises(ValueError):
            self.generator.add_disk_to_sr(storagerouter_ip='5', name='disk1', roles=['SCRUB', 'DTL'])
        with self.assertRaises(ValueError):
            self.generator.add_disk_to_sr(storagerouter_ip=self.ip_1, name='disk1', roles=['bla'])
        self.generator.add_disk_to_sr(storagerouter_ip=self.ip_1, name='disk1', roles=['SCRUB', 'DTL'])
        self.assertTrue('disk1' in self.generator.config['setup']['storagerouters'][self.ip_1]['disks'])
        self.assertEquals(len(self.generator.config['setup']['storagerouters'][self.ip_1]['disks']['disk1']['roles']), 2)
        self.generator.add_disk_to_sr(storagerouter_ip=self.ip_1, name='disk2', roles=['DB'])
        self.generator.remove_disk_from_sr(storagerouter_ip=self.ip_1, name='disk2')
        self.assertFalse('disk2' in self.generator.config['setup']['storagerouters'][self.ip_1])

        self.generator.add_domain_to_sr(storagerouter_ip=self.ip_1, name='domain1')
        self.generator.add_domain_to_sr(storagerouter_ip=self.ip_1, name='domain1', recovery=True)
        self.generator.add_domain_to_sr(storagerouter_ip=self.ip_1, name='domain2')
        self.generator.remove_domain_from_sr(storagerouter_ip=self.ip_1, name='domain2')
        self.assertFalse('domain2' in self.generator.config['setup']['storagerouters'][self.ip_1])

        self.assertEquals(len(self.generator.config['setup']['storagerouters'][self.ip_1]['domains']['domain_guids']), 1)
        self.assertEquals(len(self.generator.config['setup']['storagerouters'][self.ip_1]['domains']['recovery_domain_guids']), 1)

        self.generator.add_domain_to_sr(storagerouter_ip=self.ip_1, name='domain2')
        self.generator.add_domain_to_sr(storagerouter_ip=self.ip_1, name='domain2', recovery=True)
        self.assertEquals(len(self.generator.config['setup']['storagerouters'][self.ip_1]['domains']['domain_guids']), 2)
        self.assertEquals(len(self.generator.config['setup']['storagerouters'][self.ip_1]['domains']['recovery_domain_guids']), 2)

    def test_backend_addition_removal(self):
        self.generator.add_domain('domain1')
        self.generator.add_domain('domain2')

        self.generator.add_backend(backend_name='mybackend', domains=['domain1'])
        self.assertItemsEqual(self.generator.config['setup']['backends'][0].keys(), ['name', 'domains', 'scaling'])
        self.generator.add_backend(backend_name='mybackend02', domains=['domain1'], scaling='GLOBAL')
        self.assertItemsEqual(self.generator.config['setup']['backends'][1].keys(), ['name', 'domains', 'scaling'])

        self.generator.add_preset_to_backend(backend_name='mybackend02', preset_name='mypreset', policies=[[1, 2, 2, 1]])
        self.assertEqual(self.generator.config['setup']['backends'][1]['name'], 'mybackend02')
        with self.assertRaises(ValueError):
            self.generator.add_preset_to_backend(backend_name='non-existing_backend', preset_name='mypreset', policies=[1, 2, 2, 1])

        self.generator.add_osd_to_backend(backend_name='mybackend', osds_on_disks={self.ip_1: {'vdb': 2}})
        self.assertEquals(len(self.generator.config['setup']['backends'][0]['osds']), 1)

        self.generator.add_osd_to_backend(backend_name='mybackend', osds_on_disks={self.ip_2: {'vdb': 2}})
        self.assertEquals(len(self.generator.config['setup']['backends'][0]['osds']), 2)

        self.generator.remove_osd_from_backend(backend_name='mybackend', osd_identifier=self.ip_2)
        self.assertEquals(len(self.generator.config['setup']['backends'][0]['osds']), 1)

        self.assertEqual(self.generator.config['setup']['backends'][0]['osds'][self.ip_1]['vdb'], 2)
        with self.assertRaises(ValueError):
            self.generator.add_osd_to_backend(backend_name='mybackend02', osds_on_disks={self.ip_1: {'vdb': 2}})
        self.generator.add_osd_to_backend(backend_name='mybackend02', linked_backend='mybackend', linked_preset='mypreset')
        self.assertEqual(self.generator.config['setup']['backends'][1]['osds']['mybackend'], 'mypreset')
        self.generator.remove_backend('mybackend02')
        self.assertNotEquals(len(self.generator.config['setup']['backends']), 3)

    def test_vpool_addition_removal(self):
        vpoolname = 'vpool01'
        self.generator.add_domain('domain1')
        self.generator.add_storagerouter(storagerouter_ip=self.ip_1, hostname='hostname')
        self.generator.add_backend(backend_name='mybackend', domains=['domain1'])
        self.generator.add_preset_to_backend(backend_name='mybackend', preset_name='mypreset', policies=[[1, 2, 2, 1]])
        with self.assertRaises(ValueError):
            self.generator.add_vpool(storagerouter_ip=self.ip_1, vpool_name=vpoolname, backend_name='non-existing_backend', preset_name='mypreset', storage_ip=self.ip_1)
        with self.assertRaises(ValueError):
            self.generator.add_vpool(storagerouter_ip=self.ip_1, vpool_name=vpoolname, backend_name='mybackend', preset_name='non-existing_preset', storage_ip=self.ip_1)

        self.generator.add_vpool(storagerouter_ip=self.ip_1, vpool_name=vpoolname, backend_name='mybackend', preset_name='mypreset', storage_ip=self.ip_1)
        self.generator.add_vpool(storagerouter_ip=self.ip_1, backend_name='mybackend', preset_name='mypreset', storage_ip=self.ip_1, vpool_name='vpool1000')
        self.generator.remove_vpool(storagerouter_ip=self.ip_1, vpool_name='vpool1000')
        self.assertFalse('vpool1000' in self.generator.config['setup']['storagerouters'][self.ip_1]['vpools'])

    def test_storagedriver_addition_removal(self):
        vpoolname = 'vpool01'
        self.generator.add_domain('domain1')
        self.generator.add_storagerouter(storagerouter_ip=self.ip_1, hostname='hostname')
        self.generator.add_backend(backend_name='mybackend', domains=['domain1'])
        self.generator.add_preset_to_backend(backend_name='mybackend', preset_name='mypreset', policies=[[1, 2, 2, 1]])
        self.generator.add_vpool(storagerouter_ip=self.ip_1, vpool_name=vpoolname, backend_name='mybackend', preset_name='mypreset', storage_ip=self.ip_1)
        self.generator.update_storagedriver_of_vpool(sr_ip=self.ip_1, vpool_name=vpoolname, sr_params={'sco_size': 8})
        path = self.generator.config['setup']['storagerouters'][self.ip_1]['vpools'][vpoolname]
        self.assertEquals(path['storagedriver']['sco_size'], 8)
        self.assertTrue(isinstance(path['storagedriver']['deduplication'], str))
        self.generator.remove_storagedriver_from_vpool(sr_ip=self.ip_1, vpool_name=vpoolname)
        self.assertFalse('storagedriver' in path.keys())

    def test_full_flow(self):
        self.generator.update_ci(ci_params={'setup': True, 'grid_ip': self.ip_1})
        self.generator.add_hypervisor(hypervisor_ip=self.ip_1,
                                      virtual_machines={self.ip_2: {'name': 'ubuntu16.04-ovsnode01-setup1',
                                                                    'role': 'COMPUTE'},
                                                        self.ip_3: {'name': 'ubuntu16.04-ovsnode02-setup1',
                                                                    'role': 'VOLDRV'},
                                                        self.ip_4: {'name': 'ubuntu16.04-ovsnode03-setup1',
                                                                    'role': 'VOLDRV'}})

        self.generator.update_scenarios()
        self.generator.add_domain('Roubaix')
        self.generator.add_domain('Gravelines')
        self.generator.add_domain('Strasbourg')

        # add backends ####

        self.generator.add_backend(backend_name='mybackend', domains=['Roubaix'])
        self.generator.add_osd_to_backend(backend_name='mybackend', osds_on_disks={self.ip_2: {'sde': 2, 'sdf': 2},
                                                                                   self.ip_3: {'sde': 2, 'sdf': 2},
                                                                                   self.ip_4: {'sde': 2, 'sdf': 2}})
        self.generator.add_preset_to_backend(backend_name='mybackend', preset_name='mypreset', policies=[[1, 2, 2, 1]])

        self.generator.add_backend(backend_name='mybackend02', domains=['Gravelines'])
        self.generator.add_preset_to_backend(backend_name='mybackend02', preset_name='mypreset', policies=[[1, 2, 2, 1]])
        self.generator.add_osd_to_backend(backend_name='mybackend02', osds_on_disks={self.ip_2: {'sdg': 2},
                                                                                     self.ip_3: {'sdg': 2},
                                                                                     self.ip_4: {'sdg': 2}})

        self.generator.add_backend(backend_name='mybackend-global', domains=['Roubaix', 'Gravelines', 'Strasbourg'], scaling='GLOBAL')
        self.generator.add_preset_to_backend(backend_name='mybackend-global', preset_name='mypreset', policies=[[1, 2, 2, 1]])
        self.generator.add_osd_to_backend(backend_name='mybackend-global', linked_backend='mybackend', linked_preset='mypreset')
        self.generator.add_osd_to_backend(backend_name='mybackend-global', linked_backend='mybackend02', linked_preset='mypreset')

        # add storagerouter 1

        self.generator.add_storagerouter(storagerouter_ip=self.ip_2, hostname='ovs-node-1-1604')
        self.generator.add_domain_to_sr(storagerouter_ip=self.ip_2, name='Roubaix')
        self.generator.add_domain_to_sr(storagerouter_ip=self.ip_2, name='Gravelines', recovery=True)
        self.generator.add_domain_to_sr(storagerouter_ip=self.ip_2, name='Strasbourg', recovery=True)

        self.generator.add_disk_to_sr(storagerouter_ip=self.ip_2, name='sda', roles=['WRITE', 'DTL'])
        self.generator.add_disk_to_sr(storagerouter_ip=self.ip_2, name='sdb', roles=['DB'])
        self.generator.add_disk_to_sr(storagerouter_ip=self.ip_2, name='sdc', roles=['SCRUB'])

        self.generator.add_vpool(storagerouter_ip=self.ip_2, vpool_name='myvpool01', backend_name='mybackend-global', preset_name='mypreset', storage_ip=self.ip_1)
        self.generator.change_cache(storagerouter_ip=self.ip_2, vpool='myvpool01', block_cache=True, fragment_cache=False, on_write=False)
        self.generator.change_cache(storagerouter_ip=self.ip_2, vpool='myvpool01', fragment_cache=True, block_cache=False, on_read=False, on_write=True)
        self.generator.update_storagedriver_of_vpool(sr_ip=self.ip_2, vpool_name='myvpool01', sr_params={'sco_size': 8})

        # add storagerouter2

        self.generator.add_storagerouter(storagerouter_ip=self.ip_3, hostname='ovs-node-2-1604')
        self.generator.add_domain_to_sr(storagerouter_ip=self.ip_3, name='Gravelines')
        self.generator.add_domain_to_sr(storagerouter_ip=self.ip_3, name='Roubaix', recovery=True)
        self.generator.add_domain_to_sr(storagerouter_ip=self.ip_3, name='Strasbourg', recovery=True)

        self.generator.add_disk_to_sr(storagerouter_ip=self.ip_3, name='sda', roles=['WRITE', 'DTL'])
        self.generator.add_disk_to_sr(storagerouter_ip=self.ip_3, name='sdb', roles=['DB'])
        self.generator.add_disk_to_sr(storagerouter_ip=self.ip_3, name='sdc', roles=['SCRUB'])

        self.generator.add_vpool(storagerouter_ip=self.ip_3, vpool_name='myvpool01', backend_name='mybackend-global', preset_name='mypreset', storage_ip=self.ip_1)
        self.generator.change_cache(storagerouter_ip=self.ip_3, vpool='myvpool01', fragment_cache=True, block_cache=True, on_write=False, on_read=True)
        self.generator.update_storagedriver_of_vpool(sr_ip=self.ip_3, vpool_name='myvpool01')

        # add storagerouter 3

        self.generator.add_storagerouter(storagerouter_ip=self.ip_4, hostname='ovs-node-3-1604')
        self.generator.add_domain_to_sr(storagerouter_ip=self.ip_4, name='Gravelines')
        self.generator.add_domain_to_sr(storagerouter_ip=self.ip_4, name='Roubaix', recovery=True)
        self.generator.add_domain_to_sr(storagerouter_ip=self.ip_4, name='Strasbourg', recovery=True)

        self.generator.add_disk_to_sr(storagerouter_ip=self.ip_4, name='sda', roles=['WRITE', 'DTL'])
        self.generator.add_disk_to_sr(storagerouter_ip=self.ip_4, name='sdb', roles=['DB'])
        self.generator.add_disk_to_sr(storagerouter_ip=self.ip_4, name='sdc', roles=['SCRUB'])
        self.generator.add_vpool(storagerouter_ip=self.ip_4, vpool_name='myvpool01', backend_name='mybackend-global', preset_name='mypreset', storage_ip=self.ip_1)
        self.generator.update_storagedriver_of_vpool(sr_ip=self.ip_4, vpool_name='myvpool01', sr_params={'global_read_buffer': 256})

        expected_output = {u'ci': {u'cleanup': False,
                                   u'config_manager': u'arakoon',
                                   u'fail_on_failed_scenario': True,
                                   u'grid_ip': u'127.0.0.1',
                                   u'hypervisor': {u'password': u'rooter',
                                                   u'type': u'KVM',
                                                   u'user': u'root',
                                                   u'ip': u'127.0.0.1',
                                                   u'vms': {u'127.0.0.2': {u'name': u'ubuntu16.04-ovsnode01-setup1',
                                                                           u'role': u'COMPUTE'},
                                                            u'127.0.0.3': {u'name': u'ubuntu16.04-ovsnode02-setup1',
                                                                           u'role': u'VOLDRV'},
                                                            u'127.0.0.4': {u'name': u'ubuntu16.04-ovsnode03-setup1',
                                                                           u'role': u'VOLDRV'}}},
                                   u'local_hypervisor': {u'password': u'rooter',
                                                         u'type': u'KVM',
                                                         u'user': u'root'},
                                   u'scenarios': True,
                                   u'send_to_testrail': True,
                                   u'setup': True,
                                   u'user': {u'api': {u'password': u'admin', u'username': u'admin'},
                                             u'shell': {u'password': u'rooter', u'username': u'root'}},
                                   u'version': u'andes'},
                           u'scenarios': [u'ALL'],
                           u'setup': {
                               u'backends': [{u'domains': {u'domain_guids': [u'Roubaix']},
                                              u'name': u'mybackend',
                                              u'osds': {u'127.0.0.2': {u'sde': 2, u'sdf': 2},
                                                        u'127.0.0.3': {u'sde': 2, u'sdf': 2},
                                                        u'127.0.0.4': {u'sde': 2, u'sdf': 2}},
                                              u'presets': [{u'compression': u'snappy',
                                                            u'encryption': u'none',
                                                            u'fragment_size': 2097152,
                                                            u'name': u'mypreset',
                                                            u'policies': [[1, 2, 2, 1]]}],
                                              u'scaling': u'LOCAL'},
                                             {u'domains': {u'domain_guids': [u'Gravelines']},
                                              u'name': u'mybackend02',
                                              u'osds': {u'127.0.0.2': {u'sdg': 2},
                                                        u'127.0.0.3': {u'sdg': 2},
                                                        u'127.0.0.4': {u'sdg': 2}},
                                              u'presets': [{u'compression': u'snappy',
                                                            u'encryption': u'none',
                                                            u'fragment_size': 2097152,
                                                            u'name': u'mypreset',
                                                            u'policies': [[1, 2, 2, 1]]}],
                                              u'scaling': u'LOCAL'},
                                             {u'domains': {u'domain_guids': [u'Roubaix', u'Gravelines', u'Strasbourg']},
                                              u'name': u'mybackend-global',
                                              u'osds': {u'mybackend': u'mypreset', u'mybackend02': u'mypreset'},
                                              u'presets': [{u'compression': u'snappy',
                                                            u'encryption': u'none',
                                                            u'fragment_size': 2097152,
                                                            u'name': u'mypreset',
                                                            u'policies': [[1, 2, 2, 1]]}],
                                              u'scaling': u'GLOBAL'}],

                               u'domains': [u'Roubaix', u'Gravelines', u'Strasbourg'],
                               u'storagerouters': {u'127.0.0.2': {u'disks': {u'sda': {u'roles': [u'WRITE',
                                                                                                 u'DTL']},
                                                                             u'sdb': {u'roles': [u'DB']},
                                                                             u'sdc': {u'roles': [u'SCRUB']}},
                                                                  u'domains': {u'domain_guids': [u'Roubaix'],
                                                                               u'recovery_domain_guids': [u'Gravelines', u'Strasbourg']},
                                                                  u'hostname': u'ovs-node-1-1604',
                                                                  u'vpools': {u'myvpool01': {u'backend_name': u'mybackend-global',
                                                                                             u'block_cache': {u'location': u'disk',
                                                                                                              u'strategy': {u'cache_on_read': True, u'cache_on_write': False}},
                                                                                             u'fragment_cache': {u'location': u'disk',
                                                                                                                 u'strategy': {u'cache_on_read': False, u'cache_on_write': True}},
                                                                                             u'preset': u'mypreset',
                                                                                             u'proxies': 1,
                                                                                             u'storage_ip': u'127.0.0.1',
                                                                                             u'storagedriver': {u'cluster_size': 4,
                                                                                                                u'dtl_mode': u'sync',
                                                                                                                u'dtl_transport': u'tcp',
                                                                                                                u'global_write_buffer': 128,
                                                                                                                u'global_read_buffer': 128,
                                                                                                                u'deduplication': "non_dedupe",
                                                                                                                u'strategy': "none",
                                                                                                                u'sco_size': 8,
                                                                                                                u'volume_write_buffer': 512}}}},
                                                   u'127.0.0.3': {u'disks': {u'sda': {u'roles': [u'WRITE', u'DTL']},
                                                                             u'sdb': {u'roles': [u'DB']},
                                                                             u'sdc': {u'roles': [u'SCRUB']}},
                                                                  u'domains': {u'domain_guids': [u'Gravelines'],
                                                                               u'recovery_domain_guids': [u'Roubaix', u'Strasbourg']},
                                                                  u'hostname': u'ovs-node-2-1604',
                                                                  u'vpools': {u'myvpool01': {u'backend_name': u'mybackend-global',
                                                                                             u'block_cache': {u'location': u'disk',
                                                                                                              u'strategy': {u'cache_on_read': True, u'cache_on_write': False}},
                                                                                             u'fragment_cache': {u'location': u'disk',
                                                                                                                 u'strategy': {u'cache_on_read': True, u'cache_on_write': False}},
                                                                                             u'preset': u'mypreset',
                                                                                             u'proxies': 1,
                                                                                             u'storage_ip': u'127.0.0.1',
                                                                                             u'storagedriver': {u'cluster_size': 4,
                                                                                                                u'dtl_mode': u'sync',
                                                                                                                u'dtl_transport': u'tcp',
                                                                                                                u'global_write_buffer': 128,
                                                                                                                u'global_read_buffer': 128,
                                                                                                                u'deduplication': "non_dedupe",
                                                                                                                u'strategy': "none",
                                                                                                                u'sco_size': 4,
                                                                                                                u'volume_write_buffer': 512}}}},
                                                   u'127.0.0.4': {u'disks': {u'sda': {u'roles': [u'WRITE', u'DTL']},
                                                                             u'sdb': {u'roles': [u'DB']},
                                                                             u'sdc': {u'roles': [u'SCRUB']}},
                                                                  u'domains': {u'domain_guids': [u'Gravelines'],
                                                                               u'recovery_domain_guids': [u'Roubaix', u'Strasbourg']},
                                                                  u'hostname': u'ovs-node-3-1604',
                                                                  u'vpools': {u'myvpool01': {u'backend_name': u'mybackend-global',
                                                                                             u'block_cache': {u'location': u'disk',
                                                                                                              u'strategy': {u'cache_on_read': False, u'cache_on_write': False}},
                                                                                             u'fragment_cache': {u'location': u'disk',
                                                                                                                 u'strategy': {u'cache_on_read': False, u'cache_on_write': False}},
                                                                                             u'preset': u'mypreset',
                                                                                             u'proxies': 1,
                                                                                             u'storage_ip': u'127.0.0.1',
                                                                                             u'storagedriver': {u'cluster_size': 4,
                                                                                                                u'dtl_mode': u'sync',
                                                                                                                u'dtl_transport': u'tcp',
                                                                                                                u'global_write_buffer': 128,
                                                                                                                u'global_read_buffer': 256,
                                                                                                                u'deduplication': "non_dedupe",
                                                                                                                u'strategy': "none",
                                                                                                                u'sco_size': 4,
                                                                                                                u'volume_write_buffer': 512}}}}}
                           }
                           }

        self.assertDictEqual(self.generator.config['ci'], expected_output[u'ci'])
        self.assertEqual(self.generator.config['setup']['domains'], expected_output['setup'][u'domains'])
        self.assertDictEqual(self.generator.config['setup']['storagerouters'], expected_output['setup'][u'storagerouters'])
        self.assertEqual(self.generator.config['setup']['backends'], expected_output['setup'][u'backends'])

        self.assertDictEqual(self.generator.config, expected_output)


if __name__ == '__main__':
    unittest.main()
