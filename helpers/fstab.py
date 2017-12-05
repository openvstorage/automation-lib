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
import inspect
from ovs.extensions.generic.sshclient import SSHClient
from ovs.extensions.generic.system import System


class FstabHelper():
    """
    Class to help with Fstab manipulations
    Inherits from file class
    """
    import os


    class Entry(object):
        """
        Entry class represents a non-comment line on the `/etc/fstab` file
        """

        def __init__(self, device, mountpoint, filesystem, options, d=0, p=0):
            self.device = device
            self.mountpoint = mountpoint
            self.filesystem = filesystem

            if not options:
                options = "defaults"

            self.options = options
            self.d = d
            self.p = p

        def __eq__(self, o):
            return str(self) == str(o)

        def __ne__(self, o):
            return str(self) != str(o)

        def __str__(self):
            return "{} {} {} {} {} {}".format(self.device, self.mountpoint, self.filesystem, self.options, self.d, self.p)

        def get(self, item):
            if not isinstance(item,basestring):
                raise ValueError('Specified parameter {0} must be a string')
            item = item.lower()
            if item in self.__dict__.keys():
                if item == 'device':
                    return self.device
                elif item == 'mountpoint':
                    return self.mountpoint
                elif item == 'options':
                    return self.options
                elif item == 'd':
                    return self.d
                elif item == 'p':
                    return self.p
                else:
                    return None
            else:
                raise ValueError('Specified parameter {0} not an attribute of Entry class.'.format(item))

    DEFAULT_PATH = os.path.join(os.path.sep, 'etc', 'fstab')

    _path = DEFAULT_PATH

    def __init__(self, path=None, client=None):
        """

        :param path: path of the fstab file
        :type path: str
        """
        if path:
            self._path = path
        else:
            self._path = self.DEFAULT_PATH
        if client is None:
            client = SSHClient(System.get_my_storagerouter(), username='root')
        self.client = client


    @staticmethod
    def _hydrate_entry(line):
        """
        Parse and add a line from fstab
        :param line: line that is present in fstab
        :type line: str
        :return:
        """
        return FstabHelper.Entry(*filter(lambda x: x not in ('',' ', None), str(line).strip("\n").split(" ")))

    def get_entry_by_attr(self, attr, value):
        """
        Returns an entry with where an attr has a specific value
        :param attr: attribute from the entry
        :param value: value that the attribute should have
        :return:
        """
        entries = []
        for line in self.client.file_read(self._path).strip().splitlines():
            try:
                if not line.startswith("#") and line.strip() is not '':
                    entries.append(self._hydrate_entry(line))
            except ValueError:
                pass
        for entry in entries:
            e_attr = entry.get(attr)
            if e_attr == value:
                return entry
        return None

    def remove_entry(self, entry):
        """
        Removes a line from fstab
        :param entry:entry object
        :return:
        """
        lines = self.client.file_read(self._path).strip().splitlines()
        lines = [line for line in lines if not line.startswith('#') and self._hydrate_entry(line) != entry]
        self.client.file_write(self._path, '\n'.join(lines))

    def remove_by_mountpoint(self, mountpoint, client=None):
        """
        Removes an entry by specific mountpoint
        :param mountpoint: mountpoint
        :return:
        """

        entry = self.get_entry_by_attr('mountpoint', mountpoint)
        if entry:
            self.remove_entry(entry)

    def add(self, device, mountpoint, filesystem, options=None, dump=None, pass_=None):
        """
        Adds a entry based on supplied params
        :param device: devicename eg /dev/sda
        :param mountpoint: point where the device is mounted eg /mnt/sda
        :param filesystem: type of filesystem eg ext4
        :param options: extra options eg 'defaults'
        :param dump: filesystems needs to be dumped or not
        :param pass_: order to check filesystem at reboot time
        :return:
        """
        lines = self.client.file_read(self._path).strip().splitlines()
        lines.append(str(FstabHelper.Entry(device, mountpoint, filesystem, options, dump)))
        self.client.file_write(self._path, '\n'.join(lines))
