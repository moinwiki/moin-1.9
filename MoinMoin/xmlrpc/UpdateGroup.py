# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Wiki XMLRPC group creation

    @copyright: (c) Bastian Blank, Florian Festi, Thomas Waldmann
    @license: GNU GPL, see COPYING for details.
"""

import sys, xmlrpclib, re

from MoinMoin.Page import Page
from MoinMoin.PageEditor import PageEditor

_debug = 0

def execute(self, groupname, groupcomment, memberlist, pageacls=u"All:read"):
    """
    create or overwrite a group definition page
    @param groupname: the page name of the group definition page (unicode or utf-8)
                      must match the page_group_regex or it won't have effect
    @param memberlist: the group members (unicode or utf-8)
    @param pageacls: the ACLs to use for the group page (defaults to u"All:read")
    @rtype: bool
    @return: true on success
    """
    if self.request.cfg.xmlrpc_putpage_enabled:
        pagename = self._instr(groupname)
    else:
        pagename = u"TestUpdateGroup"

    # By default, only authenticated (trusted) users may use putPage!
    # Trusted currently means being authenticated by http auth.
    # if you also want untrusted users to be able to write pages, then
    # change your wikiconfig to have xmlrpc_putpage_trusted_only = 0
    # and make very very sure that nobody untrusted can access your wiki
    # via network or somebody will raid your wiki some day!
        
    if self.request.cfg.xmlrpc_putpage_trusted_only and not self.request.user.trusted:
        return xmlrpclib.Fault(1, "You are not allowed to edit this page")

    # also check ACLs
    if not self.request.user.may.write(pagename):
        return xmlrpclib.Fault(1, "You are not allowed to edit this page")

    # check if groupname matches page_group_regex
    if not re.match(self.request.cfg.page_group_regex, groupname):
        return xmlrpclib.Fault(2, "The groupname %s does not match your page_group_regex (%s)" % (
	                          groupname, self.request.cfg.page_group_regex))

    newtext = """\
#acl %(acl)s
%(comment)s
%(memberlist)s
""" % {
    'acl': pageacls,
    'comment': groupcomment,
    'memberlist': "\n * ".join([''] + memberlist)
    }
    
    page = PageEditor(self.request, pagename)
    try:
        msg = page.saveText(newtext, 0)
    except page.SaveError, msg:
        return xmlrpclib.Fault(3, msg)
    if _debug and msg:
        sys.stderr.write("Msg: %s\n" % msg)

    #we need this to update pagelinks cache:
    self.request.args = self.request.form = self.request.setup_args({})
    self.request.redirectedOutput(page.send_page, self.request, content_only=1)

    return xmlrpclib.Boolean(1)

