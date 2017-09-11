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
import time
import threading
from threading import Lock
from ovs.extensions.generic.logger import Logger


class ThreadHelper(object):
    LOGGER = Logger('helpers-ci_threading')

    @staticmethod
    def start_thread_with_event(target, name, args=(), kwargs=None):
        """
        Starts a thread and an event to it
        :param target: target - usually a method
        :type target: object
        :param name: name of the thread
        :type name: str
        :param args: tuple of arguments
        :type args: tuple
        :return: a tuple with the thread and event
        :rtype: tuple(threading.Thread, threading.Event)
        """
        if kwargs is None:
            kwargs = {}
        ThreadHelper.LOGGER.info('Starting thread with target {0}'.format(target))
        event = threading.Event()
        args = args + (event,)
        thread = threading.Thread(target=target, args=tuple(args), kwargs=kwargs)
        thread.setName(str(name))
        thread.setDaemon(True)
        thread.start()
        return thread, event

    @staticmethod
    def start_thread(target, name, args=(), kwargs=None):
        if kwargs is None:
            kwargs = {}
        ThreadHelper.LOGGER.info('Starting thread with target {0}'.format(target))
        thread = threading.Thread(target=target, args=tuple(args), kwargs=kwargs)
        thread.setName(str(name))
        thread.setDaemon(True)
        thread.start()
        return thread

    @staticmethod
    def stop_evented_threads(thread_pairs, r_semaphore=None, logger=LOGGER, timeout=300):
        for thread_pair in thread_pairs:
            if thread_pair[0].isAlive():
                thread_pair[1].set()
            # Wait again to sync
            logger.info('Syncing threads')
        if r_semaphore is not None:
            start = time.time()
            while r_semaphore.get_counter() < len(thread_pairs):  # Wait for the number of threads we currently have.
                if time.time() - start > timeout:
                    raise RuntimeError('Synching the thread with the r_semaphore has timed out.')
                time.sleep(0.05)
            r_semaphore.wait()  # Unlock them to let them stop (the object is set -> wont loop)
        # Wait for threads to die
        for thread_pair in thread_pairs:
            thread_pair[0].join()


# @todo import from -> from ovs.extensions.generic.threadhelpers import Waiter instead of this when PR (https://github.com/openvstorage/framework/pull/1467) is in Fargo n unstable
class Waiter(object):
    def __init__(self, target, auto_reset=False):
        self._target = target
        self._counter = 0
        self._lock = Lock()
        self._auto_release_lock = Lock()
        self._auto_reset = auto_reset
        self._auto_release_counter = 0

    def wait(self, timeout=5):
        with self._lock:
            self._counter += 1
            reached = self._counter == self._target
            if reached is True and self._auto_reset is True:
                while self._auto_release_counter < self._target - 1:
                    time.sleep(0.05)
                self._counter = 0
                with self._auto_release_lock:
                    self._auto_release_counter = 0
        if reached is False:
            start = time.time()
            while self._counter < self._target:
                time.sleep(0.05)
                if time.time() - start > timeout:
                    raise RuntimeError('Not all peers were available within {0}s'.format(timeout))
            with self._auto_release_lock:
                self._auto_release_counter += 1

    def get_counter(self):
        return self._counter
