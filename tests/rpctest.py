# -*- coding: iso-8859-1 -*-
import xmlrpclib

if __name__ == "__main__":

    server = xmlrpclib.ServerProxy('http://127.0.0.1/cgi-bin/wiki.bat/?action=xmlrpc')
    print server

    try:
        frontpage = server.getPage('FrontPage').data.decode('UTF-8')
        print "Length of FrontPage:", len(frontpage)
        print "Start of FrontPage:", repr(frontpage[:50]), "..."
        print "End of FrontPage:", "...", repr(frontpage[-50:])
        print "Interface Version:", server.getRPCVersionSupported()
        print "Number of Pages:", len(server.getAllPages())
    except xmlrpclib.Error, v:
        print "ERROR", v

