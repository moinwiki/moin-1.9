"""
    MoinMoin - AttachList Macro

    A macro to produce a list of attached files

    Usage: <<AttachList([pagename,mime_type])>>

    If pagename isn't set, the current pagename is used.
    If mime_type isn't given, all files are listed.

    @copyright: 2004 Jacob Cohen, Nigel Metheringham,
                2006-2013 MoinMoin:ReimarBauer
    @license: GNU GPL, see COPYING for details.
"""

import re

from MoinMoin.action.AttachFile import _build_filelist

def macro_AttachList(macro, pagename=None, mime_type=u'*', search_term=u'.+'):
    # defaults if we don't get anything better
    if not pagename:
        pagename = macro.formatter.page.page_name
    filterfn = re.compile(search_term, re.U).search
    return _build_filelist(macro.request, pagename, 0, 1, mime_type=mime_type, filterfn=filterfn)


