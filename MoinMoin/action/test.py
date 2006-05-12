# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - test action

    This action allows you to run some tests and show some data about your system.

    If you don't want this action to be available due to system privacy reasons,
    do this in your wiki/farm config:

    actions_excluded = ["test"]
    
    @copyright: 2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import config
from MoinMoin.wikitest import runTest
from MoinMoin.action import ActionBase

class test(ActionBase):
    """ test and show info action

    Note: the action name is the class name
    """
    def do_action(self):
        """ run tests """
        request = self.request
        request.http_headers(["Content-type: text/plain; charset=%s" % config.charset])
        request.write('MoinMoin Diagnosis\n======================\n\n')
        runTest(request)
        return True, ""

    def do_action_finish(self, success):
        """ we don't want to do the default stuff, but just NOTHING """
        pass

def execute(pagename, request):
    """ Glue code for actions """
    test(pagename, request).render()

