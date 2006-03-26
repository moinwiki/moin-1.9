# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - UserPreferences action
    
    This is a simple plugin, that adds a "UserPreferences" action.
    This action will display the UserPreferences page (or appropriate
    page in the reader's language), so that the user can login, or
    change his/her preferences.

    However, as it is an action, the page that is displayed is not 
    changed. After submitting the form, the user is presented the
    same page he/she was seeing before, and the trail is not modified.

    @copyright: 2006 by Radomir Dopieralski
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import wikiutil

def execute(pagename, request):
    page = wikiutil.getSysPage(request, 'UserPreferences')
    page.send_page(request)

