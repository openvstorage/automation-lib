# Copyright (C) 2018 iNuron NV
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
from ovs.dal.lists.iscsinodelist import IscsiNodeList
from ovs.lib.iscsinode import IscsiNodeController


class ISCSIHelper(object):
    """
    Helper class for iSCSI nodes
    """

    @classmethod
    def get_iscsi_nodes(cls):
        """
        Get all available iSCSI nodes in the environment
        :return: list containting iSCSI nodes
        :rtype: DataList
        """
        return IscsiNodeList.get_iscsi_nodes()

    @staticmethod
    def expose_vdisk(iscsi_node_guid, vdisk_guid, failover_node_guids=None, username=None, password=None, acls=None):
        """
        Expose a vDisk on the specified iSCSI Node
        :param iscsi_node_guid: Guid of the iSCSI Node to expose the vDisk on
        :type iscsi_node_guid: str
        :param vdisk_guid: Guid of the vDisk to expose
        :type vdisk_guid: str
        :param failover_node_guids: Guids of the iSCSI Node to expose the vDisk on as failover nodes
        :type failover_node_guids: list
        :param username: User to which the Edge vDisk belongs to
        :type username: str
        :param password: Password linked to the user
        :type password: str
        :param acls: ACL information to enforce limited access to the vDisk
        :type acls: list[str]
        :return: IQN details {node_guid: iqn}
        :rtype: dict
        """
        return IscsiNodeController.expose_vdisk(prim_node_guid=iscsi_node_guid,
                                                vdisk_guid=vdisk_guid,
                                                failover_node_guids=failover_node_guids,
                                                username=username,
                                                password=password,
                                                acls=acls)

    @staticmethod
    def unexpose_vdisk(vdisk_guid):
        """
        Un-expose a vDisk from all iSCSI Nodes its exposed on
        :param vdisk_guid: Guid of the vDisk to un-expose
        :type vdisk_guid: str
        :return: None
        :rtype: NoneType
        """
        IscsiNodeController.unexpose_vdisk(vdisk_guid=vdisk_guid)

    @staticmethod
    def restart_targets_for_vdisk(vdisk_guid):
        """
        Restarts all targets for the vDisks
        Deletes the current targets and re-creates them so the connections can be re-established
        :param vdisk_guid: Guid of the vDisk to restart targets for
        :type vdisk_guid: str
        :return: None
        :rtype: NoneType
        """
        IscsiNodeController.restart_targets_for_vdisk(vdisk_guid=vdisk_guid)
