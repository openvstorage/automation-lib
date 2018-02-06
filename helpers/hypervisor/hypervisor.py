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
Hypervisor/ManagementCenter factory module
Using the module requires libvirt api to be available on the MACHINE THAT EXECUTES THE CODE
"""
from ovs_extensions.generic.filemutex import file_mutex
from ovs.lib.helpers.toolbox import Toolbox
from ...helpers.ci_constants import CIConstants


class HypervisorFactory(CIConstants):
    """
    HypervisorFactory class provides functionality to get abstracted hypervisor
    """
    hypervisors = {}

    @classmethod
    def get(cls, hv_credentials=None):
        """
        Returns the appropriate hypervisor client class for a given PMachine
        :param hv_credentials: object that contains ip, user, password and hypervisor type
        :type hv_credentials: HypervisorCredentials object
        """
        if hv_credentials is None:
            return cls.get(HypervisorCredentials(ip=CIConstants.HYPERVISOR_INFO['ip'],
                                               user=CIConstants.HYPERVISOR_INFO['user'],
                                               password=CIConstants.HYPERVISOR_INFO['password'],
                                               type=CIConstants.HYPERVISOR_INFO['type']))
        if not isinstance(hv_credentials, HypervisorCredentials):
            raise TypeError('Credentials must be of type HypervisorCredentials')
        return cls.hypervisors.get(hv_credentials, cls._add_hypervisor(hv_credentials))

    @staticmethod
    def _add_hypervisor(hypervisor_credentials):
        ip = hypervisor_credentials.ip
        username = hypervisor_credentials.user
        password = hypervisor_credentials.password
        hvtype = hypervisor_credentials.type
        mutex = file_mutex('hypervisor_{0}'.format(hash(hypervisor_credentials)))
        try:
            mutex.acquire(30)
            if hypervisor_credentials not in HypervisorFactory.hypervisors:
                if hvtype == 'VMWARE':
                    # Not yet tested. Needs to be rewritten
                    raise NotImplementedError("{0} has not yet been implemented".format(hvtype))
                    from .hypervisors.vmware import VMware
                    hypervisor = VMware(ip, username, password)
                elif hvtype == 'KVM':
                    from .hypervisors.kvm import KVM
                    hypervisor = KVM(ip, username, password)
                else:
                    raise NotImplementedError('Hypervisor {0} is not yet supported'.format(hvtype))
                HypervisorFactory.hypervisors[hypervisor_credentials] = hypervisor
            return hypervisor
        finally:
            mutex.release()


class HypervisorCredentials(object):
    def __init__(self, ip, user, password, type):
        required_params = {'ip': (str, Toolbox.regex_ip),
                           'user': (str, None),
                           'password': (str, None),
                           'type': (str, ['KVM', 'VMWARE'])}
        Toolbox.verify_required_params(required_params, {'ip': ip,
                                                         'user': user,
                                                         'password': password,
                                                         'type': type})
        self.ip = ip
        self.user = user
        self.password = password
        self.type = type

    def __str__(self):
        return 'hypervisor at ip {0} of type {1}'.format(self.ip, self.type)
