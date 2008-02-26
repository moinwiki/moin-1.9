# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - create account action

    @copyright: 2007 MoinMoin:JohannesBerg
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import user, wikiutil
from MoinMoin.Page import Page
from MoinMoin.widget import html

def _do_recover(request):
    _ = request.getText
    form = request.form
    if not request.cfg.mail_enabled:
        return _("""This wiki is not enabled for mail processing.
Contact the owner of the wiki, who can enable email.""")
    try:
        email = wikiutil.clean_input(form['email'][0].lower())
        if not email:
            raise KeyError # we raise KeyError if the string is empty
    except KeyError:
        try:
            username = wikiutil.clean_input(form['name'][0])
            if not username:
                raise KeyError
        except KeyError:
            return _("Please provide a valid email address!")

        u = user.User(self.request, user.getUserId(self.request, username))
        if u.valid:
            is_ok, msg = u.mailAccountData()
            if not is_ok:
                return wikiutil.escape(msg)
        return _("If an account with this username exists, an email was sent.")

    u = user.get_by_email_address(request, email)
    if u:
        is_ok, msg = u.mailAccountData()
        return wikiutil.escape(msg)

    return _("Found no account matching the given email address '%(email)s'!") % {'email': email}

def _create_form(request):
    _ = request.getText
    url = request.page.url(request)
    ret = html.FORM(action=url)
    ret.append(html.INPUT(type='hidden', name='action', value='recoverpass'))
    lang_attr = request.theme.ui_lang_attr()
    ret.append(html.Raw('<div class="userpref"%s>' % lang_attr))
    tbl = html.TABLE(border="0")
    ret.append(tbl)
    ret.append(html.Raw('</div>'))

    row = html.TR()
    tbl.append(row)
    row.append(html.TD().append(html.STRONG().append(html.Text(_("Email")))))
    row.append(html.TD().append(html.INPUT(type="text", size="36",
                                           name="email")))

    row = html.TR()
    tbl.append(row)
    row.append(html.TD())
    td = html.TD()
    row.append(td)
    td.append(html.INPUT(type="submit", name="account_sendmail",
                         value=_('Mail me my account data')))

    return unicode(ret)


def execute(pagename, request):
    pagename = pagename
    page = Page(request, pagename)
    _ = request.getText
    form = request.form

    submitted = form.get('account_sendmail', [''])[0]

    if submitted: # user pressed create button
        msg = _do_recover(request)
        request.theme.add_msg(msg, "dialog")
        page.send_page()
    else: # show create form
        request.emit_http_headers()
        request.theme.send_title(_("Lost password"), pagename=pagename)

        request.write(request.formatter.startContent("content"))

        if not request.cfg.mail_enabled:
            request.write(_("""This wiki is not enabled for mail processing.
Contact the owner of the wiki, who can enable email."""))
        else:
            request.write(_create_form(request))

            request.write(_("""
== Recovering a lost password ==
<<BR>>
If you have forgotten your password, provide your email address and click on '''Mail me my account data'''.
<<BR>>
The email you get contains the encrypted password (so even if someone intercepts the mail, he won't know your REAL password). Just copy and paste it into the login mask into the password field and log in.
After logging in you should change your password.""", wiki=True))

        request.write(request.formatter.endContent())

        request.theme.send_footer(pagename)
        request.theme.send_closing_html()
