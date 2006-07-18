# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Wiki Synchronisation

    @copyright: 2006 by MoinMoin:AlexanderSchremmer
    @license: GNU GPL, see COPYING for details.
"""

# XXX add some code here
class Tag(object):
    """ This class is used to store information about merging state. """
    pass


class TagStore(object):
    """ This class manages the storage of tags. """

    def __init__(self, page):
        self.page = page

    def add(self, **kwargs):
        # XXX add some code here
        print "Got tag for page %r: %r" % (self.page, kwargs)
