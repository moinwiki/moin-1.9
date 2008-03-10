# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - User preferences implementation

    See also MoinMoin/action/userprefs.py

    @copyright: 2007 MoinMoin:Johannesberg
    @license: GNU GPL, see COPYING for details.
"""
from MoinMoin.util import pysupport
from MoinMoin.widget import html


# create a list of extension actions from the package directory
modules = pysupport.getPackageModules(__file__)


class UserPrefBase(object):
    '''
        Base class for Settings objects

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
        self.name = None
        self.title = 'No name set'

    def create_form(self):
        '''
            This method should return HTML code for at least
            one form. Each created form *must* contain the
            hidden fields
              * action: set to "userprefs"
              * handler: set to the plugin name
            It can additionally contain the hidden field
            'sub' set to the plugin name if the plugin needs
            multiple forms (wizard-like.)
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
        return self.request.user and self.request.user.valid

    def make_form(self, explanation=None):
        '''
            To have a consistent UI, use this method for most
            preferences forms and then call make_row(). See
            existing plugins, e.g. changepass.py.
        '''
        action = self.request.page.url(self.request)
        _form = html.FORM(action=action)
        _form.append(html.INPUT(type="hidden", name="action", value="userprefs"))
        _form.append(html.INPUT(type="hidden", name="handler", value=self.name))

        self._table = html.TABLE(border="0")

        # Use the user interface language and direction
        lang_attr = self.request.theme.ui_lang_attr()
        _form.append(html.Raw('<div class="userpref"%s>' % lang_attr))
        para = html.P()
        _form.append(para)
        if explanation:
            para.append(explanation)

        para.append(self._table)
        _form.append(html.Raw("</div>"))

        return _form

    def make_row(self, label, cell, **kw):
        '''
           Create a row in the form table.
        '''
        self._table.append(html.TR().extend([
            html.TD(**kw).extend([html.B().append(label), '   ']),
            html.TD().extend(cell),
        ]))
