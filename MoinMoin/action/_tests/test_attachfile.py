# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - tests of AttachFile action

    @copyright: 2007 by Karol Nowak <grywacz@gmail.com>
                     MoinMoin:ReimarBauer
    @license: GNU GPL, see COPYING for details.
"""
import os
from MoinMoin.action import AttachFile
from MoinMoin.PageEditor import PageEditor
from MoinMoin._tests.common import gain_superuser_rights

def test_add_attachment(request):
    """Test if add_attachment() works"""

    gain_superuser_rights(request)
    pagename = "AutoCreatedSillyPageToTestAttachments"
    filename = "AutoCreatedSillyAttachment"

    editor = PageEditor(request, pagename)
    editor.deletePage()
    editor.saveText("Test text!", 0)

    print "First of all, no exceptions should be raised!"
    AttachFile.add_attachment(request, pagename, filename, "Test content", True)

    print "The save attachment should actually exist!"
    assert AttachFile.exists(request, pagename, filename)

def test_get_attachment_path_created_on_getFilename(request):
    """
    Tests if AttachFile.getFilename creates the attachment dir on requesting
    """
    pagename = "ThisPageDoesOnlyExistForThisTest"
    filename = ""
    result = os.path.exists(AttachFile.getFilename(request, pagename, filename))
    expect = True

    # real delete pagename from filesystem
    import shutil
    page = PageEditor(request, pagename, do_editor_backup=0)
    page.deletePage()
    fpath = page.getPagePath(check_create=0)
    shutil.rmtree(fpath, True)

    assert expect == result
    
def test_getAttachUrl(request):
    """
    Tests if AttachFile.getAttachUrl taints a filename
    """
    pagename = "ThisPageDoesOnlyExistForThisTest"
    filename = "<test2.txt>"
    expect = "rename=_test2.txt_&"
    result = AttachFile.getAttachUrl(pagename, filename, request, upload=True)

    assert expect in result 
