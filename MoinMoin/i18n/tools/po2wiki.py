#!/usr/bin/python
"""
    remove everthing top of the first msgid line (PIs destroyed by gettext),
    prepend some processing instructions to a .po file to be able to put it
    onto moinmaster wiki, letting it get processed by gettext parser
"""
def run():
    import sys, os, xmlrpclib
    sys.path.insert(0, '../../..')

    excluded = ["en",] # languages managed in repository, not in wiki

    lang = sys.argv[1]
    lang = lang.replace('_', '-') # module names use _ instead of -

    data = sys.stdin.read()

    if lang in excluded:
        f = open("%s.po" % lang, "w")
        f.write(data)
        f.close()
        sys.exit(0)
        
    data = data.decode('utf-8')

    cutpos = data.index(u"msgid")
    data = data[cutpos:] # remove comments at top

    data = u"""\
## Please edit system and help pages ONLY in the moinmaster wiki! For more
## information, please see MoinMaster:MoinPagesEditorGroup.
##master-page:None
##master-date:None
#acl MoinPagesEditorGroup:read,write,delete,revert All:read
#format gettext
#language %s

#
# MoinMoin %s system text translation
#
%s""" % (lang, lang, data)


    from MoinMoin.support.BasicAuthTransport import BasicAuthTransport

    user = "ThomasWaldmann" # must be a known Wiki account
    password = os.environ.get("PASS", "")
    pagename = "MoinI18n/%s" % lang
    pagedata = data.encode('utf-8')

    authtrans = BasicAuthTransport(user, password)
    wiki = xmlrpclib.ServerProxy("http://moinmaster.wikiwikiweb.de/?action=xmlrpc2", transport=authtrans)

    rc = wiki.putPage(pagename, pagedata)
    print "Page: %s rc=%s" % (pagename, rc)

if __name__ == "__main__":
    run()

