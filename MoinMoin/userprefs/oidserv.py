# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - OpenID preferences

    @copyright: 2007     MoinMoin:JohannesBerg
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import wikiutil, user
from MoinMoin.widget import html
from MoinMoin.userprefs import UserPrefBase
import base64


class Settings(UserPrefBase):
    def __init__(self, request):
        """ Initialize OpenID settings form. """
        UserPrefBase.__init__(self, request)
        self.request = request
        self._ = request.getText
        self.cfg = request.cfg
        _ = self._
        self.title = _("OpenID server")

    def allowed(self):
        if not self.request.cfg.openid_server_enabled:
            return False

        groups = self.request.groups
        openid_group_name = self.request.cfg.openid_server_restricted_users_group

        if openid_group_name and self.request.user.name not in groups.get(openid_group_name, []):
                return False

        return True

    def _handle_remove(self):
        _ = self.request.getText
        if not hasattr(self.request.user, 'openid_trusted_roots'):
            return
        roots = self.request.user.openid_trusted_roots[:]
        for root in self.request.user.openid_trusted_roots:
            name = "rm-%s" % root
            if name in self.request.form:
                roots.remove(root)
        self.request.user.openid_trusted_roots = roots
        self.request.user.save()
        return 'info', _("The selected websites have been removed.")

    def handle_form(self):
        _ = self._
        form = self.request.form

        if form.has_key('cancel'):
            return

        if self.request.request_method != 'POST':
            return

        if form.has_key('remove'):
            return self._handle_remove()

    def _make_form(self):
        action = "%s%s" % (self.request.script_root, self.request.path)
        _form = html.FORM(action=action)
        _form.append(html.INPUT(type="hidden", name="action", value="userprefs"))
        _form.append(html.INPUT(type="hidden", name="handler", value="oidserv"))
        return _form

    def _make_row(self, label, cell, **kw):
        """ Create a row in the form table.
        """
        self._table.append(html.TR().extend([
            html.TD(**kw).extend([html.B().append(label), '   ']),
            html.TD().extend(cell),
        ]))

    def _trust_root_list(self):
        _ = self.request.getText
        form = self._make_form()
        for root in self.request.user.openid_trusted_roots:
            display = base64.decodestring(root)
            name = 'rm-%s' % root
            form.append(html.INPUT(type="checkbox", name=name, id=name))
            form.append(html.LABEL(for_=name).append(html.Text(display)))
            form.append(html.BR())
        self._make_row(_("Trusted websites"), [form], valign='top')
        label = _("Remove selected")
        form.append(html.BR())
        form.append(html.INPUT(type="submit", name="remove", value=label))

    def create_form(self):
        """ Create the complete HTML form code. """
        _ = self._

        ret = html.P()
        # Use the user interface language and direction
        lang_attr = self.request.theme.ui_lang_attr()
        ret.append(html.Raw('<div %s>' % lang_attr))
        self._table = html.TABLE(border="0")
        ret.append(self._table)
        ret.append(html.Raw("</div>"))

        request = self.request

        if hasattr(request.user, 'openid_trusted_roots') and request.user.openid_trusted_roots:
            self._trust_root_list()

        form = self._make_form()
        label = _("Cancel")
        form.append(html.INPUT(type="submit", name='cancel', value=label))
        self._make_row('', [form])
        return unicode(ret)
