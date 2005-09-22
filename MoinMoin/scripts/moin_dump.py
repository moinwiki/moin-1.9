#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
MoinMoin - Dump a MoinMoin wiki to static pages

You must run this script as owner of the wiki files, usually this is the
web server user.

@copyright: 2002-2004 by Jürgen Hermann <jh@web.de>
@license: GNU GPL, see COPYING for details.
"""

__version__ = "20050725"

import os, time, StringIO, codecs, shutil, errno

# Insert the path to MoinMoin in the start of the path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(sys.argv[0]), 
                                os.pardir, os.pardir))

from MoinMoin import config, wikiutil, Page
from MoinMoin.scripts import _util
from MoinMoin.request import RequestCLI

logo_html = '<img src="moinmoin.png">'

url_prefix = "."
HTML_SUFFIX = ".html"

page_template = u'''<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
<head>
<meta http-equiv="content-type" content="text/html; charset=%(charset)s">
<title>%(pagename)s</title>
<link rel="stylesheet" type="text/css" media="all" charset="utf-8" href="%(theme)s/css/common.css">
<link rel="stylesheet" type="text/css" media="screen" charset="utf-8" href="%(theme)s/css/screen.css">
<link rel="stylesheet" type="text/css" media="print" charset="utf-8" href="%(theme)s/css/print.css">
</head>
<body>
<table>
<tr>
<td>
%(logo_html)s
</td>
<td>
%(navibar_html)s
</td>
</tr>
</table>
<hr>
%(pagehtml)s
<hr>
%(timestamp)s
</body>
</html>
'''


class MoinDump(_util.Script):
    
    def __init__(self):
        _util.Script.__init__(self, __name__, "[options] <target-directory>")
        self.parser.add_option(
            "--config-dir", metavar="DIR", dest="config_dir",
            help=("Path to the directory containing the wiki "
                  "configuration files. [default: current directory]")
        )
        self.parser.add_option(
            "--wiki-url", metavar="WIKIURL", dest="wiki_url",
            help="URL of wiki e.g. localhost/mywiki/ [default: CLI]"
        )
        self.parser.add_option(
            "--page", metavar="NAME", dest="page",
            help="Dump a single page (with possibly broken links)"
        )

    def mainloop(self):
        """ moin-dump's main code. """

        if len(sys.argv) == 1:
            self.parser.print_help()
            sys.exit(1)

        # Prepare output directory
        outputdir = self.args[0]
        outputdir = os.path.abspath(outputdir)
        try:
            os.mkdir(outputdir)
            _util.log("Created output directory '%s'!" % outputdir)
        except OSError, err:
            if err.errno != errno.EEXIST:
                _util.fatal("Cannot create output directory '%s'!" % outputdir)

        # Insert config dir or the current directory to the start of the
        # path.
        config_dir = self.options.config_dir
        if config_dir and os.path.isfile(config_dir):
            config_dir = os.path.dirname(config_dir)
        if config_dir and not os.path.isdir(config_dir):
            _util.fatal("bad path given to --config-dir option")
        sys.path.insert(0, os.path.abspath(config_dir or os.curdir))

        # Create request 
        if self.options.wiki_url:
            request = RequestCLI(self.options.wiki_url)
        else:
            request = RequestCLI()

        # fix url_prefix so we get relative paths in output html
        request.cfg.url_prefix = url_prefix

        if self.options.page:
            pages = [self.options.page]
        else:
            # Get all existing pages in the wiki
            pages = request.rootpage.getPageList(user='')
            pages.sort()

        wikiutil.quoteWikinameURL = lambda pagename, qfn=wikiutil.quoteWikinameFS: (qfn(pagename) + HTML_SUFFIX)

        errfile = os.path.join(outputdir, 'error.log')
        errlog = open(errfile, 'w')
        errcnt = 0

        page_front_page = wikiutil.getSysPage(request, 'FrontPage').page_name
        page_title_index = wikiutil.getSysPage(request, 'TitleIndex').page_name
        page_word_index = wikiutil.getSysPage(request, 'WordIndex').page_name
        
        navibar_html = ''
        for p in [page_front_page, page_title_index, page_word_index]:
            navibar_html += '&nbsp;[<a href="%s">%s</a>]' % (wikiutil.quoteWikinameFS(p), wikiutil.escape(p))

        for pagename in pages:
            # we have the same name in URL and FS
            file = wikiutil.quoteWikinameURL(pagename) 
            _util.log('Writing "%s"...' % file)
            try:
                pagehtml = ''
                page = Page.Page(request, pagename)
                request.page = page
                try:
                    request.reset()
                    out = StringIO.StringIO()
                    request.redirect(out)
                    page.send_page(request, count_hit=0, content_only=1)
                    pagehtml = out.getvalue()
                    request.redirect()
                except:
                    errcnt = errcnt + 1
                    print >>sys.stderr, "*** Caught exception while writing page!"
                    print >>errlog, "~" * 78
                    print >>errlog, file # page filename
                    import traceback
                    traceback.print_exc(None, errlog)
            finally:
                timestamp = time.strftime("%Y-%m-%d %H:%M")
                filepath = os.path.join(outputdir, file)
                fileout = codecs.open(filepath, 'w', config.charset)
                fileout.write(page_template % {
                    'charset': config.charset,
                    'pagename': pagename,
                    'pagehtml': pagehtml,
                    'logo_html': logo_html,
                    'navibar_html': navibar_html,
                    'timestamp': timestamp,
                    'theme': request.cfg.theme_default,
                })
                fileout.close()

        # copy FrontPage to "index.html"
        indexpage = page_front_page
        if self.options.page:
            indexpage = self.options.page
        shutil.copyfile(
            os.path.join(outputdir, wikiutil.quoteWikinameFS(indexpage) + HTML_SUFFIX),
            os.path.join(outputdir, 'index' + HTML_SUFFIX)
        )

        errlog.close()
        if errcnt:
            print >>sys.stderr, "*** %d error(s) occurred, see '%s'!" % (errcnt, errfile)


def run():
    MoinDump().run()


if __name__ == "__main__":
    run()

