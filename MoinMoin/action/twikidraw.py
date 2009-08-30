# -*- coding: iso-8859-2 -*-
"""
    MoinMoin - twikidraw

    This action is used to call twikidraw

    it is just a thin wrapper around it.

    @copyright: 2001 by Ken Sugino (sugino@mediaone.net),
                2001-2004 by Juergen Hermann <jh@web.de>,
                2005 MoinMoin:AlexanderSchremmer,
                2005 DiegoOngaro at ETSZONE (diego@etszone.com),
                2007-2008 MoinMoin:ThomasWaldmann,
                2005-2009 MoinMoin:ReimarBauer,
    @license: GNU GPL, see COPYING for details.
"""
import os, time

from MoinMoin import log
logging = log.getLogger(__name__)

from MoinMoin import wikiutil
from MoinMoin.action import AttachFile
from MoinMoin.Page import Page

action_name = __name__.split('.')[-1]

def _write_stream(content, stream, bufsize=8192):
    if hasattr(content, 'read'): # looks file-like
        import shutil
        shutil.copyfileobj(content, stream, bufsize)
    elif isinstance(content, str):
        stream.write(content)
    else:
        logging.error("unsupported content object: %r" % content)
        raise

def execute(pagename, request):
    _ = request.getText
    if not request.user.may.read(pagename):
        request.write('<p>%s</p>' % _('You are not allowed to view this page.'))
        return
    target = request.values.get('target', '')
    if not target:
        request.write('<p>%s</p>' % _("Empty target given."))
        return
   
    do = request.values.get('do', '')
    if do == 'save':
        if not request.user.may.write(pagename):
            return _('You are not allowed to save a drawing on this page.')
        file_upload = request.files.get('filepath')
        if not file_upload:
            # This might happen when trying to upload file names
            # with non-ascii characters on Safari.
            return _("No file content. Delete non ASCII characters from the file name and try again.")

        filename = request.form['filename']
        basepath, basename = os.path.split(filename)
        basename, ext = os.path.splitext(basename)
        ci = AttachFile.ContainerItem(request, pagename, basename + '.tdraw')
        filecontent = file_upload.stream
        content_length = None
        if ext == '.draw': # TWikiDraw POSTs this first
            AttachFile._addLogEntry(request, 'ATTDRW', pagename, basename + '.tdraw')
            ci.truncate()
            filecontent = filecontent.read() # read file completely into memory
            filecontent = filecontent.replace("\r", "")
        elif ext == '.map':
            # touch attachment directory to invalidate cache if new map is saved
            attach_dir = AttachFile.getAttachDir(request, pagename)
            os.utime(attach_dir, None)
            filecontent = filecontent.read() # read file completely into memory
            filecontent = filecontent.strip()
        else:
            #content_length = file_upload.content_length
            # XXX gives -1 for wsgiref :( If this is fixed, we could use the file obj,
            # without reading it into memory completely:
            filecontent = filecontent.read()

        ci.put(basename + ext, filecontent, content_length)
        return None, None

    url = request.getQualifiedURL()
    now = time.time()
    htdocs = "%s%s" % (request.cfg.url_prefix_static, "/applets/TWikiDrawPlugin")
    ci = AttachFile.ContainerItem(request, pagename, target + '.tdraw')
    drawpath = ci.member_url(target + '.draw')
    pngpath = ci.member_url(target + '.png')
    pagelink = request.href(pagename, action=action_name, ts=now)
    helplink = Page(request, "HelpOnActions/AttachFile").url(request)
    savelink = request.href(pagename, action=action_name, do='save', target=target)
    timestamp = '&amp;ts=%s' % now

    html = '''<h2> %(editdrawing)s </h2>
<p>
<img src="%(pngpath)s%(timestamp)s">
<applet code="CH.ifa.draw.twiki.TWikiDraw.class"
        archive="%(htdocs)s/twikidraw.jar" width="640" height="480">
<param name="drawpath" value="%(drawpath)s">
<param name="pngpath"  value="%(pngpath)s">
<param name="savepath" value="%(savelink)s">
<param name="basename" value="%(basename)s">
<param name="viewpath" value="%(url)s/%(pagename)s/">
<param name="helppath" value="%(helplink)s">
<strong>NOTE:</strong> You need a Java enabled browser to edit the drawing example.
</applet>
</p>''' % {
    'pagename': pagename,
    'url': url,
    'target': target,
    'pngpath': pngpath,
    'timestamp': timestamp,
    'htdocs': htdocs,
    'drawpath': drawpath,
    'pagelink': pagelink,
    'helplink': helplink,
    'savelink': savelink,
    'basename': wikiutil.escape(target, 1),
    'editdrawing': _("Edit drawing")
    }

    title = "%s:%s" % (pagename, target)
    request.theme.send_title(title, page=request.page, pagename=pagename)
    request.write(request.formatter.startContent("content"))
    request.write(request.formatter.rawHTML(html))
    request.write(request.formatter.endContent())
    request.theme.send_footer(pagename)
    request.theme.send_closing_html()

