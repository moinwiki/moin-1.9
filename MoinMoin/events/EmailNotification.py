# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - email notification plugin from event system

    This code sends email notifications about page changes.

@copyright: 2007 by Karol Nowak <grywacz@gmail.com>
@license: GNU GPL, see COPYING for details.
"""

from MoinMoin.events import *

def handle(event):
    if event.__class__ is PageChangedEvent:
        print event