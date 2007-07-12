# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - switch user form

    @copyright: 2001-2004 Juergen Hermann <jh@web.de>,
                2003-2007 MoinMoin:ThomasWaldmann
                2007      MoinMoin:JohannesBerg
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import user, util, wikiutil
from MoinMoin.widget import html
from MoinMoin.userprefs import UserPrefBase

class Settings(UserPrefBase):
    def __init__(self, request):
        """ Initialize setuid settings form. """
        UserPrefBase.__init__(self, request)
        self.request = request
        self._ = request.getText
        self.cfg = request.cfg
        self.title = self._("Switch user")

    def _is_super_user(self):
        return (self.request.user.isSuperUser() or
                (not self.request._setuid_real_user is None
                 and (self.request._setuid_real_user.isSuperUser())))

    allowed = _is_super_user

    def handle_form(self):
        _ = self._
        form = self.request.form

        if form.has_key('cancel'):
            return

        if (wikiutil.checkTicket(self.request, self.request.form['ticket'][0]) and
            self.request.request_method == 'POST' and self._is_super_user()):
            su_user = form.get('selected_user', [''])[0]
            uid = user.getUserId(self.request, su_user)
            if not uid:
                return _("No user selected")
            if (not self.request._setuid_real_user is None
                and uid == self.request._setuid_real_user.id):
                del self.request.session['setuid']
                self.request.user = self.request._setuid_real_user
                self.request._setuid_real_user = None
            else:
                theuser = user.User(self.request, uid, auth_method='setuid')
                theuser.disabled = None
                self.request.session['setuid'] = uid
                self.request._setuid_real_user = self.request.user
                # now continue as the other user
                self.request.user = theuser
            return  _("You can now change the settings of the selected user account; log out to get back to your account.")
        else:
            return None


    def _user_select(self):
        options = []
        users = user.getUserList(self.request)
        realuid = None
        if hasattr(self.request, '_setuid_real_user') and self.request._setuid_real_user:
            realuid = self.request._setuid_real_user.id
        else:
            realuid = self.request.user.id
        for uid in users:
            if uid != realuid:
                name = user.User(self.request, id=uid).name # + '/' + uid # for debugging
                options.append((name, name))
        options.sort()

        size = min(5, len(options))
        current_user = self.request.user.name
        return util.web.makeSelection('selected_user', options, current_user, size=size)

    def _make_form(self):
        """ Create the FORM, and the TABLE with the input fields
        """
        sn = self.request.getScriptname()
        pi = self.request.getPathinfo()
        action = u"%s%s" % (sn, pi)
        self._form = html.FORM(action=action)

        # Use the user interface language and direction
        lang_attr = self.request.theme.ui_lang_attr()
        self._form.append(html.Raw('<div class="userpref"%s>' % lang_attr))

        self._form.append(html.INPUT(type="hidden", name="action", value="userprefs"))
        self._form.append(html.INPUT(type="hidden", name="handler", value="suid"))
        self._form.append(html.Raw("</div>"))


    def create_form(self):
        """ Create the complete HTML form code. """
        _ = self._
        self._make_form()

        if (self.request.user.isSuperUser() or
            (not self.request._setuid_real_user is None and
             self.request._setuid_real_user.isSuperUser())):
            ticket = wikiutil.createTicket(self.request)
            self._form.append(html.P().append(
                              html.Text(_('As the superuser, you can temporarily '
                                          'assume the identity of another user.'))))
            self._form.append(html.P().append(self._user_select()))
            self._form.append(html.INPUT(type="hidden", name="ticket", value="%s" % ticket))
            self._form.append(html.INPUT(type="submit", name="select_user",
                                         value=_('Select User')))
            self._form.append(html.Text(' '))
            self._form.append(html.INPUT(type="submit", name="cancel",
                                         value=_('Cancel')))
            return unicode(self._form)

        return u''
