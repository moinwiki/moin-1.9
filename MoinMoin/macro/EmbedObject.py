# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - EmbedObject Macro

    This macro is used to embed an object into a wiki page. Optionally, the
    size of the object can get adjusted. Further keywords are dependent on
    the kind of application, see HelpOnMacros/EmbedObject

    <<EmbedObject(attachment[,width=width][,height=height][,alt=alternate Text])>>

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
        self.url_mimetype = None

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

    def _check_object_value(self, param, value):
        if value != '':
            return '%(param)s="%(value)s"' % {
                                              "param": param,
                                              "value": value}
        else:
            return ""

    def _check_param_value(self, param, value, valuetype):
        if value != '':
            return '<param name="%(param)s" value="%(value)s" valuetype="%(valuetype)s">' % {
                                                                                             "param": param,
                                                                                             "value": value,
                                                                                             "valuetype": valuetype}
        else:
            return ""

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
            return "%s: %s%s%s" % (self.macro.formatter.text(_('Embedding of object by chosen formatter not possible')),
                               self.macro.formatter.url(1, kw['src']),
                               self.macro.formatter.text(self.target),
                               self.macro.formatter.url(0))

        if self.alt == "":
            self.alt = "%(text)s %(mime_type)s" % {
                           'text': _("Embedded"),
                           'mime_type': mime_type,
                        }

        if mt.major == 'video':
            return '''
<object %(ob_data)s %(ob_type)s %(ob_width)s %(ob_height)s %(ob_align)s %(ob_standby)s %(ob_stop)s>
%(wmode)s
%(movie)s
%(play)s
%(stop)s
%(repeat)s
%(autostart)s
%(op)s
%(menu)s
<p>%(alt)s</p>
</object>''' % {
    "ob_data": self._check_object_value("data", url),
    "ob_type": self._check_object_value("type", mime_type),
    "ob_width": self._check_object_value("width", self.width),
    "ob_height": self._check_object_value("height", self.height),
    "ob_align": self._check_object_value("align", self.align),
    "ob_standby": self._check_object_value("standby", self.alt),
    "ob_stop": self._check_object_value("stop", self.stop),
    "wmode": self._check_param_value("wmode", self.wmode, "data"),
    "movie": self._check_param_value("movie", url, "data"),
    "play": self._check_param_value("play", self.play, "data"),
    "stop": self._check_param_value("stop", self.stop, "data"),
    "repeat": self._check_param_value("repeat", self.repeat, "data"),
    "autostart": self._check_param_value("autostart", self.autostart, "data"),
    "op": self._check_param_value("op", self.op, "data"),
    "menu": self._check_param_value("menu", self.menu, "data"),
    "alt": self.alt,
}

        if mt.major in ['image', 'chemical', 'x-world']:
            return '''
<object %(ob_data)s %(ob_type)s  %(ob_width)s %(ob_height)s %(ob_align)s>
<param name="%(major)s" value="%(url)s">
<p>%(alt)s</p>
</object>''' % {
    "ob_data": self._check_object_value("data", url),
    "ob_width": self._check_object_value("width", self.width),
    "ob_height": self._check_object_value("height", self.height),
    "ob_type": self._check_object_value("type", mime_type),
    "ob_align": self._check_object_value("align", self.align),
    "name": self._check_param_value("name", url, "data"),
    "alt": self.alt,
}

        if mt.major == 'audio':
            return '''
<object %(ob_data)s %(ob_type)s  %(ob_width)s %(ob_height)s %(ob_align)s>
%(audio)s
%(repeat)s
%(autostart)s
%(op)s
%(play)s
%(stop)s
%(hidden)s
<p>%(alt)s</p>
</object>''' % {
    "ob_data": self._check_object_value("data", url),
    "ob_width": self._check_object_value("width", self.width or "60"),
    "ob_height": self._check_object_value("height", self.height or "20"),
    "ob_type": self._check_object_value("type", mime_type),
    "ob_align": self._check_object_value("align", self.align),
    "audio": self._check_param_value("audio", url, "data"),
    "repeat": self._check_param_value("repeat", self.repeat, "data"),
    "autostart": self._check_param_value("autostart", self.autostart, "data"),
    "op": self._check_param_value("op", self.op, "data"),
    "play": self._check_param_value("play", self.play, "data"),
    "stop": self._check_param_value("stop", self.stop, "data"),
    "hidden": self._check_param_value("hidden", self.hidden, "data"),
    "alt": self.alt,
}

        if mt.major == 'application':
            # workaround for the acroread not knowing the size to embed
            if mt.minor == 'pdf':
                self.width = self.width or '800'
                self.height = self.height or '800'

            return '''
<object %(ob_data)s %(ob_type)s  %(ob_width)s %(ob_height)s %(ob_align)s>
%(wmode)s
%(autostart)s
%(play)s
%(loop)s
%(menu)s
<p>%(alt)s</p>
</object>''' % {
    "ob_data": self._check_object_value("data", url),
    "ob_width": self._check_object_value("width", self.width),
    "ob_height": self._check_object_value("height", self.height),
    "ob_type": self._check_object_value("type", mime_type),
    "ob_align": self._check_object_value("align", self.align),
    "wmode": self._check_param_value("wmode", self.wmode, "data"),
    "autostart": self._check_param_value("autostart", self.autostart, "data"),
    "play": self._check_param_value("play", self.play, "data"),
    "loop": self._check_param_value("loop", self.loop, "data"),
    "menu": self._check_param_value("menu", self.menu, "data"),
    "alt": self.alt,
}

    def render(self):
        _ = self._

        if not self.target:
            msg = _('Not enough arguments given to EmbedObject macro! Try <<EmbedObject(attachment [,width=width] [,height=height] [,alt=alternate Text])>>')
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
        else:
            if not self.url_mimetype:
                return _('Not enough arguments given to EmbedObject macro! Try <<EmbedObject(url, url_mimetype [,width=width] [,height=height] [,alt=alternate Text])>>')
            else:
                mt = wikiutil.MimeType() # initialize dict
                mt.major, mt.minor = self.url_mimetype.split('/')
                url = wikiutil.escape(self.target)

        # XXX Should better use formatter.embed if available?
        return self.macro.formatter.rawHTML(self.embed(mt, url))

def execute(macro, args):
    return EmbedObject(macro, args).render()

