# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - System Administration

    Web interface to do MoinMoin system administration tasks.

    @copyright: 2001, 2003 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import wikiutil
from MoinMoin.util import pysupport
from MoinMoin.userform import do_user_browser
from MoinMoin.action.AttachFile import do_admin_browser

Dependencies = ["time"]

def execute(macro, args):
    _ = macro.request.getText
    request = macro.request

    # do not show system admin to users not in superuser list
    if not request.user.isSuperUser():
        return ''

    result = []
    _MENU = {
        'attachments': (("File attachment browser"), do_admin_browser),
        'users': (("User account browser"), do_user_browser),
    }
    choice = request.form.get('sysadm', [None])[0]

    # create menu
    menuitems = [(label, id) for id, (label, handler) in _MENU.items()]
    menuitems.sort()
    for label, id in menuitems:
        if id == choice:
            result.append(macro.formatter.strong(1))
            result.append(macro.formatter.text(label))
            result.append(macro.formatter.strong(0))
        else:
            result.append(wikiutil.link_tag(request, "%s?sysadm=%s" % (macro.formatter.page.page_name, id), label))
        result.append('<br>')
    result.append('<br>')

    # add chosen content
    if _MENU.has_key(choice):
        result.append(_MENU[choice][1](request))

    return macro.formatter.rawHTML(''.join(result))

