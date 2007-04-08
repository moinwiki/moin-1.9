"""
    MoinMoin - AttachList Macro

    A macro to produce a list of attached files

    Usage: [[AttachList([pagename,mime_type])]]

    If pagename isn't set, the current pagename is used.
    If mime_type isn't given, all files are listed.

    @copyright: 2004 Jacob Cohen, Nigel Metheringham,
                2006 Reimar Bauer
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.action.AttachFile import _build_filelist

def execute(macro, args):
    # defaults if we don't get anything better
    pagename = macro.formatter.page.page_name
    mime_type = '*'
    if args:
        args = args.split(',')
        if args[0].strip():
            pagename = args[0].strip()
        if len(args) > 1 and args[1].strip():
            mime_type = args[1].strip()
    return _build_filelist(macro.request, pagename, 0, 1, mime_type=mime_type)

