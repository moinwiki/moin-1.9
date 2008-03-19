# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Login form and user browser

    @copyright: 2001-2004 Juergen Hermann <jh@web.de>,
                2003-2007 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import time
from MoinMoin import user, util, wikiutil
import MoinMoin.events as events
from MoinMoin.widget import html

# compatibility
from MoinMoin.userform.login import getLogin
from MoinMoin.userform.admin import do_user_browser
