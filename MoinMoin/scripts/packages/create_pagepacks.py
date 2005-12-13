#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Package Generator

    @copyright: 2005 by Alexander Schremmer
    @license: GNU GPL, see COPYING for details.
"""

import os, sys
import zipfile
import threading
import xmlrpclib
from sets import Set
from datetime import datetime
from time import sleep

# your MoinMoin package path here
sys.path.insert(0, r"../../..")
sys.path.insert(0, r".")

from MoinMoin import config, wikidicts, wikiutil
from MoinMoin.Page import Page
from MoinMoin.PageEditor import PageEditor
from MoinMoin.request import RequestCLI
from MoinMoin.packages import packLine, unpackLine, MOIN_PACKAGE_FILE

master_url ="http://moinmaster.wikiwikiweb.de/?action=xmlrpc2"

EXTRA = u'extra'
ALL = u'all_languages'
COMPRESSION_LEVEL = zipfile.ZIP_STORED

def buildPageSets():
    """ Calculates which pages should go into which package. """
    pageSets = {}

    allPages = Set()

    masterSet = Set(xmlrpclib.ServerProxy(master_url).getAllPages())

    systemPages = wikidicts.Group(request, "SystemPagesGroup").members()

    specialPages = Set([x for x in systemPages if not x.endswith("Group")] + ["SystemPagesGroup"])

    for pagename in systemPages:
        if pagename.endswith("Group"):
            #print x + " -> " + repr(wikidicts.Group(request, x).members())
            gd.addgroup(request, pagename)

    for name, group in gd.dictdict.items():
        group.expandgroups(gd)
        groupPages = Set(group.members() + [name])
        name = name.replace("SystemPagesIn", "").replace("Group", "")
        pageSets[name] = groupPages
        allPages |= groupPages

    masterNonSystemPages = masterSet - allPages - specialPages

    frontPagesEtc = Set([x for x in masterNonSystemPages if not (
        x.startswith("MoinI18n") or x == "MoinPagesEditorGroup" or
        x == "InterWikiMap"
        )])

    specialPages |= frontPagesEtc

    pageSets[EXTRA] = specialPages

    pageSets[ALL] = allPages

    for name in pageSets.keys():
        if name not in (EXTRA, u"English"):
            pageSets[name] -= pageSets[EXTRA]
            pageSets[name] -= pageSets[u"English"]

    return pageSets

def packagePages(pagelist, filename, function):
    """ Puts pages from pagelist into filename and calls function on them on installation. """
    try:
        os.remove(filename)
    except OSError:
        pass
    zf = zipfile.ZipFile(filename, "w", COMPRESSION_LEVEL)

    cnt = 0
    script = [packLine(['MoinMoinPackage', '1']),
              ]

    for pagename in pagelist:
        pagename = pagename.strip()
        page = Page(request, pagename)
        if page.exists():
            cnt += 1
            script.append(packLine([function, str(cnt), pagename]))
            timestamp = wikiutil.version2timestamp(page.mtime_usecs())
            zi = zipfile.ZipInfo(filename=str(cnt), date_time=datetime.fromtimestamp(timestamp).timetuple()[:6])
            zi.compress_type = COMPRESSION_LEVEL
            zf.writestr(zi, page.get_raw_body().encode("utf-8"))
        else:
            #print >>sys.stderr, "Could not find the page %s." % pagename.encode("utf-8")
            pass

    script += [packLine(['Print', 'Installed MoinMaster page bundle %s.' % os.path.basename(filename)])]

    zf.writestr(MOIN_PACKAGE_FILE, u"\n".join(script).encode("utf-8"))
    zf.close()

def packageCompoundInstaller(bundledict, filename):
    """ Creates a package which installs all other packages. """
    try:
        os.remove(filename)
    except OSError:
        pass
    zf = zipfile.ZipFile(filename, "w", COMPRESSION_LEVEL)

    script = [packLine(['MoinMoinPackage', '1']),
              ]

    script += [packLine(["InstallPackage", "SystemPagesSetup", name + ".zip"])
               for name in bundledict.keys() if name not in (EXTRA, ALL, u"English")]
    script += [packLine(['Print', 'Installed all MoinMaster page bundles.'])]

    zf.writestr(MOIN_PACKAGE_FILE, u"\n".join(script).encode("utf-8"))
    zf.close()

def getMasterPages():
    """ Leechezzz. """
    master = xmlrpclib.ServerProxy(master_url)
    maxThreads = 100

    def downloadpage(wiki, pagename):
        source = wiki.getPage(pagename)
        if source.find("##master-page:FrontPage") != -1:
            source += u"""\n\n||<tablestyle="background: lightyellow; width:100%; text-align:center">[[en]] If you want to add help pages in your favorite language, see '''SystemPagesSetup'''.||\n"""

        PageEditor(request, pagename, uid_override="Fetching ...")._write_file(source)
        #print "Fetched " + pagename.encode("utf-8")

    stopped = []
    running = []

    print "Loading master page list ..."
    pagelist = master.getAllPages()
    print "Preparing threads ..."
    for pagename in pagelist:
        t = threading.Thread(target=downloadpage, args=(master, pagename), name=pagename.encode("unicode_escape"))
        stopped.append(t)

    print "Starting scheduler ..."
    while len(running) > 0 or len(stopped) != 0:
        for x in running:
            if not x.isAlive():
                #print "Found dead thread " + repr(x)
                running.remove(x)
        print "running %i| stopped %i" % (len(running), len(stopped))
        for i in xrange(min(maxThreads - len(running), len(stopped))):
            t = stopped.pop()
            running.append(t)
            t.start()
            #print "Scheduled %s." % repr(t)
        sleep(1)

request = RequestCLI(url='localhost/')
request.form = request.args = request.setup_args()

gd = wikidicts.GroupDict(request)
gd.reset()

#getMasterPages()
print "Building page sets ..."
pageSets = buildPageSets()

print "Creating packages ..."
generate_filename = lambda name: os.path.join('testwiki', 'underlay', 'pages', 'SystemPagesSetup', 'attachments', '%s.zip' % name)

packageCompoundInstaller(pageSets, generate_filename(ALL))
[packagePages(list(pages), generate_filename(name), "ReplaceUnderlay") for name, pages in pageSets.items() if name != ALL]

print "Finished."

