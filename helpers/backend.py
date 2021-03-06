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

from ovs.dal.hybrids.albabackend import AlbaBackend
from ovs.dal.lists.albabackendlist import AlbaBackendList
from ovs.dal.lists.backendlist import BackendList
from ovs.dal.lists.backendtypelist import BackendTypeList
from ovs.extensions.generic.logger import Logger
from ..helpers.ci_constants import CIConstants
from ..helpers.exceptions import PresetNotFoundError, AlbaBackendNotFoundError


class BackendHelper(CIConstants):
    """
    BackendHelper class
    """
    LOGGER = Logger("helpers-ci_backend")

    def __init__(self):
        pass

    @staticmethod
    def get_alba_backend_guid_by_name(backend_name):
        """

        :param backend_name: name of a backend
        :type backend_name: str
        :return: alba_backend_guid
        :rtype: str
        """
        try:
            return BackendList.get_by_name(backend_name).alba_backend_guid
        except AttributeError:
            error_msg = "No alba backend found with name `{0}`".format(backend_name)
            BackendHelper.LOGGER.error(error_msg)
            raise NameError(error_msg)

    @staticmethod
    def get_backend_guid_by_name(backend_name):
        """

        :param backend_name: name of a backend
        :type backend_name: str
        :return: backend_guid
        :rtype: str
        """

        return BackendList.get_by_name(backend_name).guid

    @staticmethod
    def get_backend_by_name(backend_name):
        """

        :param backend_name: name of a backend
        :type backend_name: str
        :return: Backend object
        :rtype: ovs.dal.hybrids.backend.Backend
        """

        return BackendList.get_by_name(backend_name)

    @staticmethod
    def get_backend_status_by_name(backend_name):
        """

        :param backend_name: name of a backend
        :type backend_name: str
        :return: backend status
        :rtype: str
        """

        return BackendList.get_by_name(backend_name).status

    @staticmethod
    def get_backendtype_guid_by_code(backendtype_code):
        """
        Get a backend type guid by a backend code

        :param backendtype_code: type name of a backend
        :type backendtype_code: str
        :return: backendtype_guid
        :rtype: str
        """

        return BackendTypeList.get_backend_type_by_code(backendtype_code).guid

    @staticmethod
    def get_albabackend_by_guid(albabackend_guid):
        """
        Get a albabackend by albabackend guid

        :param albabackend_guid: albabackend guid
        :type albabackend_guid: str
        :return: alba backend object
        :rtype: ovs.dal.hybrids.albabackend
        """

        return AlbaBackend(albabackend_guid)

    @staticmethod
    def get_albabackend_by_name(albabackend_name):
        """
        Get a Albabackend by name

        :param albabackend_name: albabackend name
        :type albabackend_name: str
        :return: alba backend object
        :rtype: ovs.dal.hybrids.albabackend
        """

        try:
            return [alba_backend for alba_backend in AlbaBackendList.get_albabackends()
                    if alba_backend.name == albabackend_name][0]
        except IndexError:
            error_msg = "No Alba backend found with name: {0}".format(albabackend_name)
            BackendHelper.LOGGER.error(error_msg)
            raise NameError(error_msg)

    @classmethod
    def get_asd_safety(cls, albabackend_guid, asd_id, *args, **kwargs):
        """
        Request the calculation of the disk safety
        :param albabackend_guid: guid of the alba backend
        :type albabackend_guid: str
        :param asd_id: id of the asd
        :type asd_id: str
        :return: asd safety
        :rtype: dict
        """
        params = {'asd_id': asd_id}
        task_guid = cls.api.get('alba/backends/{0}/calculate_safety'.format(albabackend_guid), params=params)
        result = cls.api.wait_for_task(task_id=task_guid, timeout=30)

        if result[0] is False:
            errormsg = "Calculate safety for '{0}' failed with '{1}'".format(asd_id, result[1])
            BackendHelper.LOGGER.error(errormsg)
            raise RuntimeError(errormsg)
        return result[1]

    @classmethod
    def get_backend_local_stack(cls, albabackend_name, *args, **kwargs):
        """
        Fetches the local stack property of a backend

        :param albabackend_name: backend name
        :type albabackend_name: str
        """
        options = {
            'contents': 'local_stack',
        }
        return cls.api.get(api='/alba/backends/{0}/'.format(BackendHelper.get_alba_backend_guid_by_name(albabackend_name)),
                           params={'queryparams': options})

    @staticmethod
    def get_alba_backends():
        """
        Fetches all the alba backends on the cluster

        :return: alba backends
        :rtype: list
        """

        return AlbaBackendList.get_albabackends()

    @classmethod
    def get_maintenance_config(cls, albabackend_name):
        """
        Fetch the maintenance config of an AlbaBackend
        :param albabackend_name: backend name
        :type albabackend_name: str
        :return: dict[str]
        """
        return cls.api.get(api='/alba/backends/{0}/get_maintenance_config'.format(BackendHelper.get_alba_backend_guid_by_name(albabackend_name)))

    @classmethod
    def get_maintenance_metadata(cls):
        """
        Fetch the maintenance metadata config
        :return: dict[str]
        """
        return cls.api.get(api='/alba/backends/get_maintenance_metadata')


    @staticmethod
    def get_preset_by_albabackend(preset_name, albabackend_name):
        """
        Fetches preset by albabackend_guid

        :param preset_name: name of a existing preset
        :type preset_name: str
        :param albabackend_name: name of a existing alba backend
        :type albabackend_name: str
        :return: alba backends
        :rtype: list
        """

        try:
            return [preset for preset in BackendList.get_by_name(albabackend_name).alba_backend.presets
                    if preset['name'] == preset_name][0]
        except IndexError:
            raise PresetNotFoundError("Preset `{0}` on alba backend `{1}` was not found"
                                      .format(preset_name, albabackend_name))
        except AttributeError:
            raise AlbaBackendNotFoundError("Albabackend with name `{0}` does not exist".format(albabackend_name))

    @staticmethod
    def get_local_stack_alias(disk_object):
        """
        Fetches the object with the alias that is present in the local_stack object
        :param disk_object: object with disk info
        :type disk_object: dict
        :return: path of the disk
        :rtype: str
        """
        alias_prefixes = ['ata', 'scsi', 'virtio']
        for disk_type in alias_prefixes:
            found_aliases = [x for x in disk_object["aliases"] if x.rsplit('/', 1)[-1].startswith(disk_type)]
            if len(found_aliases) == 0:
                continue
            else:
                return found_aliases[0].rsplit('/', 1)[-1]
        raise RuntimeError('Could not find a suitable disk alias to use. Only looking for {0} and object has {1}'.format(alias_prefixes, disk_object))
