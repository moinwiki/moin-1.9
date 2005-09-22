# -*- coding: utf-8 -*-
"""
    MoinMoin - MoinMoin.module_tested Tests

    Module names must start with 'test_' to be included in the tests.

    @copyright: 2005 by Florian Festi
    @license: GNU GPL, see COPYING for details.
"""

import unittest, tempfile, os, time, shutil
from MoinMoin._tests import TestConfig, TestSkiped
from MoinMoin.util.lock import ExclusiveLock


class ExclusiveLockTests(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp('', 'lock_')
        self.lock_dir = os.path.join(self.test_dir, "lock")
        
    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def testTimeout(self):
        """ util.lock: ExclusiveLock: raise ValueError for timeout < 2.0 """
        self.assertRaises(ValueError, ExclusiveLock, self.lock_dir, timeout=1.0)
        
    def testAcquire(self):
        """ util.lock: ExclusiveLock: acquire """
        lock = ExclusiveLock(self.lock_dir)
        self.failUnless(lock.acquire(0.1), "Could not acquire lock")

    def testRelease(self):
        """ util.lock: ExclusiveLock: release 
        
        After releasing a lock, new one could be acquired.
        """
        lock = ExclusiveLock(self.lock_dir)
        if not lock.acquire(0.1):
            raise TestSkiped("can't acquire lock")
        lock.release()
        self.failUnless(lock.acquire(0.1), 
                        "Could not acquire lock after release")

    def testIsLocked(self):
        """ util.lock: ExclusiveLock: isLocked """
        lock = ExclusiveLock(self.lock_dir)
        if not lock.acquire(0.1):
            raise TestSkiped("can't acquire lock")
        self.failUnless(lock.isLocked(), "lock state wrong")
        lock.release()
        self.failIf(lock.isLocked(), "lock state wrong")

    def testExists(self):
        """ util.lock: ExclusiveLock: exists """
        lock = ExclusiveLock(self.lock_dir)
        if not lock.acquire(0.1):
            raise TestSkiped("can't acquire lock")
        self.failUnless(lock.exists(), "lock should exists")

    def testIsExpired(self):
        """ util.lock: ExclusiveLock: isExpired """
        timeout = 2.0
        lock = ExclusiveLock(self.lock_dir, timeout=timeout)
        if not lock.acquire(0.1):
            raise TestSkiped("can't acquire lock")
        self.failIf(lock.isExpired(), "lock should not be expired yet")
        time.sleep(timeout)
        self.failUnless(lock.isExpired(), "lock should be expired")

    def testExpire(self):
        """ util.lock: ExclusiveLock: expire """
        timeout = 2.0
        lock = ExclusiveLock(self.lock_dir, timeout=timeout)
        if not lock.acquire(0.1):
            raise TestSkiped("can't acquire lock")
        self.failIf(lock.expire(), "lock should not be expired yet")
        time.sleep(timeout)
        self.failUnless(lock.expire(), "lock should be expired")

    def testExclusive(self):
        """ util.lock: ExclusiveLock: lock is exclusive """
        first = ExclusiveLock(self.lock_dir)
        second = ExclusiveLock(self.lock_dir)
        if not first.acquire(0.1):
            raise TestSkiped("can't acquire lock")
        self.failIf(second.acquire(0.1), "first lock is not exclusive")                

    def testAcquireAfterTimeout(self):
        """ util.lock: ExclusiveLock: acquire after timeout
        
        Lock with one lock, try to acquire another after timeout.
        """
        timeout = 2.0 # minimal timout
        first = ExclusiveLock(self.lock_dir, timeout)
        second = ExclusiveLock(self.lock_dir, timeout)
        if not first.acquire(0.1):
            raise TestSkiped("can't acquire lock")
        if second.acquire(0.1):
            raise TestSkiped("first lock is not exclusive")
        # Second lock should be acquired after timeout
        self.failUnless(second.acquire(timeout + 0.1), 
                        "can't acquire after timeout")
            
    def unlock(self, lock, delay):
        time.sleep(delay)
        lock.release()

