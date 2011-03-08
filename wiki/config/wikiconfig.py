# -*- coding: iso-8859-1 -*-
# IMPORTANT! This encoding (charset) setting MUST be correct! If you live in a
# western country and you don't know that you use utf-8, you probably want to
# use iso-8859-1 (or some other iso charset). If you use utf-8 (a Unicode
# encoding) you MUST use: coding: utf-8
# That setting must match the encoding your editor uses when you modify the
# settings below. If it does not, special non-ASCII chars will be wrong.

"""
    MoinMoin - Configuration for a single wiki

    If you run a single wiki only, you can omit the farmconfig.py config
    file and just use wikiconfig.py - it will be used for every request
    we get in that case.

    Note that there are more config options than you'll find in
    the version of this file that is installed by default; see
    the module MoinMoin.config.multiconfig for a full list of names and their
    default values.

    Also, the URL http://moinmo.in/HelpOnConfiguration has
    a list of config options.

    ** Please do not use this file for a wiki farm. Use the sample file
    from the wikifarm directory instead! **
"""

import os

from MoinMoin.config import multiconfig, url_prefix_static


class Config(multiconfig.DefaultConfig):

    # Critical setup  ---------------------------------------------------

    # Directory containing THIS wikiconfig:
    wikiconfig_dir = os.path.abspath(os.path.dirname(__file__))

    # We assume that this config file is located in the instance directory, like:
    # instance_dir/
    #              wikiconfig.py
    #              data/
    #              underlay/
    # If that's not true, feel free to just set instance_dir to the real path
    # where data/ and underlay/ is located:
    #instance_dir = '/where/ever/your/instance/is'
    instance_dir = wikiconfig_dir

    # Where your own wiki pages are (make regular backups of this directory):
    data_dir = os.path.join(instance_dir, 'data', '') # path with trailing /

    # Where system and help pages are (you may exclude this from backup):
    data_underlay_dir = os.path.join(instance_dir, 'underlay', '') # path with trailing /

    # The URL prefix we use to access the static stuff (img, css, js).
    # Note: moin runs a static file server at url_prefix_static path (relative
    # to the script url).
    # If you run your wiki script at the root of your site (/), just do NOT
    # use this setting and it will automatically work.
    # If you run your wiki script at /mywiki, you need to use this:
    #url_prefix_static = '/mywiki' + url_prefix_static


    # Wiki identity ----------------------------------------------------

    # Site name, used by default for wiki name-logo [Unicode]
    sitename = u'Untitled Wiki'

    # Wiki logo. You can use an image, text or both. [Unicode]
    # For no logo or text, use '' - the default is to show the sitename.
    # See also url_prefix setting below!
    logo_string = u'<img src="%s/common/moinmoin.png" alt="MoinMoin Logo">' % url_prefix_static

    # name of entry page / front page [Unicode], choose one of those:

    # a) if most wiki content is in a single language
    #page_front_page = u"MyStartingPage"

    # b) if wiki content is maintained in many languages
    #page_front_page = u"FrontPage"

    # The interwiki name used in interwiki links
    #interwikiname = u'UntitledWiki'
    # Show the interwiki name (and link it to page_front_page) in the Theme,
    # nice for farm setups or when your logo does not show the wiki's name.
    #show_interwiki = 1


    # Security ----------------------------------------------------------

    # This is checked by some rather critical and potentially harmful actions,
    # like despam or PackageInstaller action:
    #superuser = [u"YourName", ]

    # IMPORTANT: grant yourself admin rights! replace YourName with
    # your user name. See HelpOnAccessControlLists for more help.
    # All acl_rights_xxx options must use unicode [Unicode]
    #acl_rights_before = u"YourName:read,write,delete,revert,admin"

    # The default (ENABLED) password_checker will keep users from choosing too
    # short or too easy passwords. If you don't like this and your site has
    # rather low security requirements, feel free to DISABLE the checker by:
    #password_checker = None # None means "don't do any password strength checks"

    # Link spam protection for public wikis (Uncomment to enable)
    # Needs a reliable internet connection.
    #from MoinMoin.security.antispam import SecurityPolicy


    # Mail --------------------------------------------------------------

    # Configure to enable subscribing to pages (disabled by default)
    # or sending forgotten passwords.

    # SMTP server, e.g. "mail.provider.com" (None to disable mail)
    #mail_smarthost = ""

    # The return address, e.g u"J�rgen Wiki <noreply@mywiki.org>" [Unicode]
    #mail_from = u""

    # "user pwd" if you need to use SMTP AUTH
    #mail_login = ""


    # User interface ----------------------------------------------------

    # Add your wikis important pages at the end. It is not recommended to
    # remove the default links.  Leave room for user links - don't use
    # more than 6 short items.
    # You MUST use Unicode strings here, but you need not use localized
    # page names for system and help pages, those will be used automatically
    # according to the user selected language. [Unicode]
    navi_bar = [
        # If you want to show your page_front_page here:
        #u'%(page_front_page)s',
        u'RecentChanges',
        u'FindPage',
        u'HelpContents',
    ]

    # The default theme anonymous or new users get
    theme_default = 'modernized'


    # Language options --------------------------------------------------

    # See http://moinmo.in/ConfigMarket for configuration in
    # YOUR language that other people contributed.

    # The main wiki language, set the direction of the wiki pages
    language_default = 'en'

    # the following regexes should match the complete name when used in free text
    # the group 'all' shall match all, while the group 'key' shall match the key only
    # e.g. CategoryFoo -> group 'all' ==  CategoryFoo, group 'key' == Foo
    # moin's code will add ^ / $ at beginning / end when needed
    # You must use Unicode strings here [Unicode]
    page_category_regex = ur'(?P<all>Category(?P<key>(?!Template)\S+))'
    page_dict_regex = ur'(?P<all>(?P<key>\S+)Dict)'
    page_group_regex = ur'(?P<all>(?P<key>\S+)Group)'
    page_template_regex = ur'(?P<all>(?P<key>\S+)Template)'

    # Content options ---------------------------------------------------

    # Show users hostnames in RecentChanges
    show_hosts = 1

    # Enable graphical charts, requires gdchart.
    #chart_options = {'width': 600, 'height': 300}

