#!/usr/bin/python
"""
    get latest translation page content from the wiki and write it to *.po
"""
def run():
    import sys, xmlrpclib
    sys.path.insert(0, '../..')

    excluded = ["en",] # languages managed in repository, not in wiki

    langfname = sys.argv[1]
    lang = langfname.replace('_', '-') # module names use _ instead of -

    if not lang in excluded:
        wiki = xmlrpclib.ServerProxy("http://moinmaster.wikiwikiweb.de/?action=xmlrpc2")

        pagename = "MoinI18n/%s" % lang
        pagedata = wiki.getPage(pagename).encode('utf-8').replace("\n","\r\n")

        f = open("%s.po" % langfname, "w")
        f.write(pagedata)
        f.close()

if __name__ == "__main__":
    run()

