# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - create account action

    @copyright: 2007 MoinMoin:JohannesBerg
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import user, wikiutil, util
from MoinMoin.Page import Page
from MoinMoin.widget import html
import MoinMoin.events as events
from MoinMoin.userprefs.prefs import Settings


_debug = False

def _create_user(request):
    _ = request.getText
    form = request.form

    if request.request_method != 'POST':
        return _("Use UserPreferences to change your settings or create an account.")
    # Create user profile
    theuser = user.User(request, auth_method="new-user")

    # Require non-empty name
    try:
        theuser.name = form['name'][0]
    except KeyError:
        return _("Empty user name. Please enter a user name.")

    # Don't allow creating users with invalid names
    if not user.isValidName(request, theuser.name):
        return _("""Invalid user name {{{'%s'}}}.
Name may contain any Unicode alpha numeric character, with optional one
space between words. Group page name is not allowed.""") % wikiutil.escape(theuser.name)

    # Name required to be unique. Check if name belong to another user.
    if user.getUserId(request, theuser.name):
        return _("This user name already belongs to somebody else.")

    # try to get the password and pw repeat
    password = form.get('password', [''])[0]
    password2 = form.get('password2', [''])[0]

    # Check if password is given and matches with password repeat
    if password != password2:
        return _("Passwords don't match!")
    if not password:
        return _("Please specify a password!")

    # Encode password
    if password and not password.startswith('{SHA}'):
        try:
            theuser.enc_password = user.encodePassword(password)
        except UnicodeError, err:
            # Should never happen
            return "Can't encode password: %s" % str(err)

    # try to get the email, for new users it is required
    email = wikiutil.clean_input(form.get('email', [''])[0])
    theuser.email = email.strip()
    if not theuser.email:
        return _("Please provide your email address. If you lose your"
                 " login information, you can get it by email.")

    # Email should be unique - see also MoinMoin/script/accounts/moin_usercheck.py
    if theuser.email and request.cfg.user_email_unique:
        users = user.getUserList(request)
        for uid in users:
            if uid == theuser.id:
                continue
            thisuser = user.User(request, uid)
            if thisuser.email == theuser.email and not thisuser.disabled:
                return _("This email already belongs to somebody else.")

    # save data
    theuser.save()

    user_created = events.UserCreatedEvent(request, theuser)
    events.send_event(user_created)

    if form.has_key('create_and_mail'):
        theuser.mailAccountData()

    result = _("User account created! You can use this account to login now...")
    if _debug:
        result = result + util.dumpFormData(form)
    return result


def execute(pagename, request):
    pagename = pagename
    page = Page(request, pagename)
    _ = request.getText
    form = request.form

    submitted = form.has_key('create_only') or form.has_key('create_and_mail')

    if submitted: # user pressed create button
        error = _create_user(request)
        return page.send_page(msg=error)
    else: # show create form
        request.emit_http_headers()
        request.theme.send_title(_("Create Account"), pagename=pagename)

        request.write(request.formatter.startContent("content"))

        # THIS IS A BIG HACK. IT NEEDS TO BE CLEANED UP
        request.write(Settings(request).create_form(create_only=True))

        request.write(request.formatter.endContent())

        request.theme.send_footer(pagename)
        request.theme.send_closing_html()
