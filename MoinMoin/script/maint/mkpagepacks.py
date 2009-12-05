# -*- coding: iso-8859-1 -*-
"""
MoinMoin - Package Generator

@copyright: 2005 Alexander Schremmer,
            2006-2009 MoinMoin:ThomasWaldmann
@license: GNU GPL, see COPYING for details.
"""

import os
import zipfile
from datetime import datetime

from MoinMoin.support.python_compatibility import set
from MoinMoin import wikiutil
from MoinMoin.action.AttachFile import _get_files
from MoinMoin.Page import Page
from MoinMoin.action import AttachFile
from MoinMoin.packages import packLine, MOIN_PACKAGE_FILE
from MoinMoin.script import MoinScript
from MoinMoin import i18n
from MoinMoin.i18n import strings
i18n.strings = strings


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

        all_pages = set(request.rootpage.getPageList())
        packaged_pages = set()

        languages = i18n.wikiLanguages()
        pageset_names = i18n.strings.pagesets
        pageSets = {}
        for lang in languages:
            def trans(text, request=request, lang=lang, **kw):
                return i18n.getText(text, request, lang, **kw)

            try:
                lang_long = languages[lang]['x-language-in-english']
                lang_long = lang_long.replace('/', '_').replace(' ', '_')
            except KeyError:
                lang_long = lang

            for pageset_name in pageset_names:
                pageset_orig = set(getattr(i18n.strings, pageset_name))
                pageset_trans = set([trans(pn) for pn in pageset_orig])
                key = u"%s_%s" % (lang_long, pageset_name)
                pageset = pageset_trans
                if lang != 'en':
                    pageset -= pageset_orig
                if pageset:
                    print key, len(pageset)
                    pageSets[key] = pageset
                    packaged_pages |= pageset

        not_packaged_pages = all_pages - packaged_pages
        pageSets['00_needs_fixing'] = not_packaged_pages
        return pageSets

    def packagePages(self, pagelist, filename, function):
        """ Puts pages from pagelist into filename and calls function on them on installation. """
        request = self.request
        try:
            os.remove(filename)
        except OSError:
            pass
        # page LanguageSetup needs no packing!
        existing_pages = [pagename for pagename in pagelist if Page(request, pagename).exists() and pagename != 'LanguageSetup']
        if not existing_pages:
            return

        zf = zipfile.ZipFile(filename, "w", COMPRESSION_LEVEL)

        script = [packLine(['MoinMoinPackage', '1']), ]

        cnt = 0
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
            zi = zipfile.ZipInfo(filename=zipname, date_time=datetime.fromtimestamp(timestamp).timetuple()[:6])
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

    def mainloop(self):
        # self.options.wiki_url = 'localhost/'
        if self.options.wiki_url and '.' in self.options.wiki_url:
            print "NEVER EVER RUN THIS ON A REAL WIKI!!! This must be run on a local testwiki."
            return

        self.init_request() # this request will work on a test wiki in tests/wiki/ directory
                            # we assume that there are current moinmaster pages there
        request = self.request

        if not ('tests/wiki' in request.cfg.data_dir.replace("\\", "/") and 'tests/wiki' in request.cfg.data_underlay_dir.replace("\\", "/")):
            import sys
            print sys.path
            print "NEVER EVER RUN THIS ON A REAL WIKI!!! This must be run on a local testwiki."
            return

        print "Building page sets ..."
        pageSets = self.buildPageSets()

        print "Creating packages ..."
        package_path = os.path.join('tests', 'wiki', 'underlay', 'pages', 'LanguageSetup', 'attachments')
        try:
            # create attachment dir in case it is not there:
            os.mkdir(package_path)
        except OSError:
            pass
        generate_filename = lambda name: os.path.join(package_path, '%s.zip' % name)
        [self.packagePages(list(pages), generate_filename(name), "ReplaceUnderlay") for name, pages in pageSets.items()]

        print "Removing pagedirs of packaged pages ..."
        dontkill = set(['LanguageSetup'])
        [self.removePages(list(pages - dontkill)) for name, pages in pageSets.items()]

        print "Finished."

