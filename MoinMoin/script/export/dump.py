# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Dump a MoinMoin wiki to static pages

    You must run this script as owner of the wiki files, usually this is the
    web server user.

    @copyright: 2002-2004 by Jürgen Hermann <jh@web.de>,
                2005-2006 by Thomas Waldmann
    @license: GNU GPL, see COPYING for details.

"""

import sys, os, time, StringIO, codecs, shutil, re, errno

from MoinMoin import config, wikiutil, Page
from MoinMoin.script import _util
from MoinMoin.script._util import MoinScript
from MoinMoin.action import AttachFile

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
<div id="page">
<h1 id="title">%(pagename)s</h1>
%(pagehtml)s
</div>
<hr>
%(timestamp)s
</body>
</html>
'''

def _attachment(request, pagename, filename, outputdir):
    source_dir = AttachFile.getAttachDir(request, pagename)
    source_file = os.path.join(source_dir, filename)
    dest_dir = os.path.join(outputdir, "attachments", wikiutil.quoteWikinameFS(pagename))
    dest_file = os.path.join(dest_dir, filename)
    dest_url = "attachments/%s/%s" % (wikiutil.quoteWikinameFS(pagename), filename)
    if os.access(source_file, os.R_OK):
        if not os.access(dest_dir, os.F_OK):
            try:
                os.makedirs(dest_dir)
            except:
                _util.fatal("Cannot create attachment directory '%s'" % dest_dir)
        elif not os.path.isdir(dest_dir):
            _util.fatal("'%s' is not a directory" % dest_dir)

        shutil.copyfile(source_file, dest_file)
        _util.log('Writing "%s"...' % dest_url)
        return dest_url
    else:
        return ""
  

class PluginScript(MoinScript):
    """ Dump script class """
    
    def __init__(self, argv=None, def_values=None):
        MoinScript.__init__(self, argv, def_values)
        self.parser.add_option(
            "-t", "--target-dir", dest="target_dir",
            help="Write html dump to DIRECTORY"
        )

    def mainloop(self):
        """ moin-dump's main code. """

        # Prepare output directory
        outputdir = os.path.abspath(self.options.target_dir)
        try:
            os.mkdir(outputdir)
            _util.log("Created output directory '%s'!" % outputdir)
        except OSError, err:
            if err.errno != errno.EEXIST:
                _util.fatal("Cannot create output directory '%s'!" % outputdir)

        # Insert config dir or the current directory to the start of the path.
        config_dir = self.options.config_dir
        if config_dir and os.path.isfile(config_dir):
            config_dir = os.path.dirname(config_dir)
        if config_dir and not os.path.isdir(config_dir):
            _util.fatal("bad path given to --config-dir option")
        sys.path.insert(0, os.path.abspath(config_dir or os.curdir))

        self.init_request()
        request = self.request

        # fix url_prefix so we get relative paths in output html
        original_url_prefix = request.cfg.url_prefix
        request.cfg.url_prefix = url_prefix

        if self.options.page:
            pages = [self.options.page]
        else:
            # Get all existing pages in the wiki
            pages = request.rootpage.getPageList(user='')
            pages.sort()

        wikiutil.quoteWikinameURL = lambda pagename, qfn=wikiutil.quoteWikinameFS: (qfn(pagename) + HTML_SUFFIX)

        AttachFile.getAttachUrl = lambda pagename, filename, request, addts=0, escaped=0: (_attachment(request, pagename, filename, outputdir))

        errfile = os.path.join(outputdir, 'error.log')
        errlog = open(errfile, 'w')
        errcnt = 0

        page_front_page = wikiutil.getSysPage(request, request.cfg.page_front_page).page_name
        page_title_index = wikiutil.getSysPage(request, 'TitleIndex').page_name
        page_word_index = wikiutil.getSysPage(request, 'WordIndex').page_name
        
        navibar_html = ''
        for p in [page_front_page, page_title_index, page_word_index]:
            navibar_html += '&nbsp;[<a href="%s">%s</a>]' % (wikiutil.quoteWikinameURL(p), wikiutil.escape(p))

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
                    pagehtml = request.redirectedOutput(page.send_page, request, count_hit=0, content_only=1)
                except:
                    errcnt = errcnt + 1
                    print >>sys.stderr, "*** Caught exception while writing page!"
                    print >>errlog, "~" * 78
                    print >>errlog, file # page filename
                    import traceback
                    traceback.print_exc(None, errlog)
            finally:
                logo_html = re.sub(original_url_prefix + "/?", "", request.cfg.logo_string)
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

