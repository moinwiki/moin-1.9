# -*- coding: iso-8859-2 -*-
"""
    MoinMoin - anywikidraw

    This action is used to call anywikidraw (http://sourceforge.net/projects/anywikidraw/)

    @copyright: 2001 by Ken Sugino (sugino@mediaone.net),
                2001-2004 by Juergen Hermann <jh@web.de>,
                2005 MoinMoin:AlexanderSchremmer,
                2005 DiegoOngaro at ETSZONE (diego@etszone.com),
                2007-2008 MoinMoin:ThomasWaldmann,
                2005-2009 MoinMoin:ReimarBauer
    @license: GNU GPL, see COPYING for details.
"""
import os, re

from MoinMoin import log
logging = log.getLogger(__name__)

from MoinMoin import config, wikiutil
from MoinMoin.action import AttachFile, do_show
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

def gedit_drawing(self, url, text, **kw):
    # This is called for displaying a drawing image by gui editor.
    _ = self.request.getText
    # TODO: this 'text' argument is kind of superfluous, replace by using alt=... kw arg
    # ToDo: make this clickable for the gui editor
    if 'alt' not in kw or not kw['alt']:
        kw['alt'] = text
    # we force the title here, needed later for html>wiki converter
    kw['title'] = "drawing:%s" % wikiutil.quoteWikinameURL(url)
    pagename, drawing = AttachFile.absoluteName(url, self.page.page_name)
    containername = wikiutil.taintfilename(drawing) + ".adraw"
    drawing_url = AttachFile.getAttachUrl(pagename, containername, self.request, drawing=drawing, upload=True)
    ci = AttachFile.ContainerItem(self.request, pagename, containername)
    if not ci.exists():
        title = _('Create new drawing "%(filename)s (opens in new window)"') % {'filename': drawing}
        img = self.icon('attachimg')  # TODO: we need a new "drawimg" in similar grey style and size
        css = 'nonexistent'
        return self.url(1, drawing_url, css=css, title=title) + img + self.url(0)
    kw['src'] = ci.member_url('drawing.png')
    return self.image(**kw)

def attachment_drawing(self, url, text, **kw):
    # This is called for displaying a clickable drawing image by text_html formatter.
    # XXX text arg is unused!
    _ = self.request.getText
    pagename, drawing = AttachFile.absoluteName(url, self.page.page_name)
    containername = wikiutil.taintfilename(drawing) + ".adraw"

    drawing_url = AttachFile.getAttachUrl(pagename, containername, self.request, drawing=drawing, upload=True)
    ci = AttachFile.ContainerItem(self.request, pagename, containername)
    if not ci.exists():
        title = _('Create new drawing "%(filename)s (opens in new window)"') % {'filename': drawing}
        img = self.icon('attachimg')  # TODO: we need a new "drawimg" in similar grey style and size
        css = 'nonexistent'
        return self.url(1, drawing_url, css=css, title=title) + img + self.url(0)

    title = _('Edit drawing %(filename)s (opens in new window)') % {'filename': self.text(drawing)}
    kw['src'] = src = ci.member_url('drawing.png')
    kw['css'] = 'drawing'

    try:
        mapfile = ci.get('drawing.map')
        map = mapfile.read()
        mapfile.close()
    except (KeyError, IOError, OSError):
        map = ''
    if map:
        # XXX check how that is done by josef
        # we have a image map. inline it and add a map ref to the img tag
        mapid = 'ImageMapOf' + drawing
        map = map.replace('id="%s.svg"' % drawing, '')
        map = map.replace('name="%s.svg"' % drawing, 'name="%s"' % mapid)
        # add alt and title tags to areas
        #map = re.sub(r'href\s*=\s*"((?!%TWIKIDRAW%).+?)"', r'href="\1" alt="\1" title="\1"', map)
        #map = map.replace('%TWIKIDRAW%"', '%s" alt="%s" title="%s"' % (drawing_url, title, title))
        # unxml, because 4.01 concrete will not validate />
        map = map.replace('/>', '>')
        title = _('Clickable drawing: %(filename)s') % {'filename': self.text(drawing)}
        if 'title' not in kw:
            kw['title'] = title
        if 'alt' not in kw:
            kw['alt'] = kw['title']
        kw['usemap'] = '#'+mapid
        return self.url(1, drawing_url) + map + self.image(**kw) + self.url(0)
    else:
        if 'title' not in kw:
            kw['title'] = title
        if 'alt' not in kw:
            kw['alt'] = kw['title']
        return self.url(1, drawing_url) + self.image(**kw) + self.url(0)

class AnyWikiDraw(object):
    """ anywikidraw action """
    def __init__(self, request, pagename, target):
        self._ = request.getText
        self.request = request
        self.pagename = pagename
        self.target = target

    def render_msg(self, msg, msgtype):
        """ Called to display some message (can also be the action form) """
        self.request.theme.add_msg(msg, msgtype)
        do_show(self.pagename, self.request)

    def save(self):
        _ = self._
        pagename = self.pagename
        request = self.request
        target = self.target
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

        ci = AttachFile.ContainerItem(request, pagename, target + '.adraw')
        filecontent = file_upload.stream
        content_length = None
        if ext == '.svg': # TWikiDraw POSTs this first
            AttachFile._addLogEntry(request, 'ATTDRW', pagename, target + '.adraw')
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

        if filecontent:
            ci.put('drawing' + ext, filecontent, content_length)

    def render(self):
        _ = self._
        request = self.request
        pagename = self.pagename
        target = self.target
        url = request.getQualifiedURL()
        target_url = ''
        drawing_name = ''

        htdocs = "%s%s" % (request.cfg.url_prefix_static, '/applets/anywikidraw')
        ci = AttachFile.ContainerItem(request, pagename, target + '.adraw')
        if ci.exists():
            drawing_name = "%s.svg" % target
            target_url = ci.member_url('drawing.svg')

        html = """
    <h2> %(editdrawing)s </h2>
<!--
    Document   : anywikidraw_for_twiki_demo
    Created on : May 13, 2008, 7:32:27 AM
    Author     : werni
    Version    : $Id: anywikidraw_for_twiki_demo.html 107 2009-06-15 19:33:05Z rawcoder $

    adjusted for MoinMoin 2009-08-29 ReimarBauer
-->
        <applet codebase="."
                archive="%(htdocs)s/lib/AnyWikiDrawForTWiki.jar"
                code=org.anywikidraw.twiki.TWikiDrawingApplet.class
                width="800" height="600">

           <!-- The following parameters are used to tell AnyWikiDraw how to communicate with MoinMoin.
           -->
           <param name="DrawingName" value="%(target)s.svg"/>
           <param name="DrawingWidth" value="800"/>
           <param name="DrawingHeight" value="600"/>
           <param name="DrawingURL" value="%(target_url)s"/>
           <param name="PageURL" value="%(url)s/%(pagename)s">
           <param name="UploadURL" value="%(pagename)s?action=anywikidraw&do=save&target=%(target)s"/>

           <!-- The following parameters are used to configure the drawing applet -->
           <param name="Locale" value="en"/>

           <!-- The following parameters are used to configure Sun's Java Plug-In -->
           <param name="codebase_lookup" value="false"/>
           <param name="classloader_cache" value="false"/>
           <param name="java_arguments" value="-Djnlp.packEnabled=true"/>
           <param name="image" value="lib/Splash.gif"/>
           <param name="boxborder" value="false"/>
           <param name="centerimage" value="true"/>
        </applet>
""" % {'htdocs': htdocs,
       'pagename': pagename,
       'target': target,
       'drawing_name': drawing_name,
       'target_url': target_url,
       'url': url,
       'editdrawing': _('Edit drawing'),
       }

        title = '%s:%s' % (pagename, target)
        request.theme.send_title(title, page=request.page, pagename=pagename)
        request.write(request.formatter.startContent("content"))
        request.write(request.formatter.rawHTML(html))
        request.write(request.formatter.endContent())
        request.theme.send_footer(pagename)
        request.theme.send_closing_html()

def execute(pagename, request):
    _ = request.getText
    msg = None
    if not request.user.may.read(pagename):
        msg = '<p>%s</p>' % _('You are not allowed to view this page.')
        AnyWikiDraw(request, pagename, target).render_msg(msg, 'error')
        return

    target = request.values.get('target', '')
    if not target:
        msg = '<p>%s</p>' % _("Empty target given.")
        AnyWikiDraw(request, pagename, target).render_msg(msg, 'error')
        return

    do = request.values.get('do', '')
    if do == 'save' and request.user.may.write(pagename):
        msg = AnyWikiDraw(request, pagename, target).save()
        AnyWikiDraw(request, pagename, target).render_msg(msg, 'error')
        return

    AnyWikiDraw(request, pagename, target).render()

