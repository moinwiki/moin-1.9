"""
    MoinMoin - AttachList Macro

    A macro to produce a list of attached pages

    Usage: [[AttachList]]

    @copyright: 2004 Jacob Cohen, Nigel Metheringham
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.action.AttachFile import _build_filelist

def execute(macro, args):
    pagename = macro.formatter.page.page_name
    if args:
        pagename = args
    result = _build_filelist(macro.request, pagename, 0, 1)
    return result

