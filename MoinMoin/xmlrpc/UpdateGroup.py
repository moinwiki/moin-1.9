# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Wiki XMLRPC group creation

    @copyright: 2005-2006 Bastian Blank, Florian Festi, Thomas Waldmann
    @license: GNU GPL, see COPYING for details.
"""

import sys, xmlrpclib

from MoinMoin import log
logging = log.getLogger(__name__)

from MoinMoin.PageEditor import PageEditor

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

    pagename = self._instr(groupname)

    # also check ACLs
    if not self.request.user.may.write(pagename):
        return xmlrpclib.Fault(1, "You are not allowed to edit this page")

    # check if groupname matches page_group_regex
    if not self.request.cfg.cache.page_group_regexact.search(groupname):
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
        logging.error("SaveError msg: %s" % str(msg))
        return xmlrpclib.Fault(3, msg)
    if msg:
        logging.debug("saveText msg: %s" % msg)

    #we need this to update pagelinks cache:
    #self.request.args = self.request.form = self.request.setup_args()
    self.request.redirectedOutput(page.send_page, content_only=1)

    return xmlrpclib.Boolean(1)

