# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Wiki Security Interface

    This implements the basic interface for user permissions and
    system policy. If you want to define your own policy, inherit
    from the base class 'Permissions', so that when new permissions
    are defined, you get the defaults.

    Then assign your new class to "SecurityPolicy" in wikiconfig;
    and I mean the class, not an instance of it!

    @copyright: 2000-2004 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

#############################################################################
### Basic Permissions Interface -- most features enabled by default
#############################################################################


class Permissions:
    """ Basic interface for user permissions and system policy.

        Note that you still need to allow some of the related actions, this
        just controls their behaviour, not their activation.
    """

    def __init__(self, user):
        """ Calculate the permissons `user` has.
        """
        from MoinMoin.Page import Page
        self.Page = Page
        self.name = user.name
        self.request = user._request

    def save(self, editor, newtext, rev, **kw):
        """ Check whether user may save a page.

            `editor` is the PageEditor instance, the other arguments are
            those of the `PageEditor.saveText` method.
        """
        return self.write(editor.page_name)

    def __getattr__(self, attr):
        """ if attr is one of the rights in acl_rights_valid, then return a
            checking function for it. Else raise an error.
        """
        request = self.request
        Page = self.Page
        if attr in request.cfg.acl_rights_valid:
            return lambda pagename, Page=Page, request=request, attr=attr: Page(request, pagename).getACL(request).may(request, self.name, attr)
        else:
            raise AttributeError, attr
        

# make an alias for the default policy
Default = Permissions

