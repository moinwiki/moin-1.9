# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - modernized_cms theme

    @copyright: 2009 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.theme.modernized import Theme as ThemeBase

class Theme(ThemeBase):

    name = "modernized" # we tell that we are 'modernized', so we use its static data

    def onlyloggedin(method):
        """ decorator that returns empty string for not logged-in users,
            otherwise it calls the decorated method
        """
        return lambda self, *args, **kwargs: (
            self.request.user.valid and self.request.user.name and method(self, *args, **kwargs)
            or
            ''
            )

    interwiki = onlyloggedin(ThemeBase.interwiki)
    title = onlyloggedin(ThemeBase.title)
    username = onlyloggedin(ThemeBase.username)
    pageinfo = onlyloggedin(ThemeBase.pageinfo)
    editbar = onlyloggedin(ThemeBase.editbar)


def execute(request):
    return Theme(request)

