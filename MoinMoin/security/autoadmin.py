# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - SecurityPolicy implementing auto admin rights for some users and some groups.

    AutoAdminGroup page contains users which automatically get admin rights
    on their homepage and subpages of it. E.g. if ThomasWaldmann is in
    AutoAdminGroup (or in a group contained in AutoAdminGroup), he gets
    admin rights on pages ThomasWaldmann and ThomasWaldmann/*.

    AutoAdminGroup page also contains groups which members automatically get
    admin rights on the group's basename.
    E.g. if SomeProject/AdminGroup is in AutoAdminGroup and ThomasWaldmann is
    in SomeProject/AdminGroup, then ThomasWaldmann gets admin rights on pages
    SomeProject and SomeProject/*.

    Further, it can autocreate the UserName/XxxxGroup (see grouppages var) when
    a user save his homepage. Alternatively, this could be also done manually by
    the user using *Template pages.

    Usage (for wiki admin):
     * Create an AutoAdminGroup page. If you don't know better, create an empty
       page for starting.
     * Enabling a home page for AutoAdmin: just add the user name to the
       AutoAdminGroup page. After that, this user can create or change ACLs on
       his homepage or subpages of it.
     * Enabling another (project) page for AutoAdmin: add <PageName>/AdminGroup
       to AutoAdminGroup. Also create that <PageName>/AdminGroup page and add
       at least one user or one group to that page, enabling him or them to
       create or change ACLs on <PageName> or subpages of it.
     Those pages edited by wiki admin should be ACL protected with write access
     limited to allowed people. They are used as source for some ACL
     information and thus should be treated like the ACLs they get fed into.

    Usage (for homepage owners):
     * see if there is a HomepageTemplate with a prepared ACL line and some
       other magic already on it. It is a good idea to have your homepage
       read- and writeable for everybody as a means of open communication.

     * For creating personal (or private) subpages of your homepage, use the
       ReadWritePageTemplate, ReadPageTemplate or PrivatePageTemplate.
       They usually have some prepared ACL line on them, e.g.:
       #acl @ME@/ReadWriteGroup:read,write @ME@/ReadGroup:read
       That @ME@ from the template will be expanded to your name when saving,
       thus using those 2 subpages (YourName/ReadWriteGroup and
       YourName/ReadGroup) for allowing read/write or read-only access to
       Now you only have to maintain 2 subpages (maybe they even have been
       auto- created for you)

    Usage (for project people):
     * see if there is some <ProjectName>Template with a prepared ACL line for
       your project pages and use it for creating new subpages.
       Use <ProjectName>/ReadWriteGroup and /ReadGroup etc. as you would do for
       a homepage (see above).

    @copyright: 2005-2006 Bastian Blank, Florian Festi, Thomas Waldmann
    @license: GNU GPL, see COPYING for details.
"""

grouppage_autocreate = False # autocreate the group pages - alternatively use templates
grouppages = ['AdminGroup', 'ReadGroup', 'ReadWriteGroup', ] # names of the subpages defining ACL groups

from MoinMoin.security import Permissions
from MoinMoin.Page import Page
from MoinMoin.PageEditor import PageEditor

class SecurityPolicy(Permissions):
    """ Extend the default security policy with autoadmin feature """

    def admin(self, pagename):
        try:
            request = self.request
            has_member = request.dicts.has_member
            username = request.user.name
            pagename = request.page.page_name
            mainpage = pagename.split('/')[0]
            if username == mainpage and has_member('AutoAdminGroup', username):
                return True
            groupname = "%s/AdminGroup" % mainpage
            if has_member(groupname, username) and has_member('AutoAdminGroup', groupname):
                return True
        except AttributeError:
            pass # when we get called from xmlrpc, there is no request.page
        return Permissions.__getattr__(self, 'admin')(pagename)

    def save(self, editor, newtext, rev, **kw):
        request = self.request
        username = request.user.name
        pagename = editor.page_name

        if grouppage_autocreate and username == pagename:
            # create group pages when a user saves his own homepage
            for page in grouppages:
                grouppagename = "%s/%s" % (username, page)
                grouppage = Page(request, grouppagename)
                if not grouppage.exists():
                    text = """\
#acl %(username)s:read,write,delete,revert
 * %(username)s
""" % locals()
                    editor = PageEditor(request, grouppagename)
                    editor._write_file(text)

        parts = pagename.split('/')
        if len(parts) == 2:
            subpage = parts[1]
            if subpage in grouppages and not self.admin(pagename):
                return False

        # No problem to save if my base class agrees
        return Permissions.save(self, editor, newtext, rev, **kw)


