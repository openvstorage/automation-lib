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

from subprocess import check_output
from ovs.extensions.generic.system import System
from ovs.extensions.generic.logger import Logger
from ovs.extensions.generic.sshclient import SSHClient
from ..helpers.ci_constants import CIConstants
from ..helpers.fstab import FstabHelper
from ..helpers.storagerouter import StoragerouterHelper
from ..setup.roles import RoleSetup


class RoleRemover(CIConstants):

    LOGGER = Logger("remove-ci_role_remover")
    CONFIGURE_DISK_TIMEOUT = 300

    @staticmethod
    def _umount(mountpoint, client=None):
        """
        Unmount the given partition
        :param mountpoint: Location where the mountpoint is mounted
        :type mountpoint: str
        :return:
        """
        if client is None:
            client = SSHClient(System.get_my_storagerouter(), username='root')
        try:
            client.run(['umount', mountpoint])
        except Exception:
            RoleRemover.LOGGER.exception('Unable to umount mountpoint {0}'.format(mountpoint))
            raise RuntimeError('Could not unmount {0}'.format(mountpoint))

    @staticmethod
    def _remove_filesystem(device, alias_part_label, client=None):
        """

        :param alias_part_label: eg /dev/disk/by-partlabel/ata-QEMU_HARDDISK_QM00011
        :type alias_part_label: str
        :return:
        """
        if client is None:
            client = SSHClient(System.get_my_storagerouter(), username='root')
        try:
            partition_cmd = "udevadm info --name={0} | awk -F '=' '/ID_PART_ENTRY_NUMBER/{{print $NF}}'".format(alias_part_label)
            partition_number = client.run(partition_cmd, allow_insecure=True)
            if partition_number:
                format_cmd = 'parted {0} rm {1}'.format(device, partition_number)
                client.run(format_cmd.split())
        except Exception:
            RoleRemover.LOGGER.exception('Unable to remove filesystem of {0}'.format(alias_part_label))
            raise RuntimeError('Could not remove filesystem of {0}'.format(alias_part_label))

    @classmethod
    def remove_role(cls, storagerouter_ip, diskname):
        allowed_roles = ['WRITE', 'DTL', 'SCRUB', 'DB']
        cls.LOGGER.info("Starting removal of disk roles.")
        # Fetch information

        storagerouter = StoragerouterHelper.get_storagerouter_by_ip(storagerouter_ip=storagerouter_ip)
        disk = StoragerouterHelper.get_disk_by_name(guid=storagerouter.guid, diskname=diskname)
        # Check if there are any partitions on the disk, if so check if there is enough space
        client = SSHClient(storagerouter, username='root')

        if len(disk.partitions) > 0:
            for partition in disk.partitions:
                # Remove all partitions that have roles
                if set(partition.roles).issubset(allowed_roles) and len(partition.roles) > 0:
                    cls.LOGGER.info("Removing {0} from partition {1} on disk {2}".format(partition.roles, partition.guid, diskname))
                    RoleSetup.configure_disk(storagerouter_guid=storagerouter.guid,
                                             disk_guid=disk.guid,
                                             offset=partition.offset,
                                             size=disk.size,
                                             roles=[],
                                             partition_guid=partition.guid)


                    cls._umount(partition.mountpoint, client=client)
                    # Remove from fstab

                    cls.LOGGER.info("Removing {0} from fstab".format(partition.mountpoint, partition.guid, diskname))
                    FstabHelper(client=client).remove_by_mountpoint(partition.mountpoint,client)
                    # Remove filesystem
                    cls.LOGGER.info("Removing filesystem on partition {0} on disk {1}".format(partition.guid, diskname))
                    alias = partition.aliases[0]
                    device = '/dev/{0}'.format(diskname)
                    cls._remove_filesystem(device, alias,client=client)
                    # Remove partition from model
                    cls.LOGGER.info("Removing partition {0} on disk {1} from model".format(partition.guid, diskname))
                    partition.delete()
                else:
                    print 'Found no roles on partition'
                    RoleRemover.LOGGER.info("{1} on disk {2}".format(partition.roles, partition.guid, diskname))
        else:
            print 'found no partition'
            RoleRemover.LOGGER.info("Found no partition on the disk.")
