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
        _ = self._
        self.title = _("Switch user")
        self.name = 'suid'

    def allowed(self):
        return (UserPrefBase.allowed(self) and
                self.request.user.isSuperUser() or
                (not self.request._setuid_real_user is None and
                 (self.request._setuid_real_user.isSuperUser())))

    def handle_form(self):
        _ = self._
        form = self.request.form

        if 'cancel' in form:
            return

        if (wikiutil.checkTicket(self.request, self.request.form['ticket'][0])
            and self.request.request_method == 'POST'):
            uid = form.get('selected_user', [''])[0]
            if not uid:
                return 'error', _("No user selected")
            theuser = user.User(self.request, uid, auth_method='setuid')
            if not theuser or not theuser.exists():
                return 'error', _("No user selected")
            # set valid to True so superusers can even switch
            # to disable accounts
            theuser.valid = True
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
                name = user.User(self.request, id=uid).name
                options.append((uid, name))
        options.sort(lambda x, y: cmp(x[1].lower(), y[1].lower()))

        size = min(5, len(options))
        current_user = self.request.user.id

        if not options:
            _ = self._
            self._only = True
            return _("You are the only user.")

        self._only = False
        return util.web.makeSelection('selected_user', options, current_user, size=size)

    def create_form(self):
        """ Create the complete HTML form code. """
        _ = self._
        form = self.make_form(html.Text(_('As a superuser, you can temporarily '
                                          'assume the identity of another user.')))

        ticket = wikiutil.createTicket(self.request)
        self.make_row(_('Select User'), [self._user_select()], valign="top")
        form.append(html.INPUT(type="hidden", name="ticket", value="%s" % ticket))
        if not self._only:
            buttons = [html.INPUT(type="submit", name="select_user",
                                  value=_('Select User')),
                       ' ', ]
        else:
            buttons = []
        buttons.append(html.INPUT(type="submit", name="cancel",
                                  value=_('Cancel')))
        self.make_row('', buttons)
        return unicode(form)
