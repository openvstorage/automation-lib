# Copyright 2014 iNuron NV
#
# Licensed under the Open vStorage Modified Apache License (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.openvstorage.org/license
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Module for the KVM hypervisor client
"""

from ..apis.kvm.sdk import Sdk


class KVM(object):
    """
    Represents the hypervisor client for KVM
    """

    def __init__(self, ip, username, password):
        """
        Initializes the object with credentials and connection information
        """
        self.sdk = Sdk(ip, username, password)

    def get_state(self, vmid):
        """
        Dummy method
        """
        return self.sdk.get_power_state(vmid)

    def create_vm_from_template(self, name, source_vm, disks, ip, mountpoint, wait=True):
        """
        create vm from template
        TODO:
        storage_ip and mountpoint refer to target Storage Driver
        but on kvm storagedriver.storage_ip is 127.0.0.1
        """
        _ = ip, wait  # For compatibility purposes only
        return self.sdk.create_vm_from_template(name, source_vm, disks, mountpoint)

    def create_vm_from_cloud_init(self, name, vcpus, ram, boot_disk_size, bridge, ip, netmask, gateway, nameserver, amount_disks, size,
                                  mountpoint, cloud_init_url, cloud_init_name, root_password, force=False):
        """
        Create vm from cloud init
        :param name: Name of the vm
        :param vcpus: amount of vcpus
        :param ram: amount of ram (MB)
        :param boot_disk_size: size of the boot disks (notation xGB)
        :param bridge: network bridge name
        :param ip: ip of the vm
        :param netmask: netmask
        :param gateway: gateway
        :param nameserver: dns ip
        :param amount_disks: amount of extra disks
        :param size: size of the extra disks (notation xGB)
        :param mountpoint: where the extra disks should be created
        :param cloud_init_url: cloud init url
        :param cloud_init_name: vmdk template name
        :param root_password: root password of the vm
        :param force: remove vm with the same name or used disks
        :return:
        """
        return self.sdk.create_vm_from_cloud_init(name, vcpus, ram, boot_disk_size, bridge, ip, netmask, gateway, nameserver,
                                                  amount_disks, size, mountpoint, cloud_init_url, cloud_init_name,
                                                  root_password, force)

    def delete_vm(self, vmid, storagedriver_mountpoint=None, storagedriver_storage_ip=None, devicename=None, disks_info=None, wait=True):
        """
        Deletes a given VM and its disks
        """
        _ = wait  # For compatibility purposes only
        _ = storagedriver_mountpoint  # No vpool mountpoint on kvm, use different logic
        _ = storagedriver_storage_ip  # 127.0.0.1 always
        return self.sdk.delete_vm(vmid, devicename)

    def get_vm_agnostic_object(self, vmid):
        """
        Loads a VM and returns a hypervisor agnostic representation
        """
        return self.sdk.make_agnostic_config(self.sdk.get_vm_object(vmid))

    def get_vms_by_nfs_mountinfo(self, ip, mountpoint):
        """
        Gets a list of agnostic vm objects for a given ip and mountpoint
        """
        _ = ip
        vms = []
        for vm in self.sdk.get_vms():
            config = self.sdk.make_agnostic_config(vm)
            if mountpoint in config['datastores']:
                vms.append(config)
        return vms

    def test_connection(self):
        """
        Tests the connection
        """
        return self.sdk.test_connection()

    def is_datastore_available(self, ip, mountpoint):
        """
        Check whether a given datastore is in use on the hypervisor
        """
        _ = ip
        return self.sdk.is_datastore_available(mountpoint)

    def clone_vm(self, vmid, name, disks, mountpoint, wait=False):
        """
        create a clone at vmachine level
        #disks are cloned by VDiskController
        """
        _ = wait, name, disks, mountpoint  # For compatibility purposes only
        return self.sdk.clone_vm(vmid)

    def set_as_template(self, vmid, disks, wait=False):
        """
        Dummy method
        TODO: Not yet implemented, setting an existing kvm guest as template
        """
        _ = vmid, disks, wait  # For compatibility purposes only
        raise NotImplementedError()

    def get_vm_object(self, vmid):
        """
        Dummy method
        """
        return self.sdk.get_vm_object(vmid)

    def get_vm_object_by_devicename(self, devicename, ip, mountpoint):
        """
        devicename = vmachines/template/template.xml # relative to mountpoint
        """
        _ = ip, mountpoint
        return self.sdk.make_agnostic_config(self.sdk.get_vm_object_by_xml(devicename))

    def mount_nfs_datastore(self, name, remote_host, remote_path):
        """
        Dummy method
        """
        raise NotImplementedError()

    def clean_backing_disk_filename(self, path):
        """
        Cleans a backing disk filename to the corresponding disk filename
        """
        _ = self
        return path.strip('/')

    def get_backing_disk_path(self, machinename, devicename):
        """
        Builds the path for the file backing a given device/disk
        """
        return self.get_disk_path(machinename, devicename)

    def get_disk_path(self, machinename, devicename):
        """
        Builds the path for the file backing a given device/disk
        """
        _ = self
        if machinename:
            return '/{}_{}.raw'.format(machinename.replace(' ', '_'), devicename)
        return '/{}.raw'.format(devicename)

    def clean_vmachine_filename(self, path):
        """
        Cleans a VM filename
        """
        _ = self
        return path.strip('/')

    def get_vmachine_path(self, machinename, storagerouter_machineid):
        """
        Builds the path for the file representing a given vmachine
        """
        _ = self
        machinename = machinename.replace(' ', '_')
        return '/{}/{}.xml'.format(storagerouter_machineid, machinename)

    def get_rename_scenario(self, old_name, new_name):
        """
        Gets the rename scenario based on the old and new name
        """
        _ = self
        if old_name.endswith('.xml') and new_name.endswith('.xml'):
            return 'RENAME'
        return 'UNSUPPORTED'

    def should_process(self, devicename, machine_ids=None):
        """
        Checks whether a given device should be processed
        """
        _ = self
        valid = devicename.strip('/') not in ['vmcasts/rss.xml']
        if not valid:
            return False
        if machine_ids is not None:
            return any(machine_id for machine_id in machine_ids if devicename.strip('/').startswith(machine_id))
        return True

    def file_exists(self, storagedriver, devicename):
        """
        Check if devicename exists
        """
        _ = storagedriver
        matches = self.sdk.find_devicename(devicename)
        return matches is not None
