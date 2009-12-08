# -*- coding: iso-8859-1 -*-
"""
MoinMoin - Package Generator

@copyright: 2005 Alexander Schremmer,
            2006 MoinMoin:ThomasWaldmann,
            2009 MoinMoin:ReimarBauer
@license: GNU GPL, see COPYING for details.
"""

import os
import zipfile
from datetime import datetime

from MoinMoin.support.python_compatibility import set
from MoinMoin import wikidicts, wikiutil
from MoinMoin.action.AttachFile import _get_files
from MoinMoin.Page import Page
from MoinMoin.action import AttachFile
from MoinMoin.packages import packLine, MOIN_PACKAGE_FILE
from MoinMoin.script import MoinScript

EXTRA = u'extra'
NODIST = u'nodist'
ALL = u'all_languages'
COMPRESSION_LEVEL = zipfile.ZIP_STORED

class PluginScript(MoinScript):
    """\
Purpose:
========
This tool generates a set of packages from all the pages in a wiki.

Detailed Instructions:
======================
General syntax: moin [options] maint mkpagepacks [mkpagepacks-options]

[options] usually should be:
    --config-dir=/path/to/my/cfg/ --wiki-url=wiki.example.org/

[mkpagepacks-options] see below:
    0. THIS SCRIPT SHOULD NEVER BE RUN ON ANYTHING OTHER THAN A TEST WIKI!

    1. This script takes no command line arguments.
"""

    def __init__(self, argv, def_values):
        MoinScript.__init__(self, argv, def_values)

    def buildPageSets(self):
        """ Calculates which pages should go into which package. """
        request = self.request
        pageSets = {}

        allPages = set(request.rootpage.getPageList())

        systemPages = wikidicts.Group(request, "SystemPagesGroup").members()

        for pagename in systemPages:
            if pagename.endswith("Group"):
                #print x + " -> " + repr(wikidicts.Group(request, x).members())
                self.gd.addgroup(request, pagename)

        langPages = set()
        for name, group in self.gd.dictdict.items():
            groupPages = set(group.members() + [name])
            name = name.replace("SystemPagesIn", "").replace("Group", "")
            pageSets[name] = groupPages
            langPages |= groupPages

        specialPages = set(["SystemPagesGroup"])

        masterNonSystemPages = allPages - langPages - specialPages

        moinI18nPages = set([x for x in masterNonSystemPages if x.startswith("MoinI18n")])

        nodistPages = moinI18nPages | set(["InterWikiMap", ])

        extraPages = masterNonSystemPages - nodistPages

        pageSets[ALL] = langPages

        for name in pageSets.keys():
            if name not in (u"English"):
                pageSets[name] -= pageSets[u"English"]
                pageSets[name] -= nodistPages

        pageSets[EXTRA] = extraPages   # stuff that maybe should be in some language group
        pageSets[NODIST] = nodistPages # we dont want to have them in dist archive
        return pageSets

    def packagePages(self, pagelist, filename, function):
        """ Puts pages from pagelist into filename and calls function on them on installation. """
        request = self.request
        try:
            os.remove(filename)
        except OSError:
            pass
        # page SystemPagesSetup needs no packing!
        existing_pages = [pagename for pagename in pagelist if Page(request, pagename).exists() and pagename != 'SystemPagesSetup']
        if not existing_pages:
            return

        zf = zipfile.ZipFile(filename, "w", COMPRESSION_LEVEL)

        cnt = 0
        script = [packLine(['MoinMoinPackage', '1']), ]

        for pagename in existing_pages:
            pagename = pagename.strip()
            page = Page(request, pagename)
            files = _get_files(request, pagename)
            for attname in files:
                cnt += 1
                zipname = "%d" % cnt
                script.append(packLine(["ReplaceUnderlayAttachment", zipname, attname, pagename]))
                attpath = AttachFile.getFilename(request, pagename, attname)
                zf.write(attpath, zipname)

            cnt += 1
            zipname = "%d" % cnt
            script.append(packLine([function, zipname, pagename]))
            timestamp = wikiutil.version2timestamp(page.mtime_usecs())
            zi = zipfile.ZipInfo(filename=str(cnt), date_time=datetime.fromtimestamp(timestamp).timetuple()[:6])
            zi.compress_type = COMPRESSION_LEVEL
            zf.writestr(zi, page.get_raw_body().encode("utf-8"))

        script += [packLine(['Print', 'Installed MoinMaster page bundle %s.' % os.path.basename(filename)])]

        zf.writestr(MOIN_PACKAGE_FILE, u"\n".join(script).encode("utf-8"))
        zf.close()

    def removePages(self, pagelist):
        """ Pages from pagelist get removed from the underlay directory. """
        request = self.request
        import shutil
        for pagename in pagelist:
            pagename = pagename.strip()
            page = Page(request, pagename)
            try:
                underlay, path = page.getPageBasePath(-1)
                shutil.rmtree(path)
            except:
                pass

    def packageCompoundInstaller(self, bundledict, filename):
        """ Creates a package which installs all other packages. """
        try:
            os.remove(filename)
        except OSError:
            pass
        zf = zipfile.ZipFile(filename, "w", COMPRESSION_LEVEL)

        script = [packLine(['MoinMoinPackage', '1']), ]

        script += [packLine(["InstallPackage", "SystemPagesSetup", name + ".zip"])
                   for name in bundledict if name not in (NODIST, EXTRA, ALL, u"English")]
        script += [packLine(['Print', 'Installed all MoinMaster page bundles.'])]

        zf.writestr(MOIN_PACKAGE_FILE, u"\n".join(script).encode("utf-8"))
        zf.close()

    def mainloop(self):
        # self.options.wiki_url = 'localhost/'
        if self.options.wiki_url and '.' in self.options.wiki_url:
            print "NEVER EVER RUN THIS ON A REAL WIKI!!! This must be run on a local testwiki."
            return

        self.init_request() # this request will work on a test wiki in tests/wiki/ directory
                            # we assume that there are current moinmaster pages there
        request = self.request
        request.form = request.args = request.setup_args()

        if not ('tests/wiki' in request.cfg.data_dir.replace("\\", "/") and 'tests/wiki' in request.cfg.data_underlay_dir.replace("\\", "/")):
            import sys
            print sys.path
            print "NEVER EVER RUN THIS ON A REAL WIKI!!! This must be run on a local testwiki."
            return

        self.gd = wikidicts.GroupDict(request)
        self.gd.reset()

        print "Building page sets ..."
        pageSets = self.buildPageSets()

        print "Creating packages ..."
        generate_filename = lambda name: os.path.join('tests', 'wiki', 'underlay', 'pages', 'SystemPagesSetup', 'attachments', '%s.zip' % name)

        self.packageCompoundInstaller(pageSets, generate_filename(ALL))

        [self.packagePages(list(pages), generate_filename(name), "ReplaceUnderlay")
            for name, pages in pageSets.items() if not name in (u'English', ALL, NODIST)]

        [self.removePages(list(pages))
            for name, pages in pageSets.items() if not name in (u'English', ALL)]

        print "Finished."

