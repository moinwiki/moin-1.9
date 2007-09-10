# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - tests of AttachFile action

    @copyright: 2007 by Karol Nowak <grywacz@gmail.com>
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.action.AttachFile import add_attachment, exists
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
    add_attachment(request, pagename, filename, "Test content", True)

    print "The save attachment should actually exist!"
    assert exists(request, pagename, filename)
