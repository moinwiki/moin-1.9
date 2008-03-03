# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Login form

    @copyright: 2001-2004 Juergen Hermann <jh@web.de>,
                2003-2007 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.widget import html


class Login:
    """ User login. """

    def __init__(self, request):
        """ Initialize user settings form.
        """
        self.request = request
        self._ = request.getText
        self.cfg = request.cfg

    def make_row(self, label, cell, **kw):
        """ Create a row in the form table.
        """
        self._table.append(html.TR().extend([
            html.TD(**kw).extend([html.B().append(label), '   ']),
            html.TD().extend(cell),
        ]))


    def asHTML(self):
        """ Create the complete HTML form code. """
        _ = self._
        request = self.request
        sn = request.getScriptname()
        pi = request.getPathinfo()
        action = u"%s%s" % (sn, pi)
        hints = []
        for authm in request.cfg.auth:
            hint = authm.login_hint(request)
            if hint:
                hints.append(hint)
        self._form = html.FORM(action=action, name="loginform")
        self._table = html.TABLE(border="0")

        # Use the user interface language and direction
        lang_attr = request.theme.ui_lang_attr()
        self._form.append(html.Raw('<div class="userpref"%s>' % lang_attr))

        self._form.append(html.INPUT(type="hidden", name="action", value="login"))
        self._form.append(self._table)
        for hint in hints:
            self._form.append(html.P().append(html.Raw(hint)))
        self._form.append(html.Raw("</div>"))

        cfg = request.cfg
        if 'username' in cfg.auth_login_inputs:
            self.make_row(_('Name'), [
                html.INPUT(
                    type="text", size="32", name="name",
                ),
            ])

        if 'password' in cfg.auth_login_inputs:
            self.make_row(_('Password'), [
                html.INPUT(
                    type="password", size="32", name="password",
                ),
            ])

        if 'openid_identifier' in cfg.auth_login_inputs:
            self.make_row(_('OpenID'), [
                html.INPUT(
                    type="text", size="32", name="openid_identifier",
                    id="openididentifier"
                ),
            ])

        self.make_row('', [
            html.INPUT(
                type="submit", name='login', value=_('Login')
            ),
        ])

        return unicode(self._form)

def getLogin(request):
    """ Return HTML code for the login. """
    return Login(request).asHTML()
