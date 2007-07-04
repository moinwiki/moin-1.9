# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - dialog

    @copyright: 2004 Nir Soffer <nirs@freeshell.org>
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.widget import base


class Dialog(base.Widget):
    """ Dialog for user interaction.

    Use a dialog when you want to present and get data to the user.

    Currently this is little more than wrapper around a string.
    """

    def __init__(self, request, **kw):
        """ Initialize a dialog

        @param request: current request
        @keyword content: dialong content
        """
        base.Widget.__init__(self, request, **kw)
        self.content = kw.get('content', '')

    def render(self):
        return u'<div class="dialog">\n%s\n</div>\n' % unicode(self.content)


class Status(base.Widget):
    """ Status widget

    Use Status when you want to present to the user status information,
    and no interaction needed.

    A user might choose to turn of status display in his user pref (not
    implemented yet).

    Currently this is little more than wrapper around a string.
    """

    def __init__(self, request, **kw):
        """ Initialize a dialog

        @param request: current request
        @keyword content: status message content
        """
        base.Widget.__init__(self, request, **kw)
        self.content = kw.get('content', '')

    def render(self):
        return u'<p class="status">%s</p>\n' % unicode(self.content)

