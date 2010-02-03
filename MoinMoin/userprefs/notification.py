# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Notification preferences

    @copyright: 2001-2004 Juergen Hermann <jh@web.de>,
                2003-2007 MoinMoin:ThomasWaldmann
                2007      MoinMoin:JohannesBerg
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import events, wikiutil
from MoinMoin.widget import html
from MoinMoin.userprefs import UserPrefBase


class Settings(UserPrefBase):
    def __init__(self, request):
        """ Initialize user settings form. """
        UserPrefBase.__init__(self, request)
        self.request = request
        self._ = request.getText
        self.cfg = request.cfg
        self.title = self._("Notification")
        self.name = 'notification'

    def _decode_pagelist(self, key):
        """ Decode list of pages from form input

        Each line is a page name, empty lines ignored.

        @param key: the form key to get
        @rtype: list of unicode strings
        @return: list of normalized names
        """
        text = self.request.form.get(key, '')
        text = text.replace('\r', '')
        items = []
        for item in text.split('\n'):
            item = item.strip()
            if not item:
                continue
            items.append(item)
        return items

    def _save_notification_settings(self):
        _ = self._
        form = self.request.form

        theuser = self.request.user
        if not theuser:
            return

        # subscription for page change notification
        theuser.subscribed_pages = self._decode_pagelist('subscribed_pages')

        # subscription to various events
        available = events.get_subscribable_events()
        theuser.email_subscribed_events = []
        theuser.jabber_subscribed_events = []
        types = {
            'email': theuser.email_subscribed_events,
            'jabber': theuser.jabber_subscribed_events
        }
        for tp in types:
            for evt in available:
                fieldname = 'subscribe:%s:%s' % (tp, evt)
                if fieldname in form:
                    types[tp].append(evt)
        # save data
        theuser.save()

        return 'info', _("Notification settings saved!")


    def handle_form(self):
        _ = self._
        request = self.request
        form = request.form

        if form.has_key('cancel'):
            return

        if request.method != 'POST':
            return

        if not wikiutil.checkTicket(request, form.get('ticket', '')):
            return

        if form.has_key('save'): # Save user profile
            return self._save_notification_settings()

    # form generation part

    def _event_select(self):
        """ Create event subscription list. """
        _ = self._

        types = []
        if self.cfg.mail_enabled and self.request.user.email:
            types.append(('email', _("'''Email'''", wiki=True)))
        if self.cfg.jabber_enabled and self.request.user.jid:
            types.append(('jabber', _("'''Jabber'''", wiki=True)))

        table = html.TABLE()
        header = html.TR()
        table.append(header)
        for name, descr in types:
            header.append(html.TH().append(html.Raw(descr)))
        header.append(html.TH(align='left').append(html.Raw(_("'''Event type'''", wiki=True))))

        event_list = events.get_subscribable_events()
        super = self.request.user.isSuperUser()

        # Create a list of (value, name) tuples for display as radiobuttons
        # Only include super-user visible events if current user has these rights.
        # It's cosmetic - the check for super-user rights should be performed
        # in event handling code as well!
        allowed = []
        for key in event_list.keys():
            if not event_list[key]['superuser'] or super:
                allowed.append((key, event_list[key]['desc']))

        for evname, evdescr in allowed:
            tr = html.TR()
            table.append(tr)
            for notiftype, notifdescr in types:
                checked = evname in getattr(self.request.user,
                                            '%s_subscribed_events' % notiftype)
                tr.append(html.TD().append(html.INPUT(
                        type='checkbox',
                        checked=checked,
                        name='subscribe:%s:%s' % (notiftype, evname))))
            tr.append(html.TD().append(html.Raw(self.request.getText(evdescr))))

        return table

    def create_form(self):
        """ Create the complete HTML form code. """
        _ = self._
        self._form = self.make_form(
            _('Select the events you want to be notified about.'))

        self._form.append(html.INPUT(type="hidden", name="action", value="userprefs"))
        self._form.append(html.INPUT(type="hidden", name="handler", value="prefs"))

        ticket = wikiutil.createTicket(self.request)
        self._form.append(html.INPUT(type="hidden", name="ticket", value="%s" % ticket))

        if (not (self.cfg.mail_enabled and self.request.user.email)
            and not (self.cfg.jabber_enabled and self.request.user.jid)):
            self.make_row('', [html.Text(
                _("Before you can be notified, you need to provide a way"
                  " to contact you in the general preferences."))])
            self.make_row('', [
                html.INPUT(type="submit", name="cancel", value=_("Cancel"))])
            return unicode(self._form)

        self.make_row(_('Subscribed events'), [self._event_select()])

        # Get list of subscribe pages, DO NOT sort! it should
        # stay in the order the user entered it in his input
        # box.
        notifylist = self.request.user.getSubscriptionList()

        self.make_row(
            html.Raw(_('Subscribed wiki pages<<BR>>(one regex per line)', wiki=True)),
            [html.TEXTAREA(name="subscribed_pages", rows="6", cols="50").append(
                '\n'.join(notifylist)), ],
            valign="top"
        )

        # Add buttons
        self.make_row('', [
            html.INPUT(type="submit", name="save", value=_("Save")),
            ' ',
            html.INPUT(type="submit", name="cancel", value=_("Cancel"))])

        return unicode(self._form)

    def allowed(self):
        return UserPrefBase.allowed(self) and (
            self.cfg.mail_enabled or self.cfg.jabber_enabled)
