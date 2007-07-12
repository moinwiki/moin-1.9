# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - UserPreferences Form and User Browser

    @copyright: 2001-2004 Juergen Hermann <jh@web.de>,
                2003-2007 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import time
from MoinMoin import user, util, wikiutil, events
from MoinMoin.widget import html
from MoinMoin.userprefs import UserPrefBase


#################################################################
# This is a mess.
#
# The plan for refactoring would be:
# split the plugin into multiple preferences pages:
#    - account details (name, email, timezone, ...)
#    - change password
#    - wiki settings (editor, fancy diffs, theme, ...)
#    - notification settings (trivial, subscribed pages, ...)
#    - quick links (or leave in wiki settings?)
####


_debug = 0

class Settings(UserPrefBase):
    def __init__(self, request):
        """ Initialize user settings form. """
        UserPrefBase.__init__(self, request)
        self.request = request
        self._ = request.getText
        self.cfg = request.cfg
        self.title = self._("Preferences")

    def _decode_pagelist(self, key):
        """ Decode list of pages from form input

        Each line is a page name, empty lines ignored.

        @param key: the form key to get
        @rtype: list of unicode strings
        @return: list of normalized names
        """
        text = self.request.form.get(key, [''])[0]
        text = text.replace('\r', '')
        items = []
        for item in text.split('\n'):
            item = item.strip()
            if not item:
                continue
            items.append(item)
        return items

    def _save_user_prefs(self):
        _ = self._
        form = self.request.form

        if self.request.request_method != 'POST':
            return _("Use UserPreferences to change your settings or create an account.")
        theuser = self.request.user
        if not theuser:
            return

        if not 'name' in theuser.auth_attribs:
            # Require non-empty name
            theuser.name = form.get('name', [theuser.name])[0]

            # Don't allow changing the name to an invalid one
            if not user.isValidName(self.request, theuser.name):
                return _("""Invalid user name {{{'%s'}}}.
Name may contain any Unicode alpha numeric character, with optional one
space between words. Group page name is not allowed.""") % wikiutil.escape(theuser.name)

            # Is this an existing user trying to change information or a new user?
            # Name required to be unique. Check if name belong to another user.
            if user.getUserId(self.request, theuser.name):
                if theuser.name != self.request.user.name:
                    return _("This user name already belongs to somebody else.")

            if not theuser.name:
                return _("Empty user name. Please enter a user name.")

        if not 'password' in theuser.auth_attribs:
            # try to get the password and pw repeat
            password = form.get('password', [''])[0]
            password2 = form.get('password2', [''])[0]

            # Check if password is given and matches with password repeat
            if password != password2:
                return _("Passwords don't match!")

            # Encode password
            if password and not password.startswith('{SHA}'):
                try:
                    theuser.enc_password = user.encodePassword(password)
                except UnicodeError, err:
                    # Should never happen
                    return "Can't encode password: %s" % str(err)

        if not 'email' in theuser.auth_attribs:
            # try to get the email
            email = wikiutil.clean_input(form.get('email', [theuser.email])[0])
            theuser.email = email.strip()

            # Require email
            if not theuser.email:
                return _("Please provide your email address. If you lose your"
                         " login information, you can get it by email.")

            # Email should be unique - see also MoinMoin/script/accounts/moin_usercheck.py
            if theuser.email and self.request.cfg.user_email_unique:
                other = user.get_by_email_address(self.request, theuser.email)
                if other is not None and other.id != theuser.id:
                    return _("This email already belongs to somebody else.")

        if not 'jid' in theuser.auth_attribs:
            # try to get the jid
            jid = wikiutil.clean_input(form.get('jid', "")).strip()

            jid_changed = theuser.jid != jid
            previous_jid = theuser.jid
            theuser.jid = jid

            if theuser.jid and self.request.cfg.user_jid_unique:
                other = user.get_by_jabber_id(self.request, theuser.jid)
                if other is not None and other.id != theuser.id:
                    return _("This jabber id already belongs to somebody else.")

            if jid_changed:
                set_event = events.JabberIDSetEvent(self.request, theuser.jid)
                unset_event = events.JabberIDUnsetEvent(self.request, previous_jid)
                events.send_event(unset_event)
                events.send_event(set_event)

        if not 'aliasname' in theuser.auth_attribs:
            # aliasname
            theuser.aliasname = wikiutil.clean_input(form.get('aliasname', [''])[0])

        # editor size
        theuser.edit_rows = util.web.getIntegerInput(self.request, 'edit_rows', theuser.edit_rows, 10, 60)

        # try to get the editor
        theuser.editor_default = form.get('editor_default', [self.cfg.editor_default])[0]
        theuser.editor_ui = form.get('editor_ui', [self.cfg.editor_ui])[0]

        # time zone
        theuser.tz_offset = util.web.getIntegerInput(self.request, 'tz_offset', theuser.tz_offset, -84600, 84600)

        # datetime format
        try:
            dt_d_combined = Settings._date_formats.get(form['datetime_fmt'][0], '')
            theuser.datetime_fmt, theuser.date_fmt = dt_d_combined.split(' & ')
        except (KeyError, ValueError):
            theuser.datetime_fmt = '' # default
            theuser.date_fmt = '' # default

        # try to get the (optional) theme
        theme_name = form.get('theme_name', [self.cfg.theme_default])[0]
        if theme_name != theuser.theme_name:
            # if the theme has changed, load the new theme
            # so the user has a direct feedback
            # WARNING: this should be refactored (i.e. theme load
            # after userform handling), cause currently the
            # already loaded theme is just replaced (works cause
            # nothing has been emitted yet)
            theuser.theme_name = theme_name
            if self.request.loadTheme(theuser.theme_name) > 0:
                theme_name = wikiutil.escape(theme_name)
                return _("The theme '%(theme_name)s' could not be loaded!") % locals()

        # try to get the (optional) preferred language
        theuser.language = form.get('language', [''])[0]

        # I want to handle all inputs from user_form_fields, but
        # don't want to handle the cases that have already been coded
        # above.
        # This is a horribly fragile kludge that's begging to break.
        # Something that might work better would be to define a
        # handler for each form field, instead of stuffing them all in
        # one long and inextensible method.  That would allow for
        # plugins to provide methods to validate their fields as well.
        already_handled = ['name', 'password', 'password2', 'email',
                           'aliasname', 'edit_rows', 'editor_default',
                           'editor_ui', 'tz_offset', 'datetime_fmt',
                           'theme_name', 'language', 'jid']
        for field in self.cfg.user_form_fields:
            key = field[0]
            if ((key in self.cfg.user_form_disable)
                or (key in already_handled)):
                continue
            default = self.cfg.user_form_defaults[key]
            value = form.get(key, [default])[0]
            setattr(theuser, key, value)

        # checkbox options
        for key, label in self.cfg.user_checkbox_fields:
            if key not in self.cfg.user_checkbox_disable and key not in self.cfg.user_checkbox_remove:
                value = form.get(key, ["0"])[0]
                try:
                    value = int(value)
                except ValueError:
                    pass
                else:
                    setattr(theuser, key, value)

        # quicklinks for navibar
        theuser.quicklinks = self._decode_pagelist('quicklinks')

        # subscription for page change notification
        theuser.subscribed_pages = self._decode_pagelist('subscribed_pages')

        # subscription to various events
        available = events.get_subscribable_events()
        theuser.subscribed_events = [ev for ev in form.get('events', [])]

        # save data
        theuser.save()
        self.request.user = theuser

        result = _("User preferences saved!")
        if _debug:
            result = result + util.dumpFormData(form)
        return result


    def handle_form(self):
        _ = self._
        form = self.request.form

        if form.has_key('cancel'):
            return

        if form.has_key('save'): # Save user profile
            return self._save_user_prefs()

    # form generation part

    _date_formats = { # datetime_fmt & date_fmt
        'iso': '%Y-%m-%d %H:%M:%S & %Y-%m-%d',
        'us': '%m/%d/%Y %I:%M:%S %p & %m/%d/%Y',
        'euro': '%d.%m.%Y %H:%M:%S & %d.%m.%Y',
        'rfc': '%a %b %d %H:%M:%S %Y & %a %b %d %Y',
    }

    def _tz_select(self):
        """ Create time zone selection. """
        tz = 0
        if self.request.user.valid:
            tz = int(self.request.user.tz_offset)

        options = []
        now = time.time()
        for halfhour in range(-47, 48):
            offset = halfhour * 1800
            t = now + offset

            options.append((
                str(offset),
                '%s [%s%s:%s]' % (
                    time.strftime(self.cfg.datetime_fmt, util.timefuncs.tmtuple(t)),
                    "+-"[offset < 0],
                    "%02d" % (abs(offset) / 3600),
                    "%02d" % (abs(offset) % 3600 / 60),
                ),
            ))

        return util.web.makeSelection('tz_offset', options, str(tz))


    def _dtfmt_select(self):
        """ Create date format selection. """
        _ = self._
        try:
            dt_d_combined = '%s & %s' % (self.request.user.datetime_fmt, self.request.user.date_fmt)
            selected = [
                k for k, v in self._date_formats.items()
                    if v == dt_d_combined][0]
        except IndexError:
            selected = ''
        options = [('', _('Default'))] + self._date_formats.items()

        return util.web.makeSelection('datetime_fmt', options, selected)


    def _lang_select(self):
        """ Create language selection. """
        from MoinMoin import i18n
        _ = self._
        cur_lang = self.request.user.valid and self.request.user.language or ''
        langs = i18n.wikiLanguages().items()
        langs.sort(lambda x, y: cmp(x[1]['x-language'], y[1]['x-language']))
        options = [('', _('<Browser setting>', formatted=False))]
        for lang in langs:
            name = lang[1]['x-language']
            options.append((lang[0], name))

        return util.web.makeSelection('language', options, cur_lang)

    def _theme_select(self):
        """ Create theme selection. """
        cur_theme = self.request.user.valid and self.request.user.theme_name or self.cfg.theme_default
        options = [("<default>", "<%s>" % self._("Default"))]
        for theme in wikiutil.getPlugins('theme', self.request.cfg):
            options.append((theme, theme))

        return util.web.makeSelection('theme_name', options, cur_theme)

    def _event_select(self):
        """ Create event subscription list. """

        event_list = events.get_subscribable_events()
        selected = self.request.user.subscribed_events
        super = self.request.user.isSuperUser()

        # Create a list of (value, name) tuples for display in <select>
        # Only include super-user visible events if current user has these rights.
        # It's cosmetic - the check for super-user rights should be performed
        # in event handling code as well!
        allowed = []
        for key in event_list.keys():
            if not event_list[key]['superuser'] or super:
                allowed.append((key, event_list[key]['desc']))

        return util.web.makeMultiSelection('events', allowed, selectedvals=selected)

    def _editor_default_select(self):
        """ Create editor selection. """
        editor_default = self.request.user.valid and self.request.user.editor_default or self.cfg.editor_default
        options = [("<default>", "<%s>" % self._("Default"))]
        for editor in ['text', 'gui', ]:
            options.append((editor, editor))
        return util.web.makeSelection('editor_default', options, editor_default)

    def _editor_ui_select(self):
        """ Create editor selection. """
        editor_ui = self.request.user.valid and self.request.user.editor_ui or self.cfg.editor_ui
        options = [("<default>", "<%s>" % self._("Default")),
                   ("theonepreferred", self._("the one preferred")),
                   ("freechoice", self._("free choice")),
                  ]
        return util.web.makeSelection('editor_ui', options, editor_ui)

    def _make_form(self):
        """ Create the FORM, and the TABLE with the input fields
        """
        sn = self.request.getScriptname()
        pi = self.request.getPathinfo()
        action = u"%s%s" % (sn, pi)
        self._form = html.FORM(action=action)
        self._table = html.TABLE(border="0")

        # Use the user interface language and direction
        lang_attr = self.request.theme.ui_lang_attr()
        self._form.append(html.Raw('<div class="userpref"%s>' % lang_attr))

        self._form.append(self._table)
        self._form.append(html.Raw("</div>"))


    def make_row(self, label, cell, **kw):
        """ Create a row in the form table.
        """
        self._table.append(html.TR().extend([
            html.TD(**kw).extend([html.B().append(label), '   ']),
            html.TD().extend(cell),
        ]))


    def create_form(self):
        """ Create the complete HTML form code. """
        _ = self._
        self._make_form()

        if self.request.user.valid:
            buttons = [('save', _('Save')), ('cancel', _('Cancel')), ]
            uf_remove = self.cfg.user_form_remove
            uf_disable = self.cfg.user_form_disable
            for attr in self.request.user.auth_attribs:
                if attr == 'password':
                    uf_remove.append(attr)
                    uf_remove.append('password2')
                else:
                    uf_disable.append(attr)
            for key, label, type, length, textafter in self.cfg.user_form_fields:
                default = self.cfg.user_form_defaults[key]
                if not key in uf_remove:
                    if key in uf_disable:
                        self.make_row(_(label),
                                  [html.INPUT(type=type, size=length, name=key, disabled="disabled",
                                   value=getattr(self.request.user, key)), ' ', _(textafter), ])
                    else:
                        self.make_row(_(label),
                                  [html.INPUT(type=type, size=length, name=key, value=getattr(self.request.user, key)), ' ', _(textafter), ])

            if not self.cfg.theme_force and not "theme_name" in self.cfg.user_form_remove:
                self.make_row(_('Preferred theme'), [self._theme_select()])

            if not self.cfg.editor_force:
                if not "editor_default" in self.cfg.user_form_remove:
                    self.make_row(_('Editor Preference'), [self._editor_default_select()])
                if not "editor_ui" in self.cfg.user_form_remove:
                    self.make_row(_('Editor shown on UI'), [self._editor_ui_select()])

            if not "tz_offset" in self.cfg.user_form_remove:
                self.make_row(_('Time zone'), [
                    _('Your time is'), ' ',
                    self._tz_select(),
                    html.BR(),
                    _('Server time is'), ' ',
                    time.strftime(self.cfg.datetime_fmt, util.timefuncs.tmtuple()),
                    ' (UTC)',
                ])

            if not "datetime_fmt" in self.cfg.user_form_remove:
                self.make_row(_('Date format'), [self._dtfmt_select()])

            if not "language" in self.cfg.user_form_remove:
                self.make_row(_('Preferred language'), [self._lang_select()])

            # boolean user options
            bool_options = []
            checkbox_fields = self.cfg.user_checkbox_fields
            _ = self.request.getText
            checkbox_fields.sort(lambda a, b: cmp(a[1](_), b[1](_)))
            for key, label in checkbox_fields:
                if not key in self.cfg.user_checkbox_remove:
                    bool_options.extend([
                        html.INPUT(type="checkbox", name=key, value="1",
                            checked=getattr(self.request.user, key, 0),
                            disabled=key in self.cfg.user_checkbox_disable and True or None),
                        ' ', label(_), html.BR(),
                    ])
            self.make_row(_('General options'), bool_options, valign="top")

            self.make_row(_('Quick links'), [
                html.TEXTAREA(name="quicklinks", rows="6", cols="50")
                    .append('\n'.join(self.request.user.getQuickLinks())),
            ], valign="top")

            # FIXME: this depends on Jabber ATM, but may not do so in the future
            if self.cfg.jabber_enabled:
                self.make_row(_('Subscribed events'), [self._event_select()])

            # subscribed pages
            if self.cfg.mail_enabled:
                # Get list of subscribe pages, DO NOT sort! it should
                # stay in the order the user entered it in his input
                # box.
                notifylist = self.request.user.getSubscriptionList()

                warning = []
                if not self.request.user.email:
                    warning = [
                        html.BR(),
                        html.SMALL(Class="warning").append(
                            _("This list does not work, unless you have"
                              " entered a valid email address!")
                        )]

                self.make_row(
                    html.Raw(_('Subscribed wiki pages (one regex per line)')),
                    [html.TEXTAREA(name="subscribed_pages", rows="6", cols="50").append(
                        '\n'.join(notifylist)),
                    ] + warning,
                    valign="top"
                )
            self._form.append(html.INPUT(type="hidden", name="action", value="userprefs"))
            self._form.append(html.INPUT(type="hidden", name="handler", value="prefs"))

        # Add buttons
        button_cell = []
        for name, label in buttons:
            if not name in self.cfg.user_form_remove:
                button_cell.extend([
                    html.INPUT(type="submit", name=name, value=label),
                    ' ',
                ])
        self.make_row('', button_cell)

        return unicode(self._form)
