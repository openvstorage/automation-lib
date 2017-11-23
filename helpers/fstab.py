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

    def __init__(cls, path=None):
        if path:
            cls._path = path
        else:
            cls._path = cls.DEFAULT_PATH


    @staticmethod
    def _hydrate_entry(line):
        """
        Parse and add a line from fstab
        :param line: line that is present in fstab
        :type line: str
        :return:
        """
        return FstabHelper.Entry(*filter(lambda x: x not in ('',' ', None), str(line).strip("\n").split(" ")))

    @classmethod
    def get_entry_by_attr(cls, attr, value):
        """
        Returns an entry with where a attr has a specific value
        :param attr: attribute from the entry
        :param value: value that the attribute should have
        :return:
        """

        entries = []
        with open(cls._path, 'r') as fh:
            for line in fh:
                try:
                    if not line.startswith("#") and line.strip() is not '':
                        entries.append(cls._hydrate_entry(line))
                except ValueError:
                    pass

        for entry in entries:
            e_attr = entry.get(attr)
            if e_attr == value:
                return entry
        return None

    @classmethod
    def remove_entry(cls, entry):
        """
        Removes a line from fstab
        :param entry:entry object
        :return:
        """
        with open(cls._path, 'r+') as fh:
            d = fh.readlines()
            fh.seek(0)
            for line in d:
                if line.strip() != entry and not line.startswith('#'):
                    fh.write(line)
            fh.truncate()

    @classmethod
    def remove_by_mountpoint(cls, mountpoint):
        """
        Removes an entry by specific mountpoint
        :param mountpoint: mountpoint
        :return:
        """
        entry = cls.get_entry_by_attr('mountpoint', mountpoint)
        if entry:
            cls.remove_entry(entry)

    @classmethod
    def add(cls, device, mountpoint, filesystem, options=None, dump=None, pass_=None):
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
        with open(cls._path, 'a+') as fh:
            fh.write(str(FstabHelper.Entry(device, mountpoint, filesystem, options, dump))+'\n')
