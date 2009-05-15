# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Preferences Form

    @copyright: 2001-2004 Juergen Hermann <jh@web.de>,
                2003-2007 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import time
from MoinMoin import user, util, wikiutil, events
from MoinMoin.theme import load_theme_fallback
from MoinMoin.widget import html
from MoinMoin.userprefs import UserPrefBase


#################################################################
# This is still a mess.
#
# The plan for refactoring would be:
# split the plugin into multiple preferences pages:
#    - account details (name, email, timezone, ...)
#    - wiki settings (editor, fancy diffs, theme, ...)
#    - quick links (or leave in wiki settings?)
####


class Settings(UserPrefBase):
    def __init__(self, request):
        """ Initialize user settings form. """
        UserPrefBase.__init__(self, request)
        self.request = request
        self._ = request.getText
        self.cfg = request.cfg
        _ = self._
        self.title = _("Preferences")
        self.name = 'prefs'

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

    def _save_user_prefs(self):
        _ = self._
        form = self.request.form
        request = self.request

        if request.method != 'POST':
            return

        if not 'name' in request.user.auth_attribs:
            # Require non-empty name
            new_name = form.get('name', request.user.name)

            # Don't allow changing the name to an invalid one
            if not user.isValidName(request, new_name):
                return 'error', _("""Invalid user name {{{'%s'}}}.
Name may contain any Unicode alpha numeric character, with optional one
space between words. Group page name is not allowed.""", wiki=True) % wikiutil.escape(new_name)

            # Is this an existing user trying to change information or a new user?
            # Name required to be unique. Check if name belong to another user.
            existing_id = user.getUserId(request, new_name)
            if existing_id is not None and existing_id != request.user.id:
                return 'error', _("This user name already belongs to somebody else.")

            if not new_name:
                return 'error', _("Empty user name. Please enter a user name.")

            # done sanity checking the name, set it
            request.user.name = new_name


        if not 'email' in request.user.auth_attribs:
            # try to get the email
            new_email = wikiutil.clean_input(form.get('email', request.user.email))
            new_email = new_email.strip()

            # Require email
            if not new_email and 'email' not in request.cfg.user_form_remove:
                return 'error', _("Please provide your email address. If you lose your"
                                  " login information, you can get it by email.")

            # Email should be unique - see also MoinMoin/script/accounts/moin_usercheck.py
            if new_email and request.cfg.user_email_unique:
                other = user.get_by_email_address(request, new_email)
                if other is not None and other.id != request.user.id:
                    return 'error', _("This email already belongs to somebody else.")

            # done checking the email, set it
            request.user.email = new_email


        if not 'jid' in request.user.auth_attribs:
            # try to get the jid
            new_jid = wikiutil.clean_input(form.get('jid', '')).strip()

            jid_changed = request.user.jid != new_jid
            previous_jid = request.user.jid

            if new_jid and request.cfg.user_jid_unique:
                other = user.get_by_jabber_id(request, new_jid)
                if other is not None and other.id != request.user.id:
                    return 'error', _("This jabber id already belongs to somebody else.")

            if jid_changed:
                set_event = events.JabberIDSetEvent(request, new_jid)
                unset_event = events.JabberIDUnsetEvent(request, previous_jid)
                events.send_event(unset_event)
                events.send_event(set_event)

            # done checking the JID, set it
            request.user.jid = new_jid


        if not 'aliasname' in request.user.auth_attribs:
            # aliasname
            request.user.aliasname = wikiutil.clean_input(form.get('aliasname', ''))

        # editor size
        request.user.edit_rows = util.web.getIntegerInput(request, 'edit_rows',
                                                          request.user.edit_rows, 10, 60)

        # try to get the editor
        request.user.editor_default = form.get('editor_default', self.cfg.editor_default)
        request.user.editor_ui = form.get('editor_ui', self.cfg.editor_ui)

        # time zone
        request.user.tz_offset = util.web.getIntegerInput(request, 'tz_offset',
                                                          request.user.tz_offset, -84600, 84600)

        # datetime format
        try:
            dt_d_combined = Settings._date_formats.get(form['datetime_fmt'], '')
            request.user.datetime_fmt, request.user.date_fmt = dt_d_combined.split(' & ')
        except (KeyError, ValueError):
            request.user.datetime_fmt = '' # default
            request.user.date_fmt = '' # default

        # try to get the (optional) theme
        theme_name = form.get('theme_name', self.cfg.theme_default)
        if theme_name != request.user.theme_name:
            # if the theme has changed, load the new theme
            # so the user has a direct feedback
            # WARNING: this should be refactored (i.e. theme load
            # after userform handling), cause currently the
            # already loaded theme is just replaced (works cause
            # nothing has been emitted yet)
            request.user.theme_name = theme_name
            if load_theme_fallback(request, theme_name) > 0:
                theme_name = wikiutil.escape(theme_name)
                return 'error', _("The theme '%(theme_name)s' could not be loaded!") % locals()

        # try to get the (optional) preferred language
        request.user.language = form.get('language', '')
        if request.user.language == u'': # For language-statistics
            from MoinMoin import i18n
            request.user.real_language = i18n.get_browser_language(request)
        else:
            request.user.real_language = ''

        # I want to handle all inputs from user_form_fields, but
        # don't want to handle the cases that have already been coded
        # above.
        # This is a horribly fragile kludge that's begging to break.
        # Something that might work better would be to define a
        # handler for each form field, instead of stuffing them all in
        # one long and inextensible method.  That would allow for
        # plugins to provide methods to validate their fields as well.
        already_handled = ['name', 'email',
                           'aliasname', 'edit_rows', 'editor_default',
                           'editor_ui', 'tz_offset', 'datetime_fmt',
                           'theme_name', 'language', 'real_language', 'jid']
        for field in self.cfg.user_form_fields:
            key = field[0]
            if ((key in self.cfg.user_form_disable)
                or (key in already_handled)):
                continue
            default = self.cfg.user_form_defaults[key]
            value = form.get(key, default)
            setattr(request.user, key, value)

        # checkbox options
        for key, label in self.cfg.user_checkbox_fields:
            if key not in self.cfg.user_checkbox_disable and key not in self.cfg.user_checkbox_remove:
                value = form.get(key, "0")
                try:
                    value = int(value)
                except ValueError:
                    pass
                else:
                    setattr(request.user, key, value)

        # quicklinks for navibar
        request.user.quicklinks = self._decode_pagelist('quicklinks')

        # save data
        request.user.save()
        if request.user.disabled:
            # set valid to false so the current request won't
            # show the user as logged-in any more
            request.user.valid = False

        result = _("User preferences saved!")
        return result


    def handle_form(self):
        _ = self._
        form = self.request.form

        if 'cancel' in form:
            return

        if 'save' in form: # Save user profile
            return self._save_user_prefs()

    # form generation part

    _date_formats = { # datetime_fmt & date_fmt
        'iso': '%Y-%m-%d %H:%M:%S & %Y-%m-%d',
        'us': '%m/%d/%Y %I:%M:%S %p & %m/%d/%Y',
        'euro': '%d.%m.%Y %H:%M:%S & %d.%m.%Y',
        'rfc': '%a %b %d %H:%M:%S %Y & %a %b %d %Y',
    }

    def _tz_select(self, enabled=True):
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

        return util.web.makeSelection('tz_offset', options, str(tz), 1, False, enabled)


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


    def _lang_select(self, enabled=True):
        """ Create language selection. """
        from MoinMoin import i18n
        _ = self._
        cur_lang = self.request.user.valid and self.request.user.language or ''
        langs = i18n.wikiLanguages().items()
        langs.sort(lambda x, y: cmp(x[1]['x-language'], y[1]['x-language']))
        options = [('', _('<Browser setting>'))]
        for lang in langs:
            name = lang[1]['x-language']
            options.append((lang[0], name))

        return util.web.makeSelection('language', options, cur_lang, 1, False, enabled)

    def _theme_select(self):
        """ Create theme selection. """
        cur_theme = self.request.user.valid and self.request.user.theme_name or self.cfg.theme_default
        options = [("<default>", "<%s>" % self._("Default"))]
        for theme in wikiutil.getPlugins('theme', self.request.cfg):
            options.append((theme, theme))

        return util.web.makeSelection('theme_name', options, cur_theme)

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


    def create_form(self):
        """ Create the complete HTML form code. """
        _ = self._
        request = self.request
        self._form = self.make_form()

        if request.user.valid:
            buttons = [('save', _('Save')), ('cancel', _('Cancel')), ]
            uf_remove = self.cfg.user_form_remove
            uf_disable = self.cfg.user_form_disable
            for attr in request.user.auth_attribs:
                uf_disable.append(attr)
            for key, label, type, length, textafter in self.cfg.user_form_fields:
                default = self.cfg.user_form_defaults[key]
                if not key in uf_remove:
                    if key in uf_disable:
                        self.make_row(_(label),
                                  [html.INPUT(type=type, size=length, name=key, disabled="disabled",
                                   value=getattr(request.user, key)), ' ', _(textafter), ])
                    else:
                        self.make_row(_(label),
                                  [html.INPUT(type=type, size=length, name=key, value=getattr(request.user, key)), ' ', _(textafter), ])

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
            checkbox_fields.sort(lambda a, b: cmp(a[1](_), b[1](_)))
            for key, label in checkbox_fields:
                if not key in self.cfg.user_checkbox_remove:
                    bool_options.extend([
                        html.INPUT(type="checkbox", name=key, value="1",
                            checked=getattr(request.user, key, 0),
                            disabled=key in self.cfg.user_checkbox_disable and True or None),
                        ' ', label(_), html.BR(),
                    ])
            self.make_row(_('General options'), bool_options, valign="top")

            self.make_row(_('Quick links'), [
                html.TEXTAREA(name="quicklinks", rows="6", cols="50")
                    .append('\n'.join(request.user.getQuickLinks())),
            ], valign="top")

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
