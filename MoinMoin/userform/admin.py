# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - User account administration

    @copyright: 2001-2004 Juergen Hermann <jh@web.de>,
                2003-2007 MoinMoin:ThomasWaldmann
                2007-2008 MoinMoin:ReimarBauer
    @license: GNU GPL, see COPYING for details.
"""
from MoinMoin import user, wikiutil
from MoinMoin.util.dataset import TupleDataset, Column
from MoinMoin.Page import Page
from MoinMoin.widget import html

def do_user_browser(request):
    """ Browser for SystemAdmin macro. """
    _ = request.getText

    data = TupleDataset()
    data.columns = [
        Column('name', label=_('Username')),
        Column('groups', label=_('Member of Groups')),
        Column('email', label=_('Email')),
        Column('jabber', label=_('Jabber')),
        Column('action', label=_('Action')),
    ]

    isgroup = request.cfg.cache.page_group_regexact.search
    groupnames = request.rootpage.getPageList(user='', filter=isgroup)

    # Iterate over users
    for uid in user.getUserList(request):
        account = user.User(request, uid)

        grouppage_links = ', '.join([Page(request, groupname).link_to(request)
                                     for groupname in groupnames
                                     if request.dicts.has_member(groupname, account.name)])

        userhomepage = Page(request, account.name)
        if userhomepage.exists():
            namelink = userhomepage.link_to(request)
        else:
            namelink = wikiutil.escape(account.name)

        # creates the POST data for account disable/enable
        val = "1"
        text=_('Disable user')
        if account.disabled:
            text=_('Enable user')
            val = "0"
            namelink += " (%s)" % _("disabled")

        url = request.page.url(request)
        ret = html.FORM(action=url)
        ret.append(html.INPUT(type='hidden', name='action', value='userprofile'))
        ret.append(html.INPUT(type='hidden', name='name', value=account.name))
        ret.append(html.INPUT(type='hidden', name='key', value="disabled"))
        ret.append(html.INPUT(type='hidden', name='val', value=val))
        ret.append(html.INPUT(type='submit', name='userprofile', value=text))
        enable_disable_link = unicode(unicode(ret))

        # creates the POST data for recoverpass
        url = request.page.url(request)
        ret = html.FORM(action=url)
        ret.append(html.INPUT(type='hidden', name='action', value='recoverpass'))
        ret.append(html.INPUT(type='hidden', name='email', value=account.email))
        ret.append(html.INPUT(type='hidden', name='account_sendmail', value="1"))
        ret.append(html.INPUT(type='hidden', name='sysadm', value="users"))
        ret.append(html.INPUT(type='submit', name='recoverpass', value=_('Mail account data')))
        recoverpass_link =  unicode(unicode(ret))

        if account.email:
            email_link = (request.formatter.url(1, 'mailto:' + account.email, css='mailto') +
                          request.formatter.text(account.email) +
                          request.formatter.url(0))
        else:
            email_link = ''

        if account.jid:
            jabber_link = (request.formatter.url(1, 'xmpp:' + account.jid, css='mailto') +
                           request.formatter.text(account.jid) +
                           request.formatter.url(0))
        else:
            jabber_link = ''

        data.addRow((
            request.formatter.rawHTML(namelink),
            request.formatter.rawHTML(grouppage_links),
            email_link,
            jabber_link,
            recoverpass_link + enable_disable_link
        ))

    if data:
        from MoinMoin.widget.browser import DataBrowserWidget

        browser = DataBrowserWidget(request)
        browser.setData(data)
        return browser.render()

    # No data
    return ''

