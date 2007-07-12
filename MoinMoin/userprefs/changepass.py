# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Password change preferences plugin

    @copyright: 2001-2004 Juergen Hermann <jh@web.de>,
                2003-2007 MoinMoin:ThomasWaldmann
                2007      MoinMoin:JohannesBerg
    @license: GNU GPL, see COPYING for details.
"""

import time
from MoinMoin import user, wikiutil
from MoinMoin.widget import html
from MoinMoin.userprefs import UserPrefBase


class Settings(UserPrefBase):
    def __init__(self, request):
        """ Initialize password change form. """
        UserPrefBase.__init__(self, request)
        self.request = request
        self._ = request.getText
        _ = request.getText
        self.cfg = request.cfg
        self.title = _("Change password")


    def allowed(self):
        return (not 'password' in self.cfg.user_form_remove and
                not 'password' in self.cfg.user_form_disable and
                UserPrefBase.allowed(self) and
                not 'password' in self.request.user.auth_attribs)


    def handle_form(self):
        _ = self._
        form = self.request.form

        if form.has_key('cancel'):
            return

        if self.request.request_method != 'POST':
            return

        password = form.get('password', [''])[0]
        password2 = form.get('password2', [''])[0]

        # Check if password is given and matches with password repeat
        if password != password2:
            return _("Passwords don't match!")

        # Encode password
        if password and not password.startswith('{SHA}'):
            try:
                self.request.user.enc_password = user.encodePassword(password)
                self.request.user.save()
                return _("Your password has been changed.")
            except UnicodeError, err:
                # Should never happen
                return "Can't encode password: %s" % str(err)


    def _make_form(self):
        """ Create the FORM, and the TABLE with the input fields
        """
        _ = self._
        sn = self.request.getScriptname()
        pi = self.request.getPathinfo()
        action = u"%s%s" % (sn, pi)
        self._form = html.FORM(action=action)
        self._table = html.TABLE(border="0")

        # Use the user interface language and direction
        lang_attr = self.request.theme.ui_lang_attr()
        self._form.append(html.Raw('<div class="userpref"%s>' % lang_attr))

        self._form.append(html.STRONG().append(html.P().append(html.Text(
            _("To change your password, enter a new password twice.")))))

        self._form.append(self._table)
        self._form.append(html.Raw("</div>"))


    def _make_row(self, label, cell, **kw):
        """ Create a row in the form table.
        """
        self._table.append(html.TR().extend([
            html.TD(**kw).extend([html.B().append(label), '   ']),
            html.TD().extend(cell),
        ]))


    def create_form(self, create_only=False, recover_only=False):
        """ Create the complete HTML form code. """
        _ = self._
        self._make_form()

        self._make_row(_('Password'),
                       [html.INPUT(type="password", size=36, name="password")])
        self._make_row(_('Password repeat'),
                       [html.INPUT(type="password", size=36, name="password2")])

        self._form.append(html.INPUT(type="hidden", name="action",
                                     value="userprefs"))
        self._form.append(html.INPUT(type="hidden", name="handler",
                                     value="changepass"))

        # Add buttons
        self._form.append(html.INPUT(type="hidden", name="action",
                                     value="userprefs"))
        self._form.append(html.INPUT(type="hidden", name="handler",
                                     value="changepass"))

        self._make_row('', [
                html.INPUT(type="submit", name='save', value=_("Save")),
                html.INPUT(type="submit", name='cancel', value=_("Cancel")),
              ])

        return unicode(self._form)
