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
import re
import socket
from ovs.extensions.generic.logger import Logger
from ovs_extensions.generic.remote import remote


class NetworkHelper(object):
    """
    NetworkHelper class
    """
    LOGGER = Logger("helpers-ci_network_helper")

    def __init__(self):
        pass

    @staticmethod
    def validate_ip(ip):
        pattern = re.compile(r"^(?<!\S)((\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])\b|\.\b){7}(?!\S)$")
        if not pattern.match(ip):
            raise ValueError('Not a valid IP address')

    @staticmethod
    def get_free_port(listener_ip, logger=LOGGER):
        """
        Returns a free port
        :param listener_ip: ip to listen on
        :type listener_ip: str
        :param logger: logging instance
        :type logger: ovs.extensions.generic.logger.Logger
        :return: port number
        :rtype: int
        """
        with remote(listener_ip, [socket]) as rem:
            listening_socket = rem.socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                # Bind to first available port
                listening_socket.bind(('', 0))
                port = listening_socket.getsockname()[1]
                return port
            except socket.error as ex:
                logger.error('Could not bind the socket. Got {0}'.format(str(ex)))
                raise
            finally:
                listening_socket.close()
