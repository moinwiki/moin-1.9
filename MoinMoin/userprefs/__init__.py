# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - User preferences implementation

    See also MoinMoin/action/userprefs.py

    @copyright: 2007 MoinMoin:Johannesberg
    @license: GNU GPL, see COPYING for details.
"""
from MoinMoin.util import pysupport


# create a list of extension actions from the package directory
modules = pysupport.getPackageModules(__file__)


class UserPrefBase(object):
    '''
        Base class for Settings objections

        To get a new page in the wiki settings, create
        a new 'userprefs' plugin and in it declare a class
        named 'Settings' that inherits from this class.
    '''
    def __init__(self, request):
        '''
            Initialise a settings object. This should set the
            object's title (which is displayed in the list of
            possible settings)
        '''
        self.request = request
        self._ = request.getText
        title = 'No name set'

    def create_form(self):
        '''
            This method should return HTML code for at least
            one form. Each created form *must* contained the
            hidden fields
              * action: set to "userprefs"
              * handler: set to the plugin name
        '''
        raise NotImplementedError

    def handle_form(self, request):
        '''
            When any of the created forms is submitted and the
            hidden fields are set correctly (see create_form)
            this method will be invoked to handle the user's
            input. Note that GET requests are also handed to
            this method, so if you require POST check that.
        '''
        raise NotImplementedError

    def allowed(self):
        '''
            Not all preferences are applicable to all users,
            this method is called to determine whether the
            title should be listed or not and whether
            submissions are accepted.
        '''
        return True
