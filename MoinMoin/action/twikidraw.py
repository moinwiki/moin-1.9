# -*- coding: iso-8859-2 -*-
"""
    MoinMoin - twikidraw

    This action is used to call twikidraw

    @copyright: 2001 by Ken Sugino (sugino@mediaone.net),
                2001-2004 by Juergen Hermann <jh@web.de>,
                2005 MoinMoin:AlexanderSchremmer,
                2005 DiegoOngaro at ETSZONE (diego@etszone.com),
                2007-2008 MoinMoin:ThomasWaldmann,
                2005-2009 MoinMoin:ReimarBauer,
    @license: GNU GPL, see COPYING for details.
"""
import os, re, time

from MoinMoin import log
logging = log.getLogger(__name__)

from MoinMoin import wikiutil
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

def attachment_drawing(self, url, text, **kw):
    # This is called for displaying a clickable drawing image by text_html formatter.
    # XXX text arg is unused!
    _ = self.request.getText
    pagename, drawing = AttachFile.absoluteName(url, self.page.page_name)
    containername = wikiutil.taintfilename(drawing) + ".tdraw"

    drawing_url = AttachFile.getAttachUrl(pagename, containername, self.request, drawing=drawing, upload=True)
    ci = AttachFile.ContainerItem(self.request, pagename, containername)
    if not ci.exists():
        title = _('Create new drawing "%(filename)s (opens in new window)"') % {'filename': drawing}
        img = self.icon('attachimg')  # TODO: we need a new "drawimg" in similar grey style and size
        css = 'nonexistent'
        return self.url(1, drawing_url, css=css, title=title) + img + self.url(0)

    title = _('Edit drawing %(filename)s (opens in new window)') % {'filename': self.text(drawing)}
    kw['src'] = src = ci.member_url(drawing + u'.png')
    kw['css'] = 'drawing'

    try:
        mapfile = ci.get(drawing + u'.map')
        map = mapfile.read()
        mapfile.close()
    except (KeyError, IOError, OSError):
        map = ''
    if map:
        # we have a image map. inline it and add a map ref to the img tag
        mapid = 'ImageMapOf' + drawing
        map = map.replace('%MAPNAME%', mapid)
        # add alt and title tags to areas
        map = re.sub(r'href\s*=\s*"((?!%TWIKIDRAW%).+?)"', r'href="\1" alt="\1" title="\1"', map)
        map = map.replace('%TWIKIDRAW%"', '%s" alt="%s" title="%s"' % (drawing_url, title, title))
        # unxml, because 4.01 concrete will not validate />
        map = map.replace('/>', '>')
        title = _('Clickable drawing: %(filename)s') % {'filename': self.text(drawing)}
        if 'title' not in kw:
            kw['title'] = title
        if 'alt' not in kw:
            kw['alt'] = kw['title']
        kw['usemap'] = '#'+mapid
        return map + self.image(**kw)
    else:
        if 'title' not in kw:
            kw['title'] = title
        if 'alt' not in kw:
            kw['alt'] = kw['title']
        return self.url(1, drawing_url) + self.image(**kw) + self.url(0)


class TwikiDraw(object):
    """ twikidraw action """
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
        #return _("Thank you for your changes. Your attention to detail is appreciated.")


    def render(self):
        _ = self._
        request = self.request
        pagename = self.pagename
        target = self.target
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


def execute(pagename, request):
    _ = request.getText
    msg = None
    if not request.user.may.read(pagename):
        msg = '<p>%s</p>' % _('You are not allowed to view this page.')
        TwikiDraw(request, pagename, target).render_msg(msg, 'error')
        return

    target = request.values.get('target', '')
    if not target:
        msg = '<p>%s</p>' % _("Empty target given.")
        TwikiDraw(request, pagename, target).render_msg(msg, 'error')
        return

    do = request.values.get('do', '')
    if do == 'save' and request.user.may.write(pagename):
        msg = TwikiDraw(request, pagename, target).save()
        TwikiDraw(request, pagename, target).render_msg(msg, 'error')
        return

    TwikiDraw(request, pagename, target).render()


