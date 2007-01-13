# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Dump a MoinMoin wiki to static pages

    You must run this script as owner of the wiki files, usually this is the
    web server user.

    @copyright: 2002-2004 by Jürgen Hermann <jh@web.de>,
                2005-2006 by MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.

"""

import sys, os, time, StringIO, codecs, shutil, re, errno

from MoinMoin import config, wikiutil, Page
from MoinMoin import script
from MoinMoin.action import AttachFile

url_prefix_static = "."
logo_html = '<img src="logo.png">'
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
    filename = filename.encode(config.charset)
    source_dir = AttachFile.getAttachDir(request, pagename)
    source_file = os.path.join(source_dir, filename)
    dest_dir = os.path.join(outputdir, "attachments", wikiutil.quoteWikinameFS(pagename))
    dest_file = os.path.join(dest_dir, filename)
    dest_url = "attachments/%s/%s" % (wikiutil.quoteWikinameFS(pagename), wikiutil.url_quote(filename))
    if os.access(source_file, os.R_OK):
        if not os.access(dest_dir, os.F_OK):
            try:
                os.makedirs(dest_dir)
            except:
                script.fatal("Cannot create attachment directory '%s'" % dest_dir)
        elif not os.path.isdir(dest_dir):
            script.fatal("'%s' is not a directory" % dest_dir)

        shutil.copyfile(source_file, dest_file)
        script.log('Writing "%s"...' % dest_url)
        return dest_url
    else:
        return ""


class PluginScript(script.MoinScript):
    """ Dump script class """

    def __init__(self, argv=None, def_values=None):
        script.MoinScript.__init__(self, argv, def_values)
        self.parser.add_option(
            "-t", "--target-dir", dest="target_dir",
            help="Write html dump to DIRECTORY"
        )

    def mainloop(self):
        """ moin-dump's main code. """

        # Prepare output directory
        if not self.options.target_dir:
            _util.fatal("you must use --target-dir=/your/output/path to specify the directory we write the html files to")
        outputdir = os.path.abspath(self.options.target_dir)
        try:
            os.mkdir(outputdir)
            script.log("Created output directory '%s'!" % outputdir)
        except OSError, err:
            if err.errno != errno.EEXIST:
                script.fatal("Cannot create output directory '%s'!" % outputdir)

        # Insert config dir or the current directory to the start of the path.
        config_dir = self.options.config_dir
        if config_dir and os.path.isfile(config_dir):
            config_dir = os.path.dirname(config_dir)
        if config_dir and not os.path.isdir(config_dir):
            script.fatal("bad path given to --config-dir option")
        sys.path.insert(0, os.path.abspath(config_dir or os.curdir))

        self.init_request()
        request = self.request

        # fix url_prefix_static so we get relative paths in output html
        request.cfg.url_prefix_static = url_prefix_static

        pages = request.rootpage.getPageList(user='') # get list of all pages in wiki
        pages.sort()
        if self.options.page: # did user request a particular page or group of pages?
            try:
                namematch = re.compile(self.options.page)
                pages = [page for page in pages if namematch.match(page)]
                if not pages:
                    pages = [self.options.page]
            except:
                pages = [self.options.page]

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

        urlbase = request.url # save wiki base url
        for pagename in pages:
            # we have the same name in URL and FS
            file = wikiutil.quoteWikinameURL(pagename)
            script.log('Writing "%s"...' % file)
            try:
                pagehtml = ''
                request.url = urlbase + pagename # add current pagename to url base 
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
            indexpage = pages[0] # index page has limited use when dumping specific pages, but create one anyway
        shutil.copyfile(
            os.path.join(outputdir, wikiutil.quoteWikinameFS(indexpage) + HTML_SUFFIX),
            os.path.join(outputdir, 'index' + HTML_SUFFIX)
        )

        errlog.close()
        if errcnt:
            print >>sys.stderr, "*** %d error(s) occurred, see '%s'!" % (errcnt, errfile)

