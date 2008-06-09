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
from MoinMoin._tests import become_trusted, create_page, nuke_page

def test_add_attachment(request):
    """Test if add_attachment() works"""

    become_trusted(request)
    pagename = "AutoCreatedSillyPageToTestAttachments"
    filename = "AutoCreatedSillyAttachment"

    create_page(request, pagename, u"Foo!")

    AttachFile.add_attachment(request, pagename, filename, "Test content", True)
    exists = AttachFile.exists(request, pagename, filename)

    nuke_page(request, pagename)

    assert exists

def test_add_attachment_mimetype(request):
    """Test if add_attachment() with small mimetype file works"""

    become_trusted(request)
    pagename = "AutoCreatedSillyPageToTestAttachments"
    filename = "AutoCreatedSillyAttachment.png"

    create_page(request, pagename, u"FooBar!")

    import base64
    imageEncodeText = "iVBORw0KGgoAAAANSUhEUgAAABAAAAAMCAIAAADkharWAAAAD0lEQVQokWNgGAWjgDoAAAJMAAFOlIxNAAAAAElFTkSuQmCC"
    filecontent = base64.decodestring(imageEncodeText)

    AttachFile.add_attachment(request, pagename, filename, filecontent, True)
    exists = AttachFile.exists(request, pagename, filename)
    path = AttachFile.getAttachDir(request, pagename)
    imagef = os.path.join(path, filename)
    file_size = os.path.getsize(imagef)

    nuke_page(request, pagename)

    assert exists and file_size == 72

def test_get_attachment_path_created_on_getFilename(request):
    """
    Tests if AttachFile.getFilename creates the attachment dir on requesting
    """
    pagename = "ThisPageDoesOnlyExistForThisTest"
    filename = ""
    file_exists = os.path.exists(AttachFile.getFilename(request, pagename, filename))

    nuke_page(request, pagename)

    assert file_exists

def test_getAttachUrl(request):
    """
    Tests if AttachFile.getAttachUrl taints a filename
    """
    pagename = "ThisPageDoesOnlyExistForThisTest"
    filename = "<test2.txt>"
    expect = "rename=_test2.txt_&"
    result = AttachFile.getAttachUrl(pagename, filename, request, upload=True)

    assert expect in result

