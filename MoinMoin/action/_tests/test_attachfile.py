# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - tests of AttachFile action

    @copyright: 2007 by Karol Nowak <grywacz@gmail.com>
                2007-2008 MoinMoin:ReimarBauer
    @license: GNU GPL, see COPYING for details.
"""
import os, StringIO
from MoinMoin.action import AttachFile
from MoinMoin.PageEditor import PageEditor
from MoinMoin._tests import become_trusted, create_page, nuke_page

class TestAttachFile:
    """ testing action AttachFile"""
    pagename = u"AutoCreatedSillyPageToTestAttachments"

    def test_add_attachment(self):
        """Test if add_attachment() works"""

        become_trusted(self.request)
        filename = "AutoCreatedSillyAttachment"

        create_page(self.request, self.pagename, u"Foo!")

        AttachFile.add_attachment(self.request, self.pagename, filename, "Test content", True)
        exists = AttachFile.exists(self.request, self.pagename, filename)

        nuke_page(self.request, self.pagename)

        assert exists

    def test_add_attachment_for_file_object(self):
        """Test if add_attachment() works with file like object"""

        become_trusted(self.request)

        filename = "AutoCreatedSillyAttachment.png"

        create_page(self.request, self.pagename, u"FooBar!")
        data = "Test content"

        filecontent = StringIO.StringIO(data)

        AttachFile.add_attachment(self.request, self.pagename, filename, filecontent, True)
        exists = AttachFile.exists(self.request, self.pagename, filename)
        path = AttachFile.getAttachDir(self.request, self.pagename)
        imagef = os.path.join(path, filename)
        file_size = os.path.getsize(imagef)

        nuke_page(self.request, self.pagename)

        assert exists and file_size == len(data)

    def test_get_attachment_path_created_on_getFilename(self):
        """
        Tests if AttachFile.getFilename creates the attachment dir on self.requesting
        """
        become_trusted(self.request)

        filename = ""

        file_exists = os.path.exists(AttachFile.getFilename(self.request, self.pagename, filename))

        nuke_page(self.request, self.pagename)

        assert file_exists

coverage_modules = ['MoinMoin.action.AttachFile']
