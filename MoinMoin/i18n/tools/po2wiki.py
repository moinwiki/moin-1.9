#!/usr/bin/python
"""
    remove everthing top of the first msgid line (PIs destroyed by gettext),
    prepend some processing instructions to a .po file to be able to put it
    onto moinmaster wiki, letting it get processed by gettext parser
"""

master_url = "http://master19.moinmo.in/?action=xmlrpc2"
user = "ThomasWaldmann" # must be a known Wiki account

import sys, os
import xmlrpclib

password = os.environ.get("PASS", "")
sys.path.insert(0, '../..')

def run():
    excluded = ["en", ] # languages managed in repository, not in wiki

    lang = sys.argv[1]

    data = sys.stdin.read()

    if lang in excluded:
        f = open("%s.MoinMoin.po" % lang, "w")
        f.write(data)
        f.close()
        sys.exit(0)

    data = data.decode('utf-8')

    cutpos = data.index(u"msgid")
    data = data[cutpos:] # remove comments at top

    data = u"""\
## Please edit system and help pages ONLY in the master wiki!
## For more information, please see MoinMoin:MoinDev/Translation.
##master-page:None
##master-date:None
#acl -All:write Default
#format gettext
#language %s

#
# MoinMoin %s system text translation
#
%s""" % (lang, lang, data)


    pagename = "MoinI18n/%s" % lang
    pagedata = data.encode('utf-8')

    wiki = xmlrpclib.ServerProxy(master_url)
    token = wiki.getAuthToken(user, password)
    mc = xmlrpclib.MultiCall(wiki)
    mc.applyAuthToken(token)
    mc.WhoAmI() # then we see in the result if auth worked correctly!
    mc.putPage(pagename, pagedata)
    mc.deleteAuthToken(token)
    result = mc()
    print "Page: %s rc=%r" % (pagename, list(result))

if __name__ == "__main__":
    run()

