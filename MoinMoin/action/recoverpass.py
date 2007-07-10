# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - create account action

    @copyright: 2007 MoinMoin:JohannesBerg
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import user, wikiutil
from MoinMoin.Page import Page
from MoinMoin.widget import html
from MoinMoin.userprefs.prefs import Settings

def _do_recover(request):
    _ = request.getText
    form = request.form
    if not request.cfg.mail_enabled:
        return _("""This wiki is not enabled for mail processing.
Contact the owner of the wiki, who can enable email.""")
    try:
        email = wikiutil.clean_input(form['email'][0].lower())
    except KeyError:
        return _("Please provide a valid email address!")

    u = user.get_by_email_address(request, email)
    if u:
        msg = u.mailAccountData()
        return wikiutil.escape(msg)

    return _("Found no account matching the given email address '%(email)s'!") % {'email': email}


def execute(pagename, request):
    pagename = pagename
    page = Page(request, pagename)
    _ = request.getText
    form = request.form

    submitted = form.get('account_sendmail', [''])[0]

    if submitted: # user pressed create button
        msg = _do_recover(request)
        page.send_page(msg=msg)
    else: # show create form
        request.emit_http_headers()
        request.theme.send_title(_("Lost password"), pagename=pagename)

        request.write(request.formatter.startContent("content"))

        # THIS IS A BIG HACK. IT NEEDS TO BE CLEANED UP
        request.write(Settings(request).create_form(recover_only=True))

        request.write(_("""
== Recovering a lost password ==
[[BR]]
If you have forgotten your password, provide your email address and click on '''Mail me my account data'''.
[[BR]]
The email you get contains the encrypted password (so even if someone intercepts the mail, he won't know your REAL password). Just copy and paste it into the login mask into the password field and log in.
After logging in you should change your password."""))
        request.write(request.formatter.endContent())

        request.theme.send_footer(pagename)
        request.theme.send_closing_html()
