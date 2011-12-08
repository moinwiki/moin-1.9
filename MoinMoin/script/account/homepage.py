# -*- coding: iso-8859-1 -*-
"""
MoinMoin - creates user homepage for existing accounts

@copyright: 2009 MoinMoin:ReimarBauer
@license: GNU GPL, see COPYING for details.
"""

from MoinMoin import user
from MoinMoin.Page import Page
from MoinMoin.PageEditor import PageEditor
from MoinMoin.script import MoinScript
from MoinMoin.mail.sendmail import encodeSpamSafeEmail


class PluginScript(MoinScript):
    """\
Purpose:
========
This tool allows you to create user homepages via a command line interface.

Detailed Instructions:
======================
General syntax: moin [options] account homepage [homepage-options]

[options] usually should be:
    --config-dir=/path/to/my/cfg/ --wiki-url=http://wiki.example.org/

1. Required is one of the options --name, --group or --all-users.
To create the homepage of one user use the --name argument. For adding homepages to a group of users
give the --group page argument. Or with --all-users you create homepages for ALL users.
2. To respect ACLs  give the --user argument.
3. Optionally you may want to use a template page by the --template_page argument.
With e.g. #acl @ME@:read,write,delete,revert Default on the template page you can define
acl rights for the user. @EMAIL@ becomes expanded to the users obfuscated mail address.
"""

    def __init__(self, argv, def_values):
        MoinScript.__init__(self, argv, def_values)

        self.parser.add_option(
            "-u", "--user", dest="homepage_creator",
            help="User as whom the homepage creation operation will be performed as."
            )

        self.parser.add_option(
            "-t", "--template_page", dest="template_page",
            help="The template page which should be used for the homepage creation"
            )

        self.parser.add_option(
            "-n", "--name", dest="user_homepage",
            help="The name of the user the homepage should be created for."
            )

        self.parser.add_option(
            "-g", "--group", dest="name_of_group_page",
            help="The name of the group page to select users for creating their homepages."
            )

        self.parser.add_option(
            "-a", "--all-users", dest="all_users", action="store_true",
            help="The name of the group page to select users for creating their homepages."
            )

    def write_homepage(self, account, homepage_text):
        # writes the homepage
        if account.exists() and not account.disabled and not Page(self.request, account.name).exists():
            userhomepage = PageEditor(self.request, account.name)
            try:
                userhomepage.saveText(homepage_text, 0)
                print "INFO homepage for %s created." % account.name
            except userhomepage.Unchanged:
                print "You did not change the page content, not saved!"
            except userhomepage.NoAdmin:
                print "You don't have enough rights to create the %s page" % account.name
        else:
            print "INFO homepage for %s already exists or account is disabled or user does not exist." % account.name

    def mainloop(self):
        # we don't expect non-option arguments
        self.init_request()
        request = self.request
        # Checks for a template page and sets homepage_default_text
        if self.options.template_page and Page(self.request, self.options.template_page).exists():
            homepage_default_text = Page(self.request, self.options.template_page).get_raw_body()
            # replace is needed because substitution is done for request.user
            # see option --user
            homepage_default_text = homepage_default_text.replace('@ME@', "%(username)s")
            homepage_default_text = homepage_default_text.replace('@EMAIL@', "<<MailTo(%(obfuscated_mail)s)>>")
        else:
            homepage_default_text = '''#acl %(username)s:read,write,delete,revert Default
#format wiki

== %(username)s ==

Email: <<MailTo(%(obfuscated_mail)s)>>
## You can even more obfuscate your email address by adding more uppercase letters followed by a leading and trailing blank.

----
CategoryHomepage
'''
        # Check for user
        if self.options.homepage_creator:
            uid = user.getUserId(request, self.options.homepage_creator)
            request.user = user.User(request, uid)
        # Check for Group definition
        members = []
        if self.options.user_homepage:
            members = [self.options.user_homepage, ]
        elif self.options.name_of_group_page:
            members = request.groups.get(self.options.name_of_group_page, [])
        elif self.options.all_users:
            uids = user.getUserList(request)
            members = [user.User(request, uid).name for uid in uids]

        if not members:
            print "No user selected!"
            return

        # loop through members for creating homepages
        for name in members:
            uid = user.getUserId(request, name)
            account = user.User(request, uid)
            homepage_text = homepage_default_text % {
                                                 "username": account.name,
                                                 "obfuscated_mail": encodeSpamSafeEmail(account.email)
                                                 }
            self.write_homepage(account, homepage_text)
