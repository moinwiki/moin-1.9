# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Wiki Security Interface and Access Control Lists


    This implements the basic interface for user permissions and
    system policy. If you want to define your own policy, inherit
    from the base class 'Permissions', so that when new permissions
    are defined, you get the defaults.

    Then assign your new class to "SecurityPolicy" in wikiconfig;
    and I mean the class, not an instance of it!

    @copyright: 2000-2004 Juergen Hermann <jh@web.de>,
                2003-2008 MoinMoin:ThomasWaldmann,
                2003 Gustavo Niemeyer,
                2005 Oliver Graf,
                2007 Alexander Schremmer
    @license: GNU GPL, see COPYING for details.
"""

import re

from MoinMoin import wikiutil, user
from MoinMoin.Page import Page

#############################################################################
### Basic Permissions Interface -- most features enabled by default
#############################################################################

def _check(request, pagename, username, right):
    """ Check <right> access permission for user <username> on page <pagename>

    For cfg.acl_hierarchic=False we just check the page in question.

    For cfg.acl_hierarchic=True we, we check each page in the hierarchy. We
    start with the deepest page and recurse to the top of the tree.
    If one of those permits, True is returned.

    For both configurations, we check acl_rights_before before the page/default
    acl and acl_rights_after after the page/default acl, of course.

    This method should not be called by users, use __getattr__ instead.

    @param request: the current request object
    @param pagename: pagename to get permissions from
    @param username: the user name
    @param right: the right to check

    @rtype: bool
    @return: True if you have permission or False
    """
    cache = request.cfg.cache
    allowed = cache.acl_rights_before.may(request, username, right)
    if allowed is not None:
        return allowed

    if request.cfg.acl_hierarchic:
        pages = pagename.split('/') # create page hierarchy list
        some_acl = False
        for i in range(len(pages), 0, -1):
            # Create the next pagename in the hierarchy
            # starting at the leaf, going to the root
            name = '/'.join(pages[:i])
            # Get page acl and ask for permission
            acl = Page(request, name).getACL(request)
            if acl.acl:
                some_acl = True
                allowed = acl.may(request, username, right)
                if allowed is not None:
                    return allowed
                # If the item has an acl (even one that doesn't match) we *do not*
                # check the parents. We only check the parents if there's no acl on
                # the item at all.
                break
        if not some_acl:
            allowed = cache.acl_rights_default.may(request, username, right)
            if allowed is not None:
                return allowed
    else:
        if request.page is not None and pagename == request.page.page_name:
            p = request.page # reuse is good
        else:
            p = Page(request, pagename)
        acl = p.getACL(request) # this will be fast in a reused page obj
        allowed = acl.may(request, username, right)
        if allowed is not None:
            return allowed

    allowed = cache.acl_rights_after.may(request, username, right)
    if allowed is not None:
        return allowed

    return False


class Permissions:
    """ Basic interface for user permissions and system policy.

    Note that you still need to allow some of the related actions, this
    just controls their behavior, not their activation.

    When sub classing this class, you must extend the class methods, not
    replace them, or you might break the acl in the wiki. Correct sub
    classing looks like this:

    def read(self, pagename):
        # Your special security rule
        if something:
            return false

        # Do not return True or you break acl!
        # This call will use the default acl rules
        return Permissions.read(pagename)
    """

    def __init__(self, user):
        self.name = user.name
        self.request = user._request

    def save(self, editor, newtext, rev, **kw):
        """ Check whether user may save a page.

        `editor` is the PageEditor instance, the other arguments are
        those of the `PageEditor.saveText` method.

        @param editor: PageEditor instance.
        @param newtext: new page text, you can enable of disable saving according
            to the content of the text, e.g. prevent link spam.
        @param rev: new revision number? XXX
        @param kw: XXX
        @rtype: bool
        @return: True if you can save or False
        """
        return self.write(editor.page_name)

    def __getattr__(self, attr):
        """ Shortcut to export getPermission function for all known ACL rights

        if attr is one of the rights in acl_rights_valid, then return a
        checking function for it. Else raise an AttributeError.

        @param attr: one of ACL rights as defined in acl_rights_valid
        @rtype: function
        @return: checking function for that right, accepting a pagename
        """
        request = self.request
        if attr not in request.cfg.acl_rights_valid:
            raise AttributeError, attr
        return lambda pagename: _check(self.request, pagename, self.name, attr)


# make an alias for the default policy
Default = Permissions


class AccessControlList:
    ''' Access Control List

    Control who may do what on or with a wiki page.

    Syntax of an ACL string:

        [+|-]User[,User,...]:[right[,right,...]] [[+|-]SomeGroup:...] ...
        ... [[+|-]Known:...] [[+|-]All:...]

        "User" is a user name and triggers only if the user matches. Up
        to version 1.2 only WikiNames were supported, as of version 1.3,
        any name can be used in acl lines, including name with spaces
        using esoteric languages.

        "SomeGroup" is a page name matching cfg.page_group_regex with
         some lines in the form " * Member", defining the group members.

        "Known" is a group containing all valid / known users.

        "All" is a group containing all users (Known and Anonymous users).

        "right" may be an arbitrary word like read, write, delete, admin.
        Only words in cfg.acl_validrights are accepted, others are
        ignored. It is allowed to specify no rights, which means that no
        rights are given.

    How ACL is processed

        When some user is trying to access some ACL-protected resource,
        the ACLs will be processed in the order they are found. The first
        matching ACL will tell if the user has access to that resource
        or not.

        For example, the following ACL tells that SomeUser is able to
        read and write the resources protected by that ACL, while any
        member of SomeGroup (besides SomeUser, if part of that group)
        may also admin that, and every other user is able to read it.

            SomeUser:read,write SomeGroup:read,write,admin All:read

        In this example, SomeUser can read and write but can not admin,
        revert or delete pages. Rights that are NOT specified on the
        right list are automatically set to NO.

    Using Prefixes

        To make the system more flexible, there are also two modifiers:
        the prefixes "+" and "-".

            +SomeUser:read -OtherUser:write

        The acl line above will grant SomeUser read right, and OtherUser
        write right, but will NOT block automatically all other rights
        for these users. For example, if SomeUser ask to write, the
        above acl line does not define if he can or can not write. He
        will be able to write if acl_rights_before or acl_rights_after
        allow this (see configuration options).

        Using prefixes, this acl line:

            SomeUser:read,write SomeGroup:read,write,admin All:read

        Can be written as:

            -SomeUser:admin SomeGroup:read,write,admin All:read

        Or even:

            +All:read -SomeUser:admin SomeGroup:read,write,admin

        Notice that you probably will not want to use the second and
        third examples in ACL entries of some page. They are very
        useful on the moin configuration entries though.

   Configuration options

       cfg.acl_rights_default
           It is is ONLY used when no other ACLs are given.
           Default: "Known:read,write,delete All:read,write",

       cfg.acl_rights_before
           When the page has ACL entries, this will be inserted BEFORE
           any page entries.
           Default: ""

       cfg.acl_rights_after
           When the page has ACL entries, this will be inserted AFTER
           any page entries.
           Default: ""

       cfg.acl_rights_valid
           These are the acceptable (known) rights (and the place to
           extend, if necessary).
           Default: ["read", "write", "delete", "admin"]
    '''

    special_users = ["All", "Known", "Trusted"] # order is important

    def __init__(self, cfg, lines=[]):
        """Initialize an ACL, starting from <nothing>.
        """
        if lines:
            self.acl = [] # [ ('User', {"read": 0, ...}), ... ]
            self.acl_lines = []
            for line in lines:
                self._addLine(cfg, line)
        else:
            self.acl = None
            self.acl_lines = None

    def _addLine(self, cfg, aclstring, remember=1):
        """ Add another ACL line

        This can be used in multiple subsequent calls to process longer lists.

        @param cfg: current config
        @param aclstring: acl string from page or cfg
        @param remember: should add the line to self.acl_lines
        """

        # Remember lines
        if remember:
            self.acl_lines.append(aclstring)

        # Iterate over entries and rights, parsed by acl string iterator
        acliter = ACLStringIterator(cfg.acl_rights_valid, aclstring)
        for modifier, entries, rights in acliter:
            if entries == ['Default']:
                self._addLine(cfg, cfg.acl_rights_default, remember=0)
            else:
                for entry in entries:
                    rightsdict = {}
                    if modifier:
                        # Only user rights are added to the right dict.
                        # + add rights with value of 1
                        # - add right with value of 0
                        for right in rights:
                            rightsdict[right] = (modifier == '+')
                    else:
                        # All rights from acl_rights_valid are added to the
                        # dict, user rights with value of 1, and other with
                        # value of 0
                        for right in cfg.acl_rights_valid:
                            rightsdict[right] = (right in rights)
                    self.acl.append((entry, rightsdict))

    def may(self, request, name, dowhat):
        """ May <name> <dowhat>? Returns boolean answer.

            Note: this check does NOT include the acl_rights_before / _after ACL,
                  but it WILL use acl_rights_default if there is no (page) ACL.
        """
        if self.acl is None: # no #acl used on Page
            acl = request.cfg.cache.acl_rights_default.acl
        else: # we have a #acl on the page (self.acl can be [] if #acl is empty!)
            acl = self.acl

        groups = request.groups

        allowed = None
        for entry, rightsdict in acl:
            if entry in self.special_users:
                handler = getattr(self, "_special_"+entry, None)
                allowed = handler(request, name, dowhat, rightsdict)
            elif entry in groups:
                if name in groups[entry]:
                    allowed = rightsdict.get(dowhat)
                else:
                    for special in self.special_users:
                        if special in entry:
                            handler = getattr(self, "_special_" + special, None)
                            allowed = handler(request, name, dowhat, rightsdict)
                            break # order of self.special_users is important
            elif entry == name:
                allowed = rightsdict.get(dowhat)
            if allowed is not None:
                return allowed
        return allowed # should be None

    def getString(self, b='#acl ', e='\n'):
        """print the acl strings we were fed with"""
        if self.acl_lines:
            acl_lines = ''.join(["%s%s%s" % (b, l, e) for l in self.acl_lines])
        else:
            acl_lines = ''
        return acl_lines

    def _special_All(self, request, name, dowhat, rightsdict):
        return rightsdict.get(dowhat)

    def _special_Known(self, request, name, dowhat, rightsdict):
        """ check if user <name> is known to us,
            that means that there is a valid user account present.
            works for subscription emails.
        """
        if user.getUserId(request, name): # is a user with this name known?
            return rightsdict.get(dowhat)
        return None

    def _special_Trusted(self, request, name, dowhat, rightsdict):
        """ check if user <name> is known AND has logged in using a trusted
            authentication method.
            Does not work for subsription emails that should be sent to <user>,
            as he is not logged in in that case.
        """
        if (request.user.name == name and
            request.user.auth_method in request.cfg.auth_methods_trusted):
            return rightsdict.get(dowhat)
        return None

    def __eq__(self, other):
        return self.acl_lines == other.acl_lines

    def __ne__(self, other):
        return self.acl_lines != other.acl_lines


class ACLStringIterator:
    """ Iterator for acl string

    Parse acl string and return the next entry on each call to
    next. Implement the Iterator protocol.

    Usage:
        iter = ACLStringIterator(cfg.acl_rights_valid, 'user name:right')
        for modifier, entries, rights in iter:
            # process data
    """

    def __init__(self, rights, aclstring):
        """ Initialize acl iterator

        @param rights: the acl rights to consider when parsing
        @param aclstring: string to parse
        """
        self.rights = rights
        self.rest = aclstring.strip()
        self.finished = 0

    def __iter__(self):
        """ Required by the Iterator protocol """
        return self

    def next(self):
        """ Return the next values from the acl string

        When the iterator is finished and you try to call next, it
        raises a StopIteration. The iterator finish as soon as the
        string is fully parsed or can not be parsed any more.

        @rtype: 3 tuple - (modifier, [entry, ...], [right, ...])
        @return: values for one item in an acl string
        """
        # Handle finished state, required by iterator protocol
        if self.rest == '':
            self.finished = 1
        if self.finished:
            raise StopIteration

        # Get optional modifier [+|-]entries:rights
        modifier = ''
        if self.rest[0] in ('+', '-'):
            modifier, self.rest = self.rest[0], self.rest[1:]

        # Handle the Default meta acl
        if self.rest.startswith('Default ') or self.rest == 'Default':
            self.rest = self.rest[8:]
            entries, rights = ['Default'], []

        # Handle entries:rights pairs
        else:
            # Get entries
            try:
                entries, self.rest = self.rest.split(':', 1)
            except ValueError:
                self.finished = 1
                raise StopIteration("Can't parse rest of string")
            if entries == '':
                entries = []
            else:
                # TODO strip each entry from blanks?
                entries = entries.split(',')

            # Get rights
            try:
                rights, self.rest = self.rest.split(' ', 1)
                # Remove extra white space after rights fragment,
                # allowing using multiple spaces between items.
                self.rest = self.rest.lstrip()
            except ValueError:
                rights, self.rest = self.rest, ''
            rights = [r for r in rights.split(',') if r in self.rights]

        return modifier, entries, rights


def parseACL(request, text):
    """ Parse acl lines from text and return ACL object """
    pi, dummy = wikiutil.get_processing_instructions(text)
    acl_lines = [args for verb, args in pi if verb == 'acl']
    return AccessControlList(request.cfg, acl_lines)
