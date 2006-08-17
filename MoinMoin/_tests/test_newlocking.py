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

    TODO: Implement for win32 using win32file.MoveFileEx("old.txt", "new.txt" , win32file.MOVEFILE_REPLACE_EXISTING)
          BTW: If the new filename is None, it deletes the file (needs very recent pywin32 binding).
          
    Windows 95 does not implement MoveFileEx() (MSDN).
    Windows 98 also does not implement MoveFileEx() (http://mail.python.org/pipermail/spambayes/2003-March/003866.html).
    Windows ME maybe also does not.
    Maybe just drop support for non-NT based windows?
    I guess this depends on pywin32 for doing that call?

    """
    # this nt specific code should be replaced by better stuff
    if os.name == 'nt':
        # uses mark hammond's pywin32 extension
        # there seems to be also stuff in win32api.MoveFileEx and win32con.MOVEFILE_REPLACE_EXISTING
        # what's the difference to them in win32file?
        from win32file import MoveFileEx, MOVEFILE_REPLACE_EXISTING
        # add error handling, check code calling us
        MoveFileEx(oldname, newname, MOVEFILE_REPLACE_EXISTING)
        return whatever # XXX
    else:
        return os.rename(oldname, newname)


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

