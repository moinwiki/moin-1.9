# -*- coding: iso-8859-1 -*-
# IMPORTANT! This encoding (charset) setting MUST be correct! If you live in a
# western country and you don't know that you use utf-8, you probably want to
# use iso-8859-1 (or some other iso charset). If you use utf-8 (a Unicode
# encoding) you MUST use: coding: utf-8
# That setting must match the encoding your editor uses when you modify the
# settings below. If it does not, special non-ASCII chars will be wrong.

"""
    MoinMoin - Configuration for a wiki farm

    This is a sample configuration for a farm using ldap and smb auth plugins.

    !!! NEEDS UPDATE FOR MOIN 1.7 !!!

    It works like this:
    * user logs in via moin's form on UserPreferences
    * ldap_login plugin checks username/password against LDAP
      * if username/password is ok for LDAP, the plugin creates a user profile
        with up-to-date settings from ldap (name, alias, email and crypted
        password) and just hands over to the next auth plugin...
      * if username/password is not ok for LDAP, it does not store/update
        a user profile, but also hands over to the next auth plugin.
    * smb_mount plugin also gets username/password and uses it to mount another
      server's share on some mountpoint (using access rights of username,
      authenticating using password) on the wiki server (very special use only -
      if you don't need it, don't use it).
    * moin_cookie finally gets username/password and uses it to load the
      user's profile, set a cookie for subsequent requests and return a user
      object.

"""

# Wikis in your farm --------------------------------------------------

# If you run multiple wikis, you need this list of pairs (wikiname, url
# regular expression). moin processes that list and tries to match the
# regular expression against the URL of this request - until it matches.
# Then it loads the <wikiname>.py config for handling that request.

# Important:
#  * the left part is the wikiname enclosed in double quotes
#  * the left part must be a valid python module name, so better use only
#    lower letters "a-z" and "_". Do not use blanks or "-" there!!!
#  * the right part is the url re, use r"..." for it
#  * the right part does NOT include "http://" nor "https://" at the beginning
#  * in the right part ".*" means "everything". Just "*" does not work like
#    for filenames on the shell / commandline, you must use ".*" as it is a RE.
#  * in the right part, "^" means "beginning" and "$" means "end"

wikis = [
    # Standalone server needs the port e.g. localhost:8000
    # Twisted server can now use the port, too.

    # wikiname,     url regular expression (no protocol)
    # ---------------------------------------------------------------
    ("info1", r"^info1.example.org/.*$"),
    ("info2", r"^info2.example.org/.*$"),
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

from MoinMoin.config.multiconfig import DefaultConfig

# Now we subclass this DefaultConfig. This means that we inherit every setting
# from the DefaultConfig, except those we explicitely define different.

class FarmConfig(DefaultConfig):

    from MoinMoin import auth as authmod
    auth = [authmod.ldap_login, authmod.smb_mount, authmod.moin_session]

    import ldap
    ldap_uri = 'ldap://ad.example.org' # ldap / active directory server URI

    # We can either use some fixed user and password for binding to LDAP.
    # Be careful if you need a % char in those strings - as they are used as
    # a format string, you have to write %% to get a single % in the end.
    #ldap_binddn = 'binduser@example.org'
    #ldap_bindpw = 'secret'

    #or we can use the username and password we got from the user:
    ldap_binddn = '%(username)s@example.org' # DN we use for first bind (AD)
    #ldap_binddn = 'cn=admin,dc=example,dc=org' # DN we use for first bind (OpenLDAP)
    ldap_bindpw = '%(password)s' # password we use for first bind

    ldap_base = 'ou=SOMEUNIT,dc=example,dc=org' # base DN we use for searching
    ldap_scope = ldap.SCOPE_SUBTREE # scope of the search we do
    ldap_filter = '(sAMAccountName=%(username)s)' # ldap filter used for searching
    # you can also do more complex filtering like:
    # "(&(cn=%(username)s)(memberOf=CN=WikiUsers,OU=Groups,DC=example,DC=org))"
    ldap_givenname_attribute = 'givenName' # ldap attribute we get the first name from
    ldap_surname_attribute = 'sn' # ldap attribute we get the family name from
    ldap_aliasname_attribute = 'displayName' # ldap attribute we get the aliasname from
    ldap_email_attribute = 'mail' # ldap attribute we get the email address from
    ldap_coding = 'utf-8' # coding used for ldap queries and result values
    ldap_timeout = 10 # how long we wait for the ldap server [s]
    ldap_verbose = True # if True, put lots of LDAP debug info into the log
    ldap_bindonce = False # set to True to only do one bind.  Useful if
                          # configured to bind as the user on the first attempt
    cookie_lifetime = 1 # 1 hour after last access ldap login is required again
    user_autocreate = True

    smb_server = "smb.example.org" # smb server name
    smb_domain = 'DOMAIN' # smb domain name
    smb_share = 'FILESHARE' # smb share we mount
    smb_mountpoint = u'/mnt/wiki/%(username)s' # where we mount the smb filesystem
    smb_display_prefix = u"S:" # where //server/share is usually mounted for your windows users (display purposes only)
    smb_dir_user = "wwwrun" # owner of the mounted directories
    smb_dir_mode = "0700" # mode of the mounted directories
    smb_file_mode = "0600" # mode of the mounted files
    smb_iocharset = "iso8859-1" # "UTF-8" > cannot access needed shared library!
    smb_coding = 'iso8859-1' # coding used for encoding the commandline for the mount command
    smb_verbose = True # if True, put SMB debug info into log
    smb_log = "/dev/null" # where we redirect mount command output to

    # customize UserPreferences (optional)
    user_checkbox_remove = [
        'disabled', 'remember_me', 'edit_on_doubleclick', 'show_nonexist_qm',
        'show_toolbar', 'show_topbottom', 'show_fancy_diff',
        'wikiname_add_spaces', ]
    user_checkbox_defaults = {'mailto_author':       0,
                              'edit_on_doubleclick': 0,
                              'remember_last_visit': 0,
                              'show_nonexist_qm':    0,
                              'show_page_trail':     1,
                              'show_toolbar':        1,
                              'show_topbottom':      0,
                              'show_fancy_diff':     1,
                              'wikiname_add_spaces': 0,
                              'remember_me':         0,
                              'want_trivial':        0,
                             }
    user_form_defaults = {
        # key: default
        'name': '',
        'aliasname': '',
        'password': '',
        'password2': '',
        'email': '',
        'css_url': '',
        'edit_rows': "20",
    }
    user_form_disable = ['name', 'aliasname', 'email', ]
    user_form_remove = ['password', 'password2', 'css_url', 'logout', 'create', 'account_sendmail', ]

    # Critical setup  ---------------------------------------------------

    # Misconfiguration here will render your wiki unusable. Check that
    # all directories are accessible by the web server or moin server.

    # If you encounter problems, try to set data_dir and data_underlay_dir
    # to absolute paths.

    # Where your mutable wiki pages are. You want to make regular
    # backups of this directory.
    data_dir = './data/'

    # Where read-only system and help page are. You might want to share
    # this directory between several wikis. When you update MoinMoin,
    # you can safely replace the underlay directory with a new one. This
    # directory is part of MoinMoin distribution, you don't have to
    # backup it.
    data_underlay_dir = './underlay/'

    # This must be '/wiki' for twisted and standalone. For CGI, it should
    # match your Apache Alias setting.
    url_prefix = '/wiki'


    # Security ----------------------------------------------------------

    # This is checked by some rather critical and potentially harmful actions,
    # like despam or PackageInstaller action:
    #superuser = [u"AdminName", ]

    # IMPORTANT: grant yourself admin rights! replace YourName with
    # your user name. See HelpOnAccessControlLists for more help.
    # All acl_rights_xxx options must use unicode [Unicode]
    acl_rights_before = u"AdminGroup:admin,read,write,delete,revert"
    acl_rights_default = u"EditorGroup:read,write.delete,revert ViewerGroup:read All:"

    # Link spam protection for public wikis (uncomment to enable).
    # Needs a reliable internet connection.
    from MoinMoin.security.autoadmin import SecurityPolicy


    # Mail --------------------------------------------------------------

    # Configure to enable subscribing to pages (disabled by default) or
    # sending forgotten passwords.

    # SMTP server, e.g. "mail.provider.com" (empty or None to disable mail)
    mail_smarthost = "mail.example.org"

    # The return address, e.g u"Jürgen Wiki <noreply@mywiki.org>" [Unicode]
    mail_from = u"wiki@example.org"

    # "user pwd" if you need to use SMTP AUTH
    mail_login = ""


    # User interface ----------------------------------------------------

    # Add your wikis important pages at the end. It is not recommended to
    # remove the default links.  Leave room for user links - don't use
    # more than 6 short items.
    # You MUST use Unicode strings here, but you need not use localized
    # page names for system and help pages, those will be used automatically
    # according to the user selected language. [Unicode]
    navi_bar = [
        # If you want to show your page_front_page here:
        u'%(page_front_page)s',
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
    language_default = 'de'

    # You must use Unicode strings here [Unicode]
    page_category_regex = u'^Category[A-Z]'
    page_dict_regex = u'[a-z]Dict$'
    page_group_regex = u'[a-z]Group$'
    page_template_regex = u'[a-z]Template$'

    # Content options ---------------------------------------------------

    # Show users hostnames in RecentChanges
    show_hosts = 1

    # Show the interwiki name (and link it to page_front_page) in the Theme,
    # nice for farm setups or when your logo does not show the wiki's name.
    show_interwiki = 1
    logo_string = u''

    # Enable graphical charts, requires gdchart.
    #chart_options = {'width': 600, 'height': 300}

    # interwiki map
    #shared_intermap = ["/opt/moinfarm/common/intermap.txt", ]

