# -*- coding: utf-8 -*-
"""
    MoinMoin - MoinMoin test for new style "locking" (== mostly avoid locking)

    The idea is to not have to lock files when we just want to read them.
    When we never overwrite file content with new stuff, locking is not needed.
    We can just write the new content into a new file (with tmpfname) and then
    rename it to the original filename. Files that opened the original filename
    before the rename will still read old content after the rename (until they
    are closed).

    @copyright: 2006 by Thomas Waldmann (idea: Bastian Blank)
    @license: GNU GPL, see COPYING for details.
"""

import unittest, tempfile, os, shutil
from MoinMoin._tests import TestConfig, TestSkipped

def rename(oldname, newname):
    """ Multiplatform rename

    Move to MoinMoin.util.filesys when done.

    TODO:
    Test/Fix win32 stuff.
    
    Check: MoveFileEx: If the new filename is None, it deletes the file (needs very recent pywin32 binding).
           This is documented for the "on reboot" stuff, does this also work when not doing it on next reboot?
           Maybe we can use this at another place.
           
    API doc: http://msdn.microsoft.com/library/default.asp?url=/library/en-us/fileio/fs/movefileex.asp
    
    Windows 95/98/ME do not implement MoveFileEx().
    Either have some other working code or document we drop support for less-than-NT.
    Document pywin32 extension dependency.

    """
    # this nt specific code should be replaced by better stuff
    if os.name == 'nt':
        # uses mark hammond's pywin32 extension
        # there seems to be also stuff in win32api.MoveFileEx and win32con.MOVEFILE_REPLACE_EXISTING
        # what's the difference to them in win32file?
        from win32file import MoveFileEx, MOVEFILE_REPLACE_EXISTING
        ret = MoveFileEx(oldname, newname, MOVEFILE_REPLACE_EXISTING)
        # If the function succeeds, the return value is nonzero.
        # If the function fails, the return value is 0 (zero). To get extended error information, call GetLastError.
        if ret == 0:
            raise OSError # emulate os.rename behaviour
    else:
        os.rename(oldname, newname) # rename has no return value, but raises OSError in case of failure


class NewLockTests(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp('', 'lock_')

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def testNoLockingForReading(self):
        """ new locking: NoLockingForReading tests if files still work when filename is target of a rename """
        fname = os.path.join(self.test_dir, 'readtest')
        tmpfname = os.path.join(self.test_dir, '__readtest')
        origdata = "precious content"
        newdata = "new content"
        f = file(fname, "w") ; f.write(origdata) ; f.close()
        f = file(fname, "r")
        ftmp = file(tmpfname, "w") ; ftmp.write(newdata) ; ftmp.close()
        rename(tmpfname, fname)
        read1data = f.read() ; f.close() # we should still get origdata here!
        f = file(fname, "r") ; read2data = f.read() ; f.close() # we should newdata now.
        self.failUnless(origdata == read1data and newdata == read2data, "got wrong data when reading")

