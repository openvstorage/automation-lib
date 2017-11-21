import unittest
from ci.api_lib.helpers.setup_json_generator import Setup_json_generator
import json
import difflib
import pprint

class Json_generator_testcase(unittest.TestCase):

    def __init__(self,*args, **kwargs):
        super(Json_generator_testcase, self).__init__(*args, **kwargs)
        self.generator = Setup_json_generator()
        self.ip = '10.100.100.100'

    def test_structure(self):
        self.assertEquals(len((self.generator).get_dict().keys()), 3)

    def test_model_ci(self):
        self.generator.model_ci(grid_ip=self.ip)
        self.assertTrue(isinstance(self.generator.get_dict()['ci']['setup'],bool))

    def test_model_scenarios(self):
        self.generator.model_scenarios()
        self.assertEquals(self.generator.get_dict()['scenarios'],['ALL'])
        self.generator.model_scenarios(['ABC','def'])
        self.assertEquals(self.generator.get_dict()['scenarios'],['ABC', 'def'])

    def test_add_domain(self):
        self.generator.add_domain('domain1')
        self.generator.add_domain('domain2')
        self.assertEquals(len(self.generator.get_dict()['setup']['domains']), 2)
        with self.assertRaises(ValueError):
            self.generator.add_domain(7)

    def test_add_storagerouter(self):
        self.generator.add_domain('domain1')
        self.generator.add_domain('domain2')
        with self.assertRaises(ValueError):
            self.generator.add_storagerouter(storagerouter_ip=100, hostname='hostname')
        with self.assertRaises(ValueError):
            self.generator.add_storagerouter(storagerouter_ip=self.ip, hostname=7)
        self.generator.add_storagerouter(storagerouter_ip=self.ip,hostname='hostname')
        self.assertTrue(self.ip in self.generator.get_dict()['setup']['storagerouters'].keys())

        self.generator._add_disk_to_sr(storagerouter_ip=self.ip,name='disk1',roles=['role1','role2'])
        self.assertTrue('disk1' in self.generator.get_dict()['setup']['storagerouters'][self.ip]['disks'])
        self.assertEquals(len(self.generator.get_dict()['setup']['storagerouters'][self.ip]['disks']['disk1']['roles']), 2)

        self.generator._add_domain_to_sr(storagerouter_ip=self.ip, name='domain1')
        self.generator._add_domain_to_sr(storagerouter_ip=self.ip, name='domain1',recovery=True)
        self.assertEquals(len(self.generator.get_dict()['setup']['storagerouters'][self.ip]['domains']['domain_guids']), 1)
        self.assertEquals(len(self.generator.get_dict()['setup']['storagerouters'][self.ip]['domains']['recovery_domain_guids']), 1)

        self.generator._add_domain_to_sr(storagerouter_ip=self.ip, name='domain2')
        self.generator._add_domain_to_sr(storagerouter_ip=self.ip, name='domain2',recovery=True)
        self.assertEquals(len(self.generator.get_dict()['setup']['storagerouters'][self.ip]['domains']['domain_guids']), 2)
        self.assertEquals(len(self.generator.get_dict()['setup']['storagerouters'][self.ip]['domains']['recovery_domain_guids']), 2)

    def test_add_backend(self):
        self.generator.add_domain('domain1')
        self.generator.add_domain('domain2')

        self.generator.add_backend(name='mybackend', domains=['domain1'])
        self.assertItemsEqual(self.generator.get_dict()['setup']['backends'][0].keys(),['name','domains','scaling','presets','osds'])
        self.generator.add_backend(name='mybackend_02', domains=['domain1'],scaling='GLOBAL')
        self.assertItemsEqual(self.generator.get_dict()['setup']['backends'][1].keys(),['name','domains','scaling','presets','osds'])

        self.generator._add_preset_to_backend(backend_name='mybackend_02',preset_name='mypreset',policies=[1,2,2,1])
        self.assertEqual(self.generator.get_dict()['setup']['backends'][1]['name'],'mybackend_02')
        with self.assertRaises(ValueError):
            self.generator._add_preset_to_backend(backend_name='non-existing_backend',preset_name='mypreset',policies=[1,2,2,1])

        self.generator._add_osd_to_backend(backend_name='mybackend',osds_on_disks={self.ip: {'vdb': 2}})
        self.assertEqual(self.generator.get_dict()['setup']['backends'][0]['osds'][self.ip]['vdb'],2)
        with self.assertRaises(ValueError):
            self.generator._add_osd_to_backend(backend_name='mybackend_02',osds_on_disks={self.ip: {'vdb': 2}})
        self.generator._add_osd_to_backend(backend_name='mybackend_02',linked_backend='mybackend',linked_preset='mypreset')
        self.assertEqual(self.generator.get_dict()['setup']['backends'][1]['osds']['mybackend'],'mypreset')

    def test_add_vpool(self):
        vpoolname = 'vpool01'
        self.generator.add_domain('domain1')
        self.generator.add_storagerouter(storagerouter_ip=self.ip, hostname='hostname')
        self.generator.add_backend(name='mybackend', domains=['domain1'])
        self.generator._add_preset_to_backend(backend_name='mybackend',preset_name='mypreset',policies=[1,2,2,1])
        with self.assertRaises(ValueError):
            self.generator.add_vpool(storagerouter_ip=self.ip, vpool_name=vpoolname, backend_name='non-existing_backend',preset='mypreset',storage_ip=self.ip)
        with self.assertRaises(ValueError):
            self.generator.add_vpool(storagerouter_ip=self.ip, vpool_name=vpoolname, backend_name='mybackend',preset='non-existing_preset',storage_ip=self.ip)

        self.generator.add_vpool(storagerouter_ip=self.ip, vpool_name=vpoolname, backend_name='mybackend',preset='mypreset',storage_ip=self.ip)
        self.assertTrue(vpoolname in self.generator.get_dict()['setup']['storagerouters'][self.ip]['vpools'].keys())
        self.assertTrue('storagedriver' in self.generator.get_dict()['setup']['storagerouters'][self.ip]['vpools'][vpoolname].keys())

    def test_full_flow(self):
        self.generator.model_ci('10.100.199.171')
        self.generator._add_hypervisor(machine_ip='10.100.69.222', vms = {'10.100.199.171': {'name': 'ubuntu16.04-ovsnode01-setup1',
                                                                                'role': 'COMPUTE'},
                                                                            '10.100.199.172': {'name': 'ubuntu16.04-ovsnode02-setup1',
                                                                                'role': 'VOLDRV'},
                                                                            '10.100.199.173': {'name': 'ubuntu16.04-ovsnode03-setup1',
                                                                                'role': 'VOLDRV'}
                                                                          })

        self.generator.model_scenarios()
        self.generator.add_domain('Roubaix')
        self.generator.add_domain('Gravelines')
        self.generator.add_domain('Strasbourg')

        #### add backends ####

        self.generator.add_backend(name='mybackend', domains=['Roubaix'])
        self.generator._add_osd_to_backend(backend_name='mybackend',osds_on_disks={'10.100.199.171': {'sde': 2,'sdf': 2},
                                                                                    '10.100.199.172': {'sde': 2,'sdf': 2},
                                                                                    '10.100.199.173': {'sde': 2, 'sdf': 2}})
        self.generator._add_preset_to_backend(backend_name='mybackend',preset_name='mypreset',policies=[[1,2,2,1]])

        self.generator.add_backend(name='mybackend02',domains=['Gravelines'])
        self.generator._add_preset_to_backend(backend_name='mybackend02',preset_name='mypreset',policies=[[1,2,2,1]])
        self.generator._add_osd_to_backend(backend_name='mybackend02',osds_on_disks={'10.100.199.171': {'sdg': 2},
                                                                                        '10.100.199.172': {'sdg': 2},
                                                                                        '10.100.199.173': {'sdg': 2}})

        self.generator.add_backend(name='mybackend-global',domains=['Roubaix','Gravelines','Strasbourg'],scaling='GLOBAL')
        self.generator._add_preset_to_backend(backend_name='mybackend-global',preset_name='mypreset',policies=[[1,2,2,1]])
        self.generator._add_osd_to_backend(backend_name='mybackend-global',linked_backend='mybackend',linked_preset='mypreset')
        self.generator._add_osd_to_backend(backend_name='mybackend-global',linked_backend='mybackend02',linked_preset='mypreset')

        #### add storagerouter 1

        self.generator.add_storagerouter(storagerouter_ip='10.100.199.171', hostname='ovs-node-1-1604')
        self.generator._add_domain_to_sr(storagerouter_ip='10.100.199.171',name='Roubaix')
        self.generator._add_domain_to_sr(storagerouter_ip='10.100.199.171',name='Gravelines',recovery=True)
        self.generator._add_domain_to_sr(storagerouter_ip='10.100.199.171',name='Strasbourg',recovery=True)

        self.generator._add_disk_to_sr(storagerouter_ip='10.100.199.171',name='sda',roles=['WRITE','DTL'])
        self.generator._add_disk_to_sr(storagerouter_ip='10.100.199.171',name='sdb',roles=['DB'])
        self.generator._add_disk_to_sr(storagerouter_ip='10.100.199.171',name='sdc',roles=['SCRUB'])

        self.generator.add_vpool(storagerouter_ip='10.100.199.171', vpool_name='myvpool01', backend_name='mybackend-global',preset='mypreset',storage_ip='10.100.199.171')
        self.generator._change_cache(storagerouter_ip='10.100.199.171',vpool='myvpool01',block_cache=True,fragment_cache=False,on_write=False)
        self.generator._change_cache(storagerouter_ip='10.100.199.171',vpool='myvpool01',fragment_cache=True,block_cache=False,on_read=False,on_write=True)


        #### add storagerouter2

        self.generator.add_storagerouter(storagerouter_ip='10.100.199.172', hostname='ovs-node-2-1604')
        self.generator._add_domain_to_sr(storagerouter_ip='10.100.199.172',name='Gravelines')
        self.generator._add_domain_to_sr(storagerouter_ip='10.100.199.172',name='Roubaix',recovery=True)
        self.generator._add_domain_to_sr(storagerouter_ip='10.100.199.172',name='Strasbourg',recovery=True)

        self.generator._add_disk_to_sr(storagerouter_ip='10.100.199.172',name='sda',roles=['WRITE','DTL'])
        self.generator._add_disk_to_sr(storagerouter_ip='10.100.199.172',name='sdb',roles=['DB'])
        self.generator._add_disk_to_sr(storagerouter_ip='10.100.199.172',name='sdc',roles=['SCRUB'])

        self.generator.add_vpool(storagerouter_ip='10.100.199.172', vpool_name='myvpool01', backend_name='mybackend-global',preset='mypreset',storage_ip='10.100.199.172')
        self.generator._change_cache(storagerouter_ip='10.100.199.172',vpool='myvpool01',fragment_cache=True,block_cache=True,on_write=False, on_read=True)



        #### add storagerouter 3

        self.generator.add_storagerouter(storagerouter_ip='10.100.199.173', hostname='ovs-node-3-1604')
        self.generator._add_domain_to_sr(storagerouter_ip='10.100.199.173',name='Gravelines')
        self.generator._add_domain_to_sr(storagerouter_ip='10.100.199.173',name='Roubaix',recovery=True)
        self.generator._add_domain_to_sr(storagerouter_ip='10.100.199.173',name='Strasbourg',recovery=True)


        self.generator._add_disk_to_sr(storagerouter_ip='10.100.199.173',name='sda',roles=['WRITE','DTL'])
        self.generator._add_disk_to_sr(storagerouter_ip='10.100.199.173',name='sdb',roles=['DB'])
        self.generator._add_disk_to_sr(storagerouter_ip='10.100.199.173',name='sdc',roles=['SCRUB'])
        self.generator.add_vpool(storagerouter_ip='10.100.199.173', vpool_name='myvpool01', backend_name='mybackend-global',preset='mypreset',storage_ip='10.100.199.173')


        expected_output = {u'ci': {u'cleanup': False,
                                   u'config_manager': u'arakoon',
                                   u'fail_on_failed_scenario': True,
                                   u'grid_ip': u'10.100.199.171',
                                   u'hypervisor': {u'ip': u'10.100.69.222',
                                                   u'password': u'rooter',
                                                   u'type': u'KVM',
                                                   u'user': u'root',
                                                   u'vms': {u'10.100.199.171': {u'name': u'ubuntu16.04-ovsnode01-setup1',
                                                                                u'role': u'COMPUTE'},
                                                            u'10.100.199.172': {u'name': u'ubuntu16.04-ovsnode02-setup1',
                                                                                u'role': u'VOLDRV'},
                                                            u'10.100.199.173': {u'name': u'ubuntu16.04-ovsnode03-setup1',
                                                                                u'role': u'VOLDRV'}}
                                                   },
                                   u'local_hypervisor': {u'password': u'rooter',
                                                         u'type': u'KVM',
                                                         u'user': u'root'},
                                   u'scenario_retries': 1,
                                   u'scenarios': True,
                                   u'send_to_testrail': True,
                                   u'setup': True,
                                   u'setup_retries': 1,
                                   u'user': {u'api': {u'password': u'admin', u'username': u'admin'},
                                             u'shell': {u'password': u'rooter', u'username': u'root'}},
                                   u'validation': True,
                                   u'version': u'fargo'},
                           u'scenarios': [u'ALL'],
                           u'setup': {u'backends': [{u'domains': {u'domain_guids': [u'Roubaix']},
                                                     u'name': u'mybackend',
                                                     u'osds': {u'10.100.199.171': {u'sde': 2, u'sdf': 2},
                                                               u'10.100.199.172': {u'sde': 2, u'sdf': 2},
                                                               u'10.100.199.173': {u'sde': 2, u'sdf': 2}},
                                                     u'presets': [{u'compression': u'snappy',
                                                                   u'encryption': u'none',
                                                                   u'fragment_size': 2097152,
                                                                   u'name': u'mypreset',
                                                                   u'policies': [[1, 2, 2, 1]]}],
                                                     u'scaling': u'LOCAL'},
                                                    {u'domains': {u'domain_guids': [u'Gravelines']},
                                                     u'name': u'mybackend02',
                                                     u'osds': {u'10.100.199.171': {u'sdg': 2},
                                                               u'10.100.199.172': {u'sdg': 2},
                                                               u'10.100.199.173': {u'sdg': 2}},
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
                                      u'storagerouters': {u'10.100.199.171': {u'disks': {u'sda': {u'roles': [u'WRITE',
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
                                                                                                         u'storage_ip': u'10.100.199.171',
                                                                                                         u'storagedriver': {u'cluster_size': 4,
                                                                                                                            u'dtl_mode': u'sync',
                                                                                                                            u'dtl_transport': u'tcp',
                                                                                                                            u'global_write_buffer': 20,
                                                                                                                            u'global_read_buffer': 0,
                                                                                                                            u'deduplication': "non_dedupe",
                                                                                                                            u'strategy': "none",
                                                                                                                            u'sco_size': 4,
                                                                                                                            u'volume_write_buffer': 512}}}},
                                                          u'10.100.199.172': {u'disks': {u'sda': {u'roles': [u'WRITE', u'DTL']},
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
                                                                                                         u'storage_ip': u'10.100.199.172',
                                                                                                         u'storagedriver': {u'cluster_size': 4,
                                                                                                                            u'dtl_mode': u'sync',
                                                                                                                            u'dtl_transport': u'tcp',
                                                                                                                            u'global_write_buffer': 20,
                                                                                                                            u'global_read_buffer': 0,
                                                                                                                            u'deduplication': "non_dedupe",
                                                                                                                            u'strategy': "none",
                                                                                                                            u'sco_size': 4,
                                                                                                                            u'volume_write_buffer': 512}}}},
                                                          u'10.100.199.173': {u'disks': {u'sda': {u'roles': [u'WRITE', u'DTL']},
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
                                                                                                         u'storage_ip': u'10.100.199.173',
                                                                                                         u'storagedriver': {u'cluster_size': 4,
                                                                                                                            u'dtl_mode': u'sync',
                                                                                                                            u'dtl_transport': u'tcp',
                                                                                                                            u'global_write_buffer': 20,
                                                                                                                            u'global_read_buffer': 0,
                                                                                                                            u'deduplication': "non_dedupe",
                                                                                                                            u'strategy': "none",
                                                                                                                            u'sco_size': 4,
                                                                                                                            u'volume_write_buffer': 512}}}}
                                                          }
                                      }
                           }


        self.assertDictEqual(self.generator.get_dict(),expected_output)


if __name__ == '__main__':
    unittest.main()
