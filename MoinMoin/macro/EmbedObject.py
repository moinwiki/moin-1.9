# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - EmbedObject Macro

    This macro is used to embed an object into a wiki page. Optionally, the
    size of the object can get adjusted. Further keywords are dependent on
    the kind of application.

    <<EmbedObject(attachment[,width=width][,height=height][,alt=Embedded mimetpye/xy])>>

    @copyright: 2006-2007 MoinMoin:ReimarBauer,
                2006 TomSi,
                2007 OliverSiemoneit

    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import wikiutil
from MoinMoin.action import AttachFile

class EmbedObject:

    def __init__(self, macro, args):
        self._ = macro.request.getText
        self.macro = macro
        self.request = macro.request
        self.formatter = macro.formatter
        self.args = args
        self.width = ""
        self.height = ""
        self.alt = ""
        self.play = "false"
        self.stop = "true"
        self.loop = "false"
        self.quality = "high"
        self.op = "true"
        self.repeat = "false"
        self.autostart = "false"
        self.align = "center"
        self.hidden = "false"
        self.menu = "true"
        self.wmode = "transparent"
        self.target = None
        self.align = "middle"
        self.guess_filename = 'Probably.swf'

        if args:
            args = args.split(',')
            args = [arg.strip() for arg in args]
        else:
            args = []

        kw_count = 0
        argc = len(args)
        if args:
            for arg in self.args.split(','):
                if '=' in arg:
                    kw_count += 1
                    key, value = arg.split('=')
                    setattr(self, key, wikiutil.escape(value.strip(), quote=1))
                    argc -= kw_count
            self.target = args[0]

    def _is_URL(self, text):
        """ Answer true if text is an URL.
            The method used here is pretty dumb. Improvements are welcome.
        """
        return '://' in text

    def embed(self, mt, url):
        _ = self._

        if not mt:
            return _("Not supported mimetype of file: %s") % self.target

        mime_type = "%s/%s" % (mt.major, mt.minor, )
        dangerous = mime_type in self.request.cfg.mimetypes_xss_protect

        if not mime_type in self.request.cfg.mimetypes_embed or dangerous:
            kw = {'src': url}
            return "%s: %s%s%s" % (self.macro.formatter.text(_('Embedding of object by choosen formatter not possible')),
                               self.macro.formatter.url(1, kw['src']),
                               self.macro.formatter.text(self.target),
                               self.macro.formatter.url(0))

        if self.alt is "":
            self.alt = "%(text)s %(mime_type)s" % {
                           'text': _("Embedded"),
                           'mime_type': mime_type,
                        }

        if mt.major == 'video':
            return '''
<object data="%(url)s" type="%(type)s" width="%(width)s" height="%(height)s" align="%(align)s" standby="%(alt)s" stop="%(stop)s">
<param name="wmode" value="%(wmode)s" valuetype="data">
<param name="movie" value="%(url)s" valuetype="data">
<param name="play" value="%(play)s" valuetype="data">
<param name="stop" value="%(stop)s" valuetype="data">
<param name="repeat" value="%(repeat)s" valuetype="data">
<param name="autostart" value="%(autostart)s" valuetype="data">
<param name="op" value="%(op)s" valuetype="data">
<param name="menu" value="%(menu)s" valuetype="data">
%(alt)s
</object>''' % {
    "width": self.width,
    "height": self.height,
    "url": url,
    "play": self.play,
    "stop": self.stop,
    "align": self.align,
    "repeat": self.repeat,
    "autostart": self.autostart,
    "op": self.op,
    "type": mime_type,
    "menu": self.menu,
    "wmode": self.wmode,
    "alt": self.alt,
}

        if mt.major in ['image', 'chemical', 'x-world']:
            return '''
<object data="%(url)s" width="%(width)s" height="%(height)s" type="%(type)s"  align="%(align)s">
<param name="%(major)s" value="%(url)s">
<p>%(alt)s</p>
</object>''' % {
    "width": self.width,
    "height": self.height,
    "url": url,
    "align": self.align,
    "type": mime_type,
    "major": mt.major,
    "alt": self.alt,
}

        if mt.major == 'audio':
            return '''
<object data="%(url)s" width="%(width)s" height="%(height)s" type="%(type)s"  align="%(align)s">
<param name="audio" value="%(url)s">
<param name="repeat" value="%(repeat)s">
<param name="autostart" value="%(autostart)s">
<param name="op" value="%(op)s">
<param name="play" value="%(play)s">
<param name="stop" value="%(stop)s" valuetype="data">
<param name="hidden" value="%(hidden)s">
<p>%(alt)s</p>
</OBJECT>''' % {
    "width": self.width or "60",
    "height": self.height or "20",
    "url": url,
    "align": self.align,
    "play": self.play,
    "stop": self.stop,
    "repeat": self.repeat,
    "autostart": self.autostart,
    "op": self.op,
    "hidden": self.hidden,
    "type": mime_type,
    "alt": self.alt,
}

        if mt.major == 'application':
            return '''
<object data="%(url)s" width="%(width)s" height="%(height)s" type="%(type)s"  align="%(align)s">
<param name="wmode" value="%(wmode)s" valuetype="data">
<param name="autostart" value="%(autostart)s">
<param name="play" value="%(play)s">
<param name="loop" value="%(loop)s">
<param name="menu" value="%(menu)s">
<p>%(alt)s</p>
</object>''' % {
    "width": self.width,
    "height": self.height,
    "url": url,
    "align": self.align,
    "autostart": self.autostart,
    "play": self.play,
    "loop": self.loop,
    "type": mime_type,
    "menu": self.menu,
    "wmode": self.wmode,
    "alt": self.alt,
}

    def render(self):
        _ = self._

        if not self.target:
            msg = _('Not enough arguments to EmbedObject macro! Try [[EmbedObject(attachment [,width=width] [,height=height] [,alt=Embedded mimetpye/xy])]]', formatted=False)
            return "%s%s%s" % (self.formatter.sysmsg(1), self.formatter.text(msg), self.formatter.sysmsg(0))

        if not self._is_URL(self.target):
            pagename, fname = AttachFile.absoluteName(self.target, self.formatter.page.page_name)

            if not AttachFile.exists(self.request, pagename, fname):
                linktext = _('Upload new attachment "%(filename)s"')
                return wikiutil.link_tag(self.request, ('%s?action=AttachFile&rename=%s' % (
                                                         wikiutil.quoteWikinameURL(pagename),
                                                         wikiutil.url_quote_plus(fname))),
                                                         linktext % {'filename': fname})

            url = AttachFile.getAttachUrl(pagename, fname, self.request)

            mt = wikiutil.MimeType(filename=fname)
            mimestr = "%s/%s" % (mt.major, mt.minor, )
        else:
            mt = wikiutil.MimeType(filename=self.guess_filename)
            url = wikiutil.escape(self.target)

        # XXX Should better use formatter.embed if available?
        return self.macro.formatter.rawHTML(self.embed(mt, url))

def execute(macro, args):
    return EmbedObject(macro, args).render()

