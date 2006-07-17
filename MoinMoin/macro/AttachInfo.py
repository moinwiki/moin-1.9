"""
    MoinMoin - AttachList Macro

    A macro to produce information about attached pages

    Usage: [[AttachInfo]]

    @copyright: 2004 Jacob Cohen, Nigel Metheringham
    @license: GNU GPL, see COPYING for details
"""

from MoinMoin.action.AttachFile import info

def execute(macro, args):
    pagename = macro.formatter.page.page_name
    if args:
        pagename = args
    result = info(pagename, macro.request)
    return result

