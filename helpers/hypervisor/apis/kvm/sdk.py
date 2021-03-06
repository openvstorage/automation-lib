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
This module contains all code for using the KVM libvirt api
"""

import subprocess
import os
import re
import glob
import uuid
import libvirt
from ovs.extensions.generic.logger import Logger
from ovs.extensions.generic.sshclient import SSHClient
from ovs.extensions.generic.system import System
from ovs_extensions.generic.toolbox import ExtensionsToolbox
from xml.etree import ElementTree
from xml.etree.ElementTree import Element
# Relative
from option_mapping import SdkOptionMapping

logger = Logger('helpers-kvm_sdk')
ROOT_PATH = '/etc/libvirt/qemu/'  # Get static info from here, or use dom.XMLDesc(0)
RUN_PATH = '/var/run/libvirt/qemu/'  # Get live info from here


# Helpers
def _recurse(treeitem):
    result = {}
    for key, item in treeitem.items():
        result[key] = item
    for child in treeitem.getchildren():
        result[child.tag] = _recurse(child)
        for key, item in child.items():
            result[child.tag][key] = item
        result[child.tag]['<text>'] = child.text
    return result


def authenticated(func):
    """
    Decorator that make sure all required calls are running onto a connected SDK
    """
    def wrapper(self, *args, **kwargs):
        self.__doc__ = func.__doc__
        # determine if connection isn't closed.
        try:
            self._conn = self.connect(self.login, self.host)
        except:
            try:
                self.disconnect(self._conn)
            except:
                pass
            raise
        return func(self, *args, **kwargs)
    return wrapper


class Sdk(object):
    """
    This class contains all SDK related methods
    """

    def __init__(self, host='127.0.0.1', login='root', passwd=None):
        logger.debug('Init libvirt')
        self.states = {
            libvirt.VIR_DOMAIN_NOSTATE: 'NO STATE',
            libvirt.VIR_DOMAIN_RUNNING: 'RUNNING',
            libvirt.VIR_DOMAIN_BLOCKED: 'BLOCKED',
            libvirt.VIR_DOMAIN_PAUSED: 'PAUSED',
            libvirt.VIR_DOMAIN_SHUTDOWN: 'SHUTDOWN',
            libvirt.VIR_DOMAIN_SHUTOFF: 'TURNEDOFF',
            libvirt.VIR_DOMAIN_CRASHED: 'CRASHED'
        }
        pattern = re.compile(r"^(?<!\S)((\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])\b|\.\b){7}(?!\S)$")
        if pattern.match(host):
            self.host = host
        else:
            raise ValueError("{0} is not a valid ip.".format(host))
        self.host = host
        self.login = login
        self.streams = {}
        self.ssh_client = SSHClient(host, username=login, password=passwd)
        self._conn = self.connect(login, host)
        # Enable event registering
        libvirt.virEventRegisterDefaultImpl()
        logger.debug('Init complete')

    def __del__(self):
        """
        Class destructor
        :return:
        """
        try:
            self.disconnect(self._conn)
        except Exception:
            # Absord destructor exceptions
            pass
        pass

    def test_connection(self):
        pass

    def connect(self, login=None, host=None):
        """
        Connects to a kvm hypervisor
        :param login: username
        :param host: ip
        :return: connection object
        """
        _ = self
        logger.debug('Init connection: {0}, {1}, {2}, {3}'.format(host, login, os.getgid(), os.getuid()))
        try:
            if login == '127.0.0.1':
                conn = libvirt.open('qemu:///system')
            else:
                conn = libvirt.open('qemu+ssh://{0}@{1}/system'.format(login, host))
        except libvirt.libvirtError as le:
            logger.error('Error during connect: %s (%s)', str(le), le.get_error_code())
            raise
        return conn

    def disconnect(self, conn=None):
        """
        Disconnects a given connection
        :param conn: connection to disconnect
        :return:
        """
        _ = self
        logger.debug('Disconnecting libvirt')
        if conn:
            try:
                conn.close()
            except libvirt.libvirtError as le:
                # Ignore error, connection might be already closed
                logger.error('Error during disconnect: {0} ({1})'.format(str(le), le.get_error_code()))
        return None

    @staticmethod
    def _get_disks(vm_object):
        """
        Get the disks of the object as dict
        :param vm_object: object representing a vm
        :type vm_object: libvirt.virDomain
        :return: dict of diskinfo
        :rtype: dict
        """
        tree = ElementTree.fromstring(vm_object.XMLDesc(0))
        return [_recurse(item) for item in tree.findall('devices/disk')]

    @staticmethod
    def _get_nics(vm_object):
        """
        Get the disks of the object as dict
        :param vm_object: object representing a vm
        :type vm_object: libvirt.virDomain
        :return: dict of nics
        :rtype: dict
        """
        tree = ElementTree.fromstring(vm_object.XMLDesc(0))
        return [_recurse(item) for item in tree.findall('devices/interface')]

    @staticmethod
    def _get_nova_name(vm_object):
        """
        Get the disks of the object as dict
        :param vm_object: object representing a vm
        :type vm_object: libvirt.virDomain
        :return: dict of ...
        :rtype: dict
        """
        tree = ElementTree.fromstring(vm_object.XMLDesc(0))
        metadata = tree.findall('metadata')[0]
        nova_instance_namespace_tag = metadata.getchildren()[0].tag
        nova_instance_namespace = nova_instance_namespace_tag[nova_instance_namespace_tag.find('{') + 1:nova_instance_namespace_tag.find('}')]
        instance = metadata.findall('{%s}instance' % nova_instance_namespace)[0]
        name = instance.findall('{%s}name' % nova_instance_namespace)[0]
        return name.text

    @staticmethod
    def _get_ram(vm_object):
        """
        Get the RAM size of the VM
        :param vm_object: VirDomain istance
        :return RAM of the VM
        """
        tree = ElementTree.fromstring(vm_object.XMLDesc(0))
        mem = tree.findall('memory')[0]
        unit = mem.items()[0][1]
        value = mem.text
        if unit == 'MiB':
            return int(value)
        elif unit == 'KiB':
            return int(value) / 1024
        elif unit == 'GiB':
            return int(value) * 1024

    def _get_disk_size(self, filename):
        """
        Gets the size of the disk
        :param filename: path to the disk
        :return: size
        """
        cmd = ['qemu-img', 'info', filename]
        try:
            out = self.ssh_client.run(' '.join(cmd), stderr=subprocess.STDOUT, shell=True)
            for line in out.split('\n'):
                if line.startswith('virtual size: '):
                    size = line.split('virtual size: ')[1].split(' ')[0]
                    return size
        except subprocess.CalledProcessError as ex:
            logger.error('Could not fetch disk size for {0}. Got {1}'.format(filename, str(ex)))
            raise

    def _get_vm_pid(self, vm_object):
        """
        Get the PID of the KVM process running the given machine
        :param vm_object: vm identifier
        :return PID of the KVM process
        """
        if self.get_power_state(vm_object.name()) == 'RUNNING':
            pid_path = '{0}/{1}.pid'.format(RUN_PATH, vm_object.name())
            try:
                with open(pid_path, 'r') as pid_file:
                    pid = pid_file.read()
                return int(pid)
            except IOError:
                # vMachine is running but no run file?
                return '-1'
        return '-2'  # No pid, machine is halted

    def make_agnostic_config(self, vm_object):
        """
        return an agnostic config (no hypervisor specific type or structure)
        """
        regex = '/mnt/([^/]+)/(.+$)'
        config = {'disks': []}
        mountpoints = []

        order = 0
        for disk in Sdk._get_disks(vm_object):
            # Skip cdrom/iso
            if disk['device'] == 'cdrom':
                continue

            # Load backing filename
            if 'file' in disk['source']:
                backingfilename = disk['source']['file']
            elif 'dev' in disk['source']:
                backingfilename = disk['source']['dev']
            else:
                continue
            match = re.search(regex, backingfilename)
            if match is None:
                continue

            # Cleaning up
            mountpoint = '/mnt/{0}'.format(match.group(1))
            filename = backingfilename.replace(mountpoint, '').strip('/')
            diskname = filename.split('/')[-1].split('.')[0]

            # Collecting data
            config['disks'].append({'filename': filename,
                                    'backingfilename': filename,
                                    'datastore': mountpoint,
                                    'name': diskname,
                                    'order': order})
            order += 1
            mountpoints.append(mountpoint)

        vm_filename = self.ssh_client.run("grep -l '<uuid>{0}</uuid>' {1}*.xml".format(vm_object.UUIDString(), ROOT_PATH))
        vm_filename = vm_filename.strip().split('/')[-1]
        vm_location = System.get_my_machine_id(self.ssh_client)
        vm_datastore = None
        possible_datastores = self.ssh_client.run("find /mnt -name '{0}'".format(vm_filename)).split('\n')
        for datastore in possible_datastores:
            # Filter results so only the correct machineid/xml combinations are left over
            if '{0}/{1}'.format(vm_location, vm_filename) in datastore.strip():
                for mountpoint in mountpoints:
                    if mountpoint in datastore.strip():
                        vm_datastore = mountpoint

        try:
            config['name'] = self._get_nova_name(vm_object)
        except Exception as ex:
            logger.debug('Cannot retrieve nova:name {0}'.format(ex))
            # not an error, as we have a fallback, but still keep logging for debug purposes
            config['name'] = vm_object.name()
        config['id'] = str(vm_object.UUIDString())
        config['backing'] = {'filename': '{0}/{1}'.format(vm_location, vm_filename),
                             'datastore': vm_datastore}
        config['datastores'] = dict((mountpoint, '{}:{}'.format(self.host, mountpoint)) for mountpoint in mountpoints)

        return config

    def get_power_state(self, vmid, readable=True):
        """
        Get the machine power state
        :param vmid: vm identifier
        :param readable: return human readable
        :return power state of the vm
        """
        if not isinstance(vmid, libvirt.virDomain):
            vmid = self.get_vm_object(vmid)
        if readable is True:
            return self.states.get(vmid.info()[0], 'UNKNOWN')
        else:
            return vmid.info()[0]

    @authenticated
    def get_vm_object(self, vmid):
        """
        return virDomain object representing virtual machine
        vmid is the name or the uuid
        cannot use ID, since for a stopped vm id is always -1
        """
        try:
            uuid.UUID(vmid)
            is_uuid = True
        except ValueError:
            # not a uuid
            is_uuid = False
        try:
            if is_uuid is True:
                return self._conn.lookupByUUIDString(vmid)
            else:
                return self._conn.lookupByName(vmid)
        except libvirt.libvirtError as ex:
            logger.error(str(ex))
            raise RuntimeError('Virtual Machine with id/name {0} could not be found. Got {1}'.format(vmid, str(ex)))

    def get_vm_object_by_xml(self, filename):
        """
        get vm based on filename: vmachines/template/template.xml
        :param filename: name of the xml
        :return VirDomain object
        """
        vmid = filename.split('/')[-1].replace('.xml', '')
        return self.get_vm_object(vmid)

    def get_vms(self):
        """
        Get all VirDomain objects
        :return list of all virDomain objects
        """
        return self._conn.listAllDomains()

    def shutdown(self, vmid):
        """
        Shuts down a virtual machine
        :param vmid: vm identifier
        :return:
        """
        if not isinstance(vmid, libvirt.virDomain):
            vmid = self.get_vm_object(vmid)
        result = vmid.shutdown()
        if result != 0:
            raise RuntimeError("Shutting down VM failed")
        return self.get_power_state(vmid)

    def destroy(self, vmid):
        """
        Forces a shutdown of a virtual machine
        :param vmid: vm identifier
        :return:
        """
        if not isinstance(vmid, libvirt.virDomain):
            vmid = self.get_vm_object(vmid)
        result = vmid.destroy()
        if result != 0:
            raise RuntimeError("Destroying VM failed")
        return self.get_power_state(vmid)

    def undefine(self, vmid):
        """
        Undefines a virtual machine
        :param vmid: vm identifier
        :return:
        """
        if not isinstance(vmid, libvirt.virDomain):
            vmid = self.get_vm_object(vmid)
        result = vmid.undefine()
        if result != 0:
            raise RuntimeError("Undefining VM failed")
        else:
            return True

    def delete_vm(self, vmid, delete_disks=False):
        """
        Delete domain from libvirt and try to delete all files from vpool (xml, .raw)
        :param vmid: id of the vm. Could also be the name
        :param delete_disks: do the disks need to be deleted or not
        :return:
        """
        if not isinstance(vmid, libvirt.virDomain):
            vmid = self.get_vm_object(vmid)
        xml = vmid.XMLDesc()
        try:
            if self.get_power_state(vmid) == "RUNNING":
                logger.info("Shutting down {0}".format(vmid))
                self.destroy(vmid)
            self.undefine(vmid)
        except RuntimeError as ex:
            raise RuntimeError("Deleting VM {0} has failed. Got {1}".format(vmid.name, str(ex)))
        if delete_disks is True:
            tree = ElementTree.ElementTree(ElementTree.fromstring(xml))
            root = tree.getroot()
            for element in root.findall('devices/disk'):
                disk_path = element.find('source').attrib.get("file")
                self.ssh_client.file_delete(disk_path)
        return True

    def power_on(self, vmid):
        """
        Powers on a libvirt domain
        :param vmid: id or name of the domain
        :return: powerstate of the vm
        """
        if not isinstance(vmid, libvirt.virDomain):
            vmid = self.get_vm_object(vmid)
        vmid.create()
        return self.get_power_state(vmid)

    def find_devicename(self, devicename):
        """
        Searched for a given devicename
        :param devicename: name of the device
        """
        _ = self
        file_matcher = '/mnt/*/{0}'.format(devicename)
        matches = []
        for found_file in glob.glob(file_matcher):
            if os.path.exists(found_file) and os.path.isfile(found_file):
                matches.append(found_file)
        return matches if matches else None

    def is_datastore_available(self, mountpoint):
        if self.ssh_client is None:
            self.ssh_client = SSHClient(self.host, username='root')
        return self.ssh_client.run("[ -d {0} ] && echo 'yes' || echo 'no'".format(mountpoint)) == 'yes'

    def clone_vm(self, vmid, name=None, mountpoint=None, diskname=None):
        """
        Clones an existing vm
        Will rename the vm to vmname-clone
        Will clone the disks with -clone and if necessary an identifier
        :param vmid: identifier of the vm
        :param name: new name for the vm
        :param mountpoint: location for the new disks
        :param diskname: new name for the disk
        """
        if not isinstance(vmid, libvirt.virDomain):
            vmid = self.get_vm_object(vmid)
        if self.get_power_state(vmid) == "RUNNING":
            logger.info("Shutting down {0}".format(vmid))
            self.destroy(vmid)
        command = ["virt-clone"]
        options = [
            "--original {}".format(vmid.name()),
        ]
        if mountpoint is None and name is None and diskname is None:
            options.append("--auto-clone")
        else:
            # Cannot rely on autoclone to generate anything, generate manually
            for disk in self._get_disks(vmid):
                options.append("--file {0}".format(self._generate_disk_clone_name(disk["source"]["file"], mountpoint, diskname)))
            if name is None:
                vm_name = self._generate_vm_clone_name(vmid.name())
            else:
                vm_name = self._generate_vm_clone_name(name, True)
            options.append("--name {0}".format(vm_name))
        cmd = self.shell_safe(" ".join(command + options))
        try:
            logger.info("Cloning vm {0} with command {1}".format(name, cmd))
            self.ssh_client.run(cmd, allow_insecure=True)
            logger.info("Cloning vm {0} has finished.".format(name, cmd))
        except subprocess.CalledProcessError as ex:
            raise RuntimeError('Could not clone {0}. VM state was {1} when error: {2} rose.'.format(vmid, str(ex), self.get_power_state(vmid)))

    @authenticated
    def _generate_vm_clone_name(self, name, specified_name=False, tries=0):
        """
        Generates a name for a vmclone. If the name is already in use, it will append a integer value
        :param name: name of the vm or the wanted name
        :param specified_name: true if the name is the wanted name
        :param tries: keep track of how many attempts there were to create the name
        :return:
        """
        if specified_name is True:
            try:
                self._conn.lookupByName(name)
                raise AssertionError("Name {0} is currently in use by another VM.".format(name))
            except AssertionError as ex:
                raise RuntimeError(str(ex))
            except libvirt.libvirtError:
                return name
        else:
            if tries == 0:
                name = "{0}-clone".format(name)
            else:
                name = "{0}-clone{1}".format(name, tries)
            try:
                self._conn.lookupByName(name)
                return self._generate_vm_clone_name(name, False, tries + 1)
            except libvirt.libvirtError:
                return name

    @staticmethod
    def _generate_disk_clone_name(path, mountpoint=None, diskname=None, tries=0):
        # If the specified name if not available, raise
        should_raise = True
        if diskname is None:
            should_raise = False
            diskname = '{0}-clone.{1}'.format(path.split('/')[-1].rsplit('.', 1)[0], path.split('/')[-1].rsplit('.', 1)[1])
        if mountpoint is None:
            # use same location
            mountpoint = "/{0}/".format(path.rsplit('/', 1)[0].strip("/"))
        else:
            mountpoint = "/{0}/".format(mountpoint.strip("/"))
        loc = "{0}{1}".format(mountpoint, diskname)
        if os.path.exists(loc):
            if should_raise:
                raise RuntimeError("{0} could not be used as disks path. The name is already in use.".format(loc))
            else:
                return Sdk._generate_disk_clone_name(path, mountpoint, "{0}{1}.{2}".format(diskname.split('.', 1)[0],
                                                                                           tries + 1,
                                                                                           diskname.rsplit('.', 1)[1]))
        else:
            logger.info("Would generate {0} for {1} its clone".format(loc, path))
            return loc

    def create_vm_from_template(self, name, source_vm, disks, mountpoint):
        """
        Create a vm based on an existing template on specified hypervisor
        :param name: name of the vm to be created
        :param source_vm: vm object of the source
        :param disks: list of dicts (agnostic) eg. {'diskguid': new_disk.guid, 'name': new_disk.name, 'backingdevice': device_location.strip('/')}
        :param mountpoint: location for the vm
         kvm doesn't have datastores, all files should be in /mnt/vpool_x/name/ and shared between nodes
         to "migrate" a kvm machine just symlink the xml on another node and use virsh define name.xml to reimport it
         (assuming that the vpool is in the same location)
        :return:
        """

        vm_disks = []

        # Get agnostic config of source vm
        if hasattr(source_vm, 'config'):
            vcpus = source_vm.config.hardware.numCPU
            ram = source_vm.config.hardware.memoryMB
        elif isinstance(source_vm, libvirt.virDomain):
            vcpus = source_vm.info()[3]
            ram = Sdk._get_ram(source_vm)
        else:
            raise ValueError('Unexpected object type {} {}'.format(source_vm, type(source_vm)))

        # Get nics of source ram - for now only KVM
        networks = []
        for nic in Sdk._get_nics(source_vm):
            if nic.get('type', None) == 'network':
                source = nic.get('source', {}).get('network', 'default')
                model = nic.get('model', {}).get('type', 'e1000')
                networks.append(('network={0}'.format(source), 'mac=RANDOM', 'model={0}'.format(model)))
                # MAC is always RANDOM

        # Assume disks are raw
        for disk in disks:
            vm_disks.append(('/{}/{}'.format(mountpoint.strip('/'), disk['backingdevice'].strip('/')), 'virtio'))

        self.create_vm(name=name, vcpus=vcpus, ram=int(ram), disks=vm_disks, networks=networks)

        try:
            return self.get_vm_object(name).UUIDString()
        except libvirt.libvirtError as le:
            logger.error(str(le))
            try:
                return self.get_vm_object(name).UUIDString()
            except libvirt.libvirtError as le:
                logger.error(str(le))
                raise RuntimeError('Virtual Machine with id/name {} could not be found.'.format(name))

    @authenticated
    def create_vm(self, name, vcpus, ram, disks, cdrom_iso=None, os_type=None, os_variant=None, vnc_listen='0.0.0.0',
                  networks=None, start=False, autostart=False, edge_configuration=None):
        """
        Creates a VM
        @TODO use Edge instead of fuse for disks
        :param name: name of the vm
        :param vcpus: number of cpus
        :param ram: number of ram (MB)
        :param disks: list of dicts : options see SdkOptionsMapping
        when using existing storage, size can be removed
        :param cdrom_iso: path to the iso the mount
        :param autostart: start vm when the hypervisor starts
        :param edge_configuration: virtual machine setup for ovs with edge configuration
        :param os_type: type of os
        :param os_variant: variant of the os
        :param vnc_listen:
        :param networks: lists of tuples : ("network=default", "mac=RANDOM" or a valid mac, "model=e1000" (any model for vmachines)
        :param start: start the guest after creation
        :return:
        """
        try:
            self._conn.lookupByName(name)
            raise AssertionError('Name {0} is currently in use by another VM.'.format(name))
        except AssertionError as ex:
            raise RuntimeError(str(ex))
        except libvirt.libvirtError:
            pass

        ovs_vm = False
        if edge_configuration is not None:
            required_edge_params = {'port': (int, {'min': 1, 'max': 65535}),
                                    'protocol': (str, ['tcp', 'udp', 'rdma']),
                                    'hostname': (str, None),
                                    'username': (str, None, False),
                                    'password': (str, None, False)}
            ExtensionsToolbox.verify_required_params(required_edge_params, edge_configuration)
            ovs_vm = True
        command = ['virt-install']
        options = ['--connect=qemu+ssh://{0}@{1}/system'.format(self.login, self.host),
                   '--name={0}'.format(name),
                   '--vcpus={0}'.format(vcpus),
                   '--ram={0}'.format(ram),
                   '--graphics=vnc,listen={0}'.format(vnc_listen),  # Have to specify 0.0.0.0 else it will listen on 127.0.0.1 only
                   '--noautoconsole',
                   '--print-xml=1']

        if cdrom_iso is None:
            options.append('--import')
        else:
            options.append('--cdrom={0}'.format(cdrom_iso))
        for disk in disks:
            options.append('--disk={}'.format(self._extract_command(disk, SdkOptionMapping.disk_options_mapping)))
        if os_type is not None:
            if os_type not in SdkOptionMapping.optype_options:
                raise ValueError('Ostype {0} is not supported'.format(os_type))
            options.append('--os-type={0}'.format(os_type))
        if os_variant is not None:
            options.append('--os-variant={0}'.format(os_variant))
        if networks is None or networks == []:
            options.append('--network=none')
        if autostart is True:
            options.append('--autostart')
        if edge_configuration is True:
            options.append('--dry-run')
        else:
            for network in networks:
                options.append('--network={0}'.format(self._extract_command(network, SdkOptionMapping.network_option_mapping)))
        try:
            logger.info('Creating vm {0} with command {1}'.format(name, ' '.join(command + options)))
            vm_xml = self.ssh_client.run(command + options)
            if ovs_vm is True:
                vm_xml = self._update_xml_for_ovs(vm_xml, edge_configuration)
            self._conn.defineXML(vm_xml)
            if start is True:
                self.power_on(name)
            logger.info('Vm {0} has been created.'.format(name))
        except subprocess.CalledProcessError as ex:
            msg = 'Error during creation of VM. Got {0}'.format(str(ex))
            logger.exception(msg)
            print ' '.join(command+options)
            raise RuntimeError(msg)

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

        template_directory = '/var/lib/libvirt/images'
        vmdk_file = "{0}/{1}.vmdk".format(template_directory, cloud_init_name)
        qcow_file = "{0}/{1}.qcow2".format(template_directory, cloud_init_name)
        # Check if cloud_init already exists if not download vmdk
        if not self.ssh_client.file_exists(vmdk_file):
            self.ssh_client.run(["wget", "-O", vmdk_file, cloud_init_url])

        if not self.ssh_client.file_exists(qcow_file):
            self.ssh_client.run(["qemu-img", "convert", "-O", "qcow2", vmdk_file, qcow_file])

        vm_directory = "{0}/{1}".format(template_directory, name)
        user_data = "{0}/user-data".format(vm_directory)
        meta_data = "{0}/meta-data".format(vm_directory)
        ci_iso = "{0}/{1}.iso".format(vm_directory, name)
        boot_disk = "{0}/{1}.qcow2".format(vm_directory, name)

        meta_data_lines = [
            'instance-id: {0}'.format(uuid.uuid1()),
            'local-hostname: {0}'.format(name),
            'network-interfaces: |',
            '  auto ens3',
            '  iface ens3 inet static',
            '  address {0}'.format(ip),
            '  netmask {0}'.format(netmask),
            '  gateway {0}'.format(gateway),
            'manage_resolve_conf: True',
            'resolv_conf:',
            '  nameservers:[{0}]'.format(nameserver),
            ''
        ]

        user_data_lines = [
            '#cloud-config',
            'hostname: {0}'.format(name),
            'manage_etc_hosts: True',
            'disable_root: False',
            'password: {0}'.format(root_password),
            'ssh_pwauth: True',
            'chpasswd:',
            '  list: |',
            '    root:{0}'.format(root_password),
            '    ubuntu:{0}'.format(root_password),
            '  expire: False',
            'runcmd:',
            '  - [sed, -ie, "s/PermitRootLogin prohibit-password/PermitRootLogin yes/", /etc/ssh/sshd_config]',
            '  - [sed, -ie, "s/PasswordAuthentication no/PasswordAuthentication yes/", /etc/ssh/sshd_config]',
            '  - [service, ssh, restart]',
            ''
        ]

        # Check if vm already exists with this name
        vm = None

        try:
            vm = self._conn.lookupByName(name)
        except libvirt.libvirtError:
            pass

        if vm and force:
            self.delete_vm(vm, True)
        elif vm and not force:
            raise Exception('VM {0} is still defined on this hypervisor. Use the force=True option to delete.'.format(name))

        if self.ssh_client.dir_exists(vm_directory):
            exists, used_disk, vm_name = self._check_disks_in_use([ci_iso, boot_disk])
            if exists:
                raise Exception("Virtual Disk {0} in used by {1}".format(used_disk, vm_name))

            self.ssh_client.dir_delete(vm_directory)

        self.ssh_client.dir_create(vm_directory)
        # Copy template image
        self.ssh_client.run(["cp", qcow_file, boot_disk])

        # Resize image
        self.ssh_client.run(["qemu-img", "resize", boot_disk, boot_disk_size])

        # Create metadata and user data file
        self.ssh_client.file_write(meta_data, '\n'.join(meta_data_lines))

        self.ssh_client.file_write(user_data, '\n'.join(user_data_lines))

        # Generate iso for cloud-init
        self.ssh_client.run(["genisoimage", "-output", ci_iso, "-volid", "cidata", "-joliet", "-r", user_data, meta_data])

        # Create extra disks
        all_disks = [{'mountpoint': boot_disk, "format": "qcow2", "bus": "virtio"}]

        if amount_disks > 0 and size > 0:
            if not self.ssh_client.dir_exists(mountpoint):
                raise Exception("Directory {0} doesn't exists.".format(mountpoint))

            for i in xrange(1, amount_disks+1):
                disk_path = "{0}/{1}_{2:02d}.qcow2".format(mountpoint, name, i,)
                exists, used_disk, vm_name = self._check_disks_in_use([disk_path])
                disk_exists_filesystem = self.ssh_client.file_exists(disk_path)
                if disk_exists_filesystem and exists:
                    raise Exception("Virtual Disk {0} in used by {1}".format(used_disk, vm_name))
                elif disk_exists_filesystem:
                    self.ssh_client.file_delete(disk_path)

                self.ssh_client.run(['qemu-img', 'create', '-f', 'qcow2', disk_path, size])
                all_disks.append({'mountpoint': disk_path, "format": "qcow2", "bus": "virtio"})

        self.create_vm(name=name, vcpus=vcpus, ram=ram, disks=all_disks, cdrom_iso=ci_iso,
                       networks=[{"bridge": bridge, "model": "virtio"}], start=True)

    def _check_disks_in_use(self, disk_paths):
        """
        Check if disks are in used
        :param disks: list of disk paths
        :type disks: list
        :return: bool
        """
        for dom in self.get_vms():
            dom_info = ElementTree.fromstring(dom.XMLDesc(0))
            disks = dom_info.findall('.//disk')
            for disk in disks:
                if disk.find('source') is None:
                    continue
                used_disk = disk.find('source').get('file')
                if used_disk in disk_paths:
                    try:
                        return True, used_disk, dom_info.find('name').text
                    except AttributeError as ex:
                        msg = "Error during checking of VM's disks. Got {0}".format(str(ex))
                        logger.exception(msg)
                        return True, used_disk, 'Unknown vm name'

        return False, '', ''

    @staticmethod
    def _update_xml_for_ovs(xml, edge_configuration):
        """
        Update the xml to use OVS protocol and use the edge
        :param xml: xml to base upon
        :param edge_configuration: configuration details for the edge
        :return:
        """
        logger.info('Changing XML to use OVS protocol.')
        tree = ElementTree.ElementTree(ElementTree.fromstring(xml))
        root = tree.getroot()
        for element in root.findall('devices/disk'):
            # update type to network instead of file
            element.attrib.update({'type': 'network'})
            # update driver
            driver_update = {'cache': 'none',
                             'io': 'threads'}
            element.find('driver').attrib.update(driver_update)
            # Change source to (vdisk without .raw)
            source_element = element.find('source')
            user_config = {}
            if edge_configuration.get('username') and edge_configuration.get('password'):
                user_config = {'username': edge_configuration['username'], 'passwd': edge_configuration['password']}
            source = {'protocol': 'openvstorage',
                      'name': source_element.attrib.get('file').rsplit('/', 1)[1].rsplit('.', 1)[0]
                      if source_element.attrib.get('file') is not None else source_element.attrib.get('name'),
                      'snapshot-timeout': '120'}
            source.update(user_config)
            source_element.attrib = source
            # Add a new element under source with edge port and hostname pointermds-regression-000
            element_attribute = {'name': edge_configuration['hostname'], 'port': str(edge_configuration['port'])}
            if len(source_element.getchildren()) == 0:
                e = Element(tag='host', attrib=element_attribute)
                source_element.insert(0, e)
            else:
                source_element.find('host').attrib = element_attribute
                # Change address attrib
        logger.info('Xml change completed.')
        return ElementTree.tostring(root)

    @staticmethod
    def _extract_command(option, mapping):
        """
        Creates a command string based on options and a mapping
        :param option: all options
        :param mapping: mapping for the options
        :return: command string
        :rtype: str
        """
        opts = {}
        cmd = []
        # Create a mapping with defaults
        for key, config in mapping.iteritems():
            value = option.get(key, config.get('default'))
            if value is None:
                continue
            else:
                if config['values'] is None:
                    if type(value) == config['type']:
                        opts[config['option']] = value
                    else:
                        raise ValueError('Type does not match. Expected {0} and got {1} for option {2}'.format(config['type'], type(value), key))
                else:
                    if value in config['values'] and len(config['values']) > 0:
                        opts[config['option']] = value
                    else:
                        raise ValueError(
                            'Value does not match. Expected {0} and got {1} for option {2}'.format(config['type'], type(value), key))
        # Generate options to append to the command
        for key, value in opts.iteritems():
            cmd.append("{0}={1}".format(key, value))
        return "{0}".format(",".join(cmd))

    @authenticated
    def migrate(self, vmid, d_ip, d_login, flags=None, bandwidth=0):
        """
        Live migrates a vm by default
        :param vmid: identifier of the vm to migrate (name or id)
        :param d_ip: ip of the destination hypervisor
        :param d_login: login of the destination hypervisor
        :param flags: Flags to supply, binary of libvirt migrate flags
        :param bandwidth: limit the bandwith to MB/s
        :return:
        """
        if flags is None:
            flags = libvirt.VIR_MIGRATE_LIVE + libvirt.VIR_MIGRATE_UNDEFINE_SOURCE + libvirt.VIR_MIGRATE_PERSIST_DEST
        vm = self.get_vm_object(vmid)
        dconn = self.connect(login=d_login, host=d_ip)
        if dconn is None:
            raise RuntimeError("Could not connect to {0}".format(d_ip))
        try:
            dom = vm.migrate(dconn=dconn, flags=flags, bandwidth=bandwidth)
            if dom is None:
                raise RuntimeError("Could not migrate the VM to {0}".format(d_ip))
        except libvirt.libvirtError as ex:
            raise RuntimeError("Could not migrate the VM to {0}. Got '{1}'".format(d_ip, str(ex)))

    @authenticated
    def get_guest_ip_addresses(self, vmid, source=libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_LEASE):
        """
        Returns the IP given by the network lease
        :param vmid: identifier of the vm to migrate (name or id)
        :param source: source to base off from
        :return: a list with all ip addresses
        """
        if not isinstance(vmid, libvirt.virDomain):
            vmid = self.get_vm_object(vmid)
        results = []
        # Example output {'vnet0': {'hwaddr': '52:54:00:c0:a9:19', 'addrs': [{'prefix': 24, 'type': 0, 'addr': '192.168.122.214'}]}}
        for interface, interface_info in vmid.interfaceAddresses(source).iteritems():
            for ip_info in interface_info.get("addrs"):
                results.append(ip_info.get("addr"))
        return results

    @authenticated
    def create_snapshot(self, vmid, snapshot_name, flags=0):
        """
        Creates a snapshot for a VM with a specfic name
        :param vmid: identifier of the vm to migrate (name or id)
        :param snapshot_name: name of the snapshot
        :param flags: extra flags supplied
        :return:
        """
        if not isinstance(vmid, libvirt.virDomain):
            vmid = self.get_vm_object(vmid)
        # Generate the snapshot xml
        snapshot_xml = "<domainsnapshot><name>{0}</name></domainsnapshot>".format(snapshot_name)
        vmid.snapshotCreateXML(snapshot_xml, flags)

    @authenticated
    def revert_to_snapshot(self, vmid, snapshot_name, flags=0):
        """
        Reverts to a specific snapshot
        :param vmid: identifier of the vm to migrate (name or id)
        :param snapshot_name: name of the snapshot
        :param flags: extra flags supplied
        :return:
        """
        if not isinstance(vmid, libvirt.virDomain):
            vmid = self.get_vm_object(vmid)
        snapshot = vmid.snapshotLookupByName(snapshot_name)
        vmid.revertToSnapshot(snapshot, flags)

    @staticmethod
    def shell_safe(argument):
        """
        Makes sure that the given path/string is escaped and safe for shell
        :param argument: Argument to make safe for shell
        """
        return "{0}".format(argument.replace(r"'", r"'\''"))

    @authenticated
    def eject_cd(self, vmid, target='all', flags=None):
        """
        :param vmid: identifier of the vm
        :param target: cd to target
        :param flags: extra flags
        :return:
        """
        if not isinstance(vmid, libvirt.virDomain):
            vmid = self.get_vm_object(vmid)
        if flags is None:
            flags = libvirt.VIR_DOMAIN_AFFECT_CONFIG + libvirt.VIR_DOMAIN_AFFECT_LIVE
        xml = vmid.XMLDesc()
        tree = ElementTree.ElementTree(ElementTree.fromstring(xml))
        root = tree.getroot()
        # Returns libvirtError: internal error: unable to execute QEMU command 'eject': Tray of device 'drive-ide0-0-0' is not open
        xml_update_segments = []
        for element in root.findall('devices/disk[@device="cdrom"]'):
            target_info = element.find('target')
            if target == 'all' or (target != 'all' and target_info.attrib['dev'] == target):
                # Disconnecting = removing source
                source_element = element.find('source')
                if source_element is not None:
                    # Open tray
                    element.attrib.update({'type': 'file'})
                    target_info.attrib.update({'tray': 'open'})
                    element.remove(element.find('source'))
                    xml_update_segments.append(element)
                    # Close again
                    target_info.attrib.pop('tray')
                    xml_update_segments.append(element)
        for xml_update_segment in xml_update_segments:
            vmid.updateDeviceFlags(ElementTree.tostring(xml_update_segment), flags)
