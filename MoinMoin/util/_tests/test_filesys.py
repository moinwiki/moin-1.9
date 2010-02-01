# -*- coding: utf-8 -*-
"""
    MoinMoin - MoinMoin.util.filesys Tests

    @copyright: 2008 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""
import sys, os, time
import shutil, tempfile

import py.test

from MoinMoin.util import filesys

class TestFuid:
    """ test filesys.fuid (a better mtime() alternative for up-to-date checking) """

    def setup_method(self, method):
        self.test_dir = tempfile.mkdtemp('', 'fuid_')
        self.fname = os.path.join(self.test_dir, "fuid-test")
        self.tmpname = os.path.join(self.test_dir, "fuid-temp")

    def teardown_method(self, method):
        shutil.rmtree(self.test_dir)

    def testNoFile(self):
        # no file created
        uid = filesys.fuid(self.fname)

        assert uid is None  # there is no file yet, fuid will fail internally and return None

    def makefile(self, fname, content):
        f = open(fname, "w")
        f.write(content)
        f.close()

    def testNewFile(self):
        # freshly created file
        self.makefile(self.fname, "foo")
        uid1 = filesys.fuid(self.fname)

        assert uid1 is not None  # None would mean some failure in fuid()

    def testUpdateFileInPlace(self):
        # update file in place, changing size and maybe mtime
        self.makefile(self.fname, "foo")
        uid1 = filesys.fuid(self.fname)

        self.makefile(self.fname, "foofoo")
        uid2 = filesys.fuid(self.fname)

        assert uid2 != uid1 # we changed size and maybe mtime

    def testUpdateFileMovingFromTemp(self):
        # update file by moving another file over it (see caching.update)
        # changing inode, maybe mtime, but not size
        if sys.platform == 'win32':
            py.test.skip("Inode change detection not supported on win32")

        self.makefile(self.fname, "foo")
        uid1 = filesys.fuid(self.fname)

        self.makefile(self.tmpname, "bar")
        os.rename(self.tmpname, self.fname)
        uid2 = filesys.fuid(self.fname)

        assert uid2 != uid1 # we didn't change size, but inode and maybe mtime

    def testStale(self):
        # is a file with mtime older than max_staleness considered stale?
        if sys.platform != 'win32':
            py.test.skip("max_staleness check only done on win32 because it doesn't support inode change detection")

        self.makefile(self.fname, "foo")
        uid1 = filesys.fuid(self.fname)

        time.sleep(2) # thanks for waiting :)
        uid2 = filesys.fuid(self.fname, max_staleness=1)
        assert uid2 != uid1  # should be considered stale if platform has no inode support


coverage_modules = ['MoinMoin.util.filesys']
