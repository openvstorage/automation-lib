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
Module for the VMware hypervisor client
"""

from ..apis.vmware.sdk import Sdk


class VMware(object):
    """
    Represents the hypervisor client for VMware
    """

    def __init__(self, ip, username, password):
        """
        Initializes the object with credentials and connection information
        """
        self.sdk = Sdk(ip, username, password)
        self.state_mapping = {'poweredOn': 'RUNNING',
                              'poweredOff': 'HALTED',
                              'suspended': 'PAUSED'}

    def get_state(self, vmid):
        """
        Get the current power state of a virtual machine
        @param vmid: hypervisor id of the virtual machine
        """
        return self.state_mapping[self.sdk.get_power_state(vmid)]

    def create_vm_from_template(self, name, source_vm, disks, ip, mountpoint, wait=True):
        """
        Create a new vmachine from an existing template
        """
        task = self.sdk.create_vm_from_template(name, source_vm, disks, ip, mountpoint, wait)
        if wait is True:
            if self.sdk.validate_result(task):
                task_info = self.sdk.get_task_info(task)
                return task_info.info.result.value
        return None

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
        raise NotImplementedError

    def clone_vm(self, vmid, name, disks, mountpoint, wait=False):
        """
        Clone a vmachine

        @param vmid: hypervisor id of the virtual machine
        @param name: name of the virtual machine
        @param disks: list of disk information
        @param wait: wait for action to complete
        @param mountpoint: mountpoint for the vm
        """
        _ = mountpoint
        task = self.sdk.clone_vm(vmid, name, disks, wait)
        if wait is True:
            if self.sdk.validate_result(task):
                task_info = self.sdk.get_task_info(task)
                return task_info.info.result.value
        return None

    def delete_vm(self, vmid, storagedriver_mountpoint, storagedriver_storage_ip, devicename, disks_info=None, wait=False):
        """
        Remove the vmachine from the hypervisor

        @param vmid: hypervisor id of the virtual machine
        @param wait: wait for action to complete
        @param storagedriver_mountpoint: mountpoint of the storagedriver
        @param storagedriver_storage_ip: ip of the storagedriver
        @param devicename: name of the device to delete
        @param disks_info: info of all disks
        """
        if disks_info is None:
            disks_info = []
        _ = disks_info
        self.sdk.delete_vm(vmid, storagedriver_mountpoint, storagedriver_storage_ip, devicename, wait)

    def get_vm_object(self, vmid):
        """
        Gets the VMware virtual machine object from VMware by its identifier
        """
        return self.sdk.get_vm(vmid)

    def get_vm_agnostic_object(self, vmid):
        """
        Gets the VMware virtual machine object from VMware by its identifier
        """
        return self.sdk.make_agnostic_config(self.sdk.get_vm(vmid))

    def get_vm_object_by_devicename(self, devicename, ip, mountpoint):
        """
        Gets the VMware virtual machine object from VMware by devicename
        and datastore identifiers
        """
        return self.sdk.make_agnostic_config(self.sdk.get_nfs_datastore_object(ip, mountpoint, devicename)[0])

    def get_vms_by_nfs_mountinfo(self, ip, mountpoint):
        """
        Gets a list of agnostic vm objects for a given ip and mountpoint
        """
        for vm in self.sdk.get_vms(ip, mountpoint):
            yield self.sdk.make_agnostic_config(vm)

    def is_datastore_available(self, ip, mountpoint):
        """
        @param ip : hypervisor ip to query for datastore presence
        @param mountpoint: nfs mountpoint on hypervisor
        @rtype: boolean
        @return: True | False
        """
        return self.sdk.is_datastore_available(ip, mountpoint)

    def set_as_template(self, vmid, disks, wait=False):
        """
        Configure a vm as template
        This lets the machine exist on the hypervisor but configures
        all disks as "Independent Non-persistent"
        @param wait: wait for action to complete
        @param vmid: hypervisor id of the virtual machine
        @param disks: disks to include in the template
        """
        return self.sdk.set_disk_mode(vmid, disks, 'independent_nonpersistent', wait)

    def mount_nfs_datastore(self, name, remote_host, remote_path):
        """
        Mounts a given NFS export as a datastore
        """
        return self.sdk.mount_nfs_datastore(name, remote_host, remote_path)

    def test_connection(self):
        """
        Checks whether this node is a vCenter
        """
        return self.sdk.test_connection()

    def clean_backing_disk_filename(self, path):
        """
        Cleans a backing disk filename to the corresponding disk filename
        """
        _ = self
        return path.replace('-flat.vmdk', '.vmdk').strip('/')

    def get_backing_disk_path(self, machinename, devicename):
        """
        Builds the path for the file backing a given device/disk
        """
        _ = self
        if machinename is None:
            return '/{0}-flat.vmdk'.format(devicename)
        return '/{0}/{1}-flat.vmdk'.format(machinename.replace(' ', '_'), devicename)

    def get_disk_path(self, machinename, devicename):
        """
        Builds the path for the file backing a given device/disk
        """
        _ = self
        if machinename is None:
            return '/{0}.vmdk'.format(devicename)
        return '/{0}/{1}.vmdk'.format(machinename.replace(' ', '_'), devicename)

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
        _ = self, storagerouter_machineid  # For compatibility purposes only
        machinename = machinename.replace(' ', '_')
        return '/{0}/{1}.vmx'.format(machinename, machinename)

    def get_rename_scenario(self, old_name, new_name):
        """
        Gets the rename scenario based on the old and new name
        """
        _ = self
        if old_name.endswith('.vmx') and new_name.endswith('.vmx'):
            return 'RENAME'
        elif old_name.endswith('.vmx~') and new_name.endswith('.vmx'):
            return 'UPDATE'
        return 'UNSUPPORTED'

    def should_process(self, devicename, machine_ids=None):
        """
        Checks whether a given device should be processed
        """
        _ = self, devicename, machine_ids
        return True

    def file_exists(self, storagedriver, devicename):
        """
        Check if devicename exists on the given vpool
        """
        return self.sdk.file_exists(storagedriver.storage_ip,
                                    storagedriver.mountpoint,
                                    self.clean_vmachine_filename(devicename))
