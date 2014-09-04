# -*- coding: iso-8859-1 -*-
# IMPORTANT! This encoding (charset) setting MUST be correct! If you live in a
# western country and you don't know that you use utf-8, you probably want to
# use iso-8859-1 (or some other iso charset). If you use utf-8 (a Unicode
# encoding) you MUST use: coding: utf-8
# That setting must match the encoding your editor uses when you modify the
# settings below. If it does not, special non-ASCII chars will be wrong.

"""
    MoinMoin - Configuration for a wiki farm

    If you run a single wiki only, you can keep the "wikis" list "as is"
    (it has a single rule mapping all requests to mywiki.py).

    Note that there are more config options than you'll find in
    the version of this file that is installed by default; see
    the module MoinMoin.config.multiconfig for a full list of names and their
    default values.

    Also, the URL http://moinmo.in/HelpOnConfiguration has
    a list of config options.
"""


# Wikis in your farm --------------------------------------------------

# If you run multiple wikis, you need this list of pairs (wikiname, url
# regular expression). moin processes that list and tries to match the
# regular expression against the URL of this request - until it matches.
# Then it loads the <wikiname>.py config for handling that request.

# Important:
#  * the left part is the wikiname enclosed in double quotes
#  * the left part must be a valid python module name, so better use only
#    lower letters "a-z" and "_". Do not use blanks, dots or minus there!
#    E.g. use "foo_bar_org", NOT: "foo-bar.org"!
#  * the right part is the url re, use r"..." for it
#  * in the right part ".*" means "everything". Just "*" does not work like
#    for filenames on the shell / commandline, you must use ".*" as it is a RE.
#  * in the right part, "^" means "beginning" and "$" means "end"

wikis = [

    # wikiname, url regular expression
    # ---------------------------------------------------------------
    ("mywiki", r".*"),   # this is ok for a single wiki

    # for multiple wikis, do something like this:
    #("wiki1", r"^http://wiki1\.example\.org/.*$"),
    #("wiki2", r"^https?://wiki2\.example\.org/.*$"),
]


# Common configuration for all wikis ----------------------------------

# Everything that should be configured the same way should go here,
# anything else that should be different should go to the single wiki's
# config.
# In that single wiki's config, we will use the class FarmConfig we define
# below as the base config settings and only override what's different.
#
# In exactly the same way, we first include MoinMoin's Config Defaults here -
# this is to get everything to sane defaults, so we need to change only what
# we like to have different:

from MoinMoin.config import multiconfig, url_prefix_static

# Now we subclass this DefaultConfig. This means that we inherit every setting
# from the DefaultConfig, except those we explicitely define different.

class FarmConfig(multiconfig.DefaultConfig):

    # Critical setup  ---------------------------------------------------

    # The URL prefix we use to access the static stuff (img, css, js).
    # Note: moin runs a static file server at url_prefix_static path (relative
    # to the script url).
    # If you run your wiki script at the root of your site (/), just do NOT
    # use this setting and it will automatically work.
    # If you run your wiki script at /mywiki, you need to use this:
    #url_prefix_static = '/mywiki' + url_prefix_static
    # If you need different url_prefix_static setups for your wikis,
    # you'll have to do it in each wiki's config.

    # Security ----------------------------------------------------------

    # This is checked by some rather critical and potentially harmful actions,
    # like despam or PackageInstaller action:
    #superuser = [u"YourName", ]

    # IMPORTANT: grant yourself admin rights! replace YourName with
    # your user name. See HelpOnAccessControlLists for more help.
    # All acl_rights_xxx options must use unicode [Unicode]
    #acl_rights_before = u"YourName:read,write,delete,revert,admin"

    # Link spam protection for public wikis (uncomment to enable).
    # Needs a reliable internet connection.
    #from MoinMoin.security.antispam import SecurityPolicy


    # Mail --------------------------------------------------------------

    # Configure to enable subscribing to pages (disabled by default) or
    # sending forgotten passwords.

    # SMTP server, e.g. "mail.provider.com" (empty or None to disable mail)
    #mail_smarthost = ""

    # The return address, e.g u"Jürgen Wiki <noreply@mywiki.org>" [Unicode]
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
    theme_default = 'modern'


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
    page_category_regex = ur'(?P<all>Category(?P<key>\S+))'
    page_dict_regex = ur'(?P<all>(?P<key>\S+)Dict)'
    page_group_regex = ur'(?P<all>(?P<key>\S+)Group)'
    page_template_regex = ur'(?P<all>(?P<key>\S+)Template)'

    # Content options ---------------------------------------------------

    # Show users hostnames in RecentChanges
    show_hosts = 1

    # Show the interwiki name (and link it to page_front_page) in the Theme,
    # nice for farm setups or when your logo does not show the wiki's name.
    show_interwiki = 1
    logo_string = u''

    # Enable graphical charts, requires gdchart.
    #chart_options = {'width': 600, 'height': 300}

