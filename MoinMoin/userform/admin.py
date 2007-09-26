# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - User account administration

    @copyright: 2001-2004 Juergen Hermann <jh@web.de>,
                2003-2007 MoinMoin:ThomasWaldmann
                2007 MoinMoin:ReimarBauer
    @license: GNU GPL, see COPYING for details.
"""
from MoinMoin import user, wikidicts
from MoinMoin.util.dataset import TupleDataset, Column
from MoinMoin.Page import Page


def do_user_browser(request):
    """ Browser for SystemAdmin macro. """
    _ = request.getText

    data = TupleDataset()
    data.columns = [
        #Column('id', label=('ID'), align='right'),
        Column('name', label=('Username')),
        Column('acl groups', label=('ACL Groups')),
        Column('email', label=('Email')),
        Column('jabber', label=('Jabber')),
        Column('action', label=_('Action')),
    ]

    isgroup = request.cfg.cache.page_group_regex.search
    grouppages = request.rootpage.getPageList(user='', filter=isgroup)

    # Iterate over users
    for uid in user.getUserList(request):
        account = user.User(request, uid)
        list_acl_pages = []
        for pagename in grouppages:
            members, groups = request.dicts.expand_group(pagename)
            pagename_link = Page(request, pagename).link_to(request)
            if account.name in members:
                list_acl_pages.append(pagename_link)
        list_groups = ', '.join(list_acl_pages)

        userhomepage = Page(request, account.name)
        if userhomepage.exists():
            namelink = userhomepage.link_to(request)
        else:
            namelink = account.name

        data.addRow((
            #request.formatter.code(1) + uid + request.formatter.code(0),
            # 0
            request.formatter.rawHTML(namelink),
            # 1
            request.formatter.rawHTML(list_groups),
            # 2
            (request.formatter.url(1, 'mailto:' + account.email, css='mailto', do_escape=0) +
             request.formatter.text(account.email) +
             request.formatter.url(0)),
            # 3
            (request.formatter.url(1, 'xmpp:' + account.jid, css='mailto', do_escape=0) +
             request.formatter.text(account.jid) +
             request.formatter.url(0)),
            # 4
            (request.page.link_to(request, text=_('Mail account data'),
                                 querystr={"action": "recoverpass",
                                           "email": account.email,
                                           "account_sendmail": "1",
                                           "sysadm": "users", },
                                 rel='nofollow'))
        ))

    if data:
        from MoinMoin.widget.browser import DataBrowserWidget

        browser = DataBrowserWidget(request)
        browser.setData(data)
        return browser.toHTML()

    # No data
    return ''

