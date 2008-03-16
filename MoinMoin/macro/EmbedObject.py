# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - EmbedObject Macro

    This macro is used to embed an object into a wiki page. Optionally, the
    size of the object can get adjusted. Further keywords are dependent on
    the kind of application, see HelpOnMacros/EmbedObject

    <<EmbedObject(attachment[,width=width][,height=height][,alt=alternate Text])>>

    @copyright: 2006-2008 MoinMoin:ReimarBauer,
                2006 TomSi,
                2007 OliverSiemoneit

    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import wikiutil
from MoinMoin.action import AttachFile

extension_type, extension_name = __name__.split('.')[-2:]

def _check_object_value(param, value):
    """
    helps omit useless lines of object values

    @param param: definition of object param
    @param value: value of param
    """
    if value:
        return '%(param)s="%(value)s"' % {"param": param, "value": wikiutil.escape(value)}
    else:
        return ""

def _check_param_value(param, value, valuetype):
    """ helps to ommit useless lines of param values
    @param param: param name defintion
    @param value: the value
    @param valuetype: the type of the value
    """
    if value:
        return '''
<param name="%(param)s" value="%(value)s" valuetype="%(valuetype)s">''' % {"param": param,
                                                                           "value": wikiutil.escape(value),
                                                                           "valuetype": valuetype}
    else:
        return ""

def macro_EmbedObject(macro, target=None, pagename=None, width=wikiutil.UnitArgument(None, float, ['px', 'em', 'mm', '%']),
                      height=wikiutil.UnitArgument(None, float, ['px', 'em', 'mm', '%']), alt=u'',
                      play=False, stop=True, loop=False, quality=(u'high', u'low', u'medium'),
                      op=True, repeat=False, autostart=False, align=(u'middle', u'top', u'bottom'), hidden=False,
                      menu=True, wmode=u'transparent', url_mimetype=None):

    """ This macro is used to embed an object into a wiki page """
    # Join unit arguments with their units
    if width:
        if width[1] == 'px':
            width = '%dpx' % int(width[0])
        else:
            width = '%g%s' % width

    if height:
        if height[1] == 'px':
            height = '%dpx' % int(height[0])
        else:
            height = '%g%s' % height

    request = macro.request
    _ = macro.request.getText
    fmt = macro.formatter

    # AttachFile calls always with pagename. Users can call the macro from a different page as the attachment is saved.
    if not pagename:
        pagename = fmt.page.page_name

    if not target:
        msg = _('Not enough arguments given to EmbedObject macro! Try <<EmbedObject(attachment [,width=width] [,height=height] [,alt=alternate Text])>>')
        return "%s%s%s" % (fmt.sysmsg(1), fmt.text(msg), fmt.sysmsg(0))

    if not wikiutil.is_URL(target):
        pagename, fname = AttachFile.absoluteName(target, pagename)

        if not AttachFile.exists(request, pagename, fname):
            linktext = _('Upload new attachment "%(filename)s"') % {'filename': fname}
            target = AttachFile.getAttachUrl(pagename, fname, request, upload=True)
            return (fmt.url(1, target) +
                    fmt.text(linktext) +
                    fmt.url(0))

        url = AttachFile.getAttachUrl(pagename, fname, request)
        mt = wikiutil.MimeType(filename=fname)
    else:
        if not url_mimetype:
            return _('Not enough arguments given to %(extension_name)s %(extension_type)s! Try <<EmbedObject(url, url_mimetype [,width=width] [,height=height] [,alt=alternate Text])>>') % {
               "extension_name": extension_name,
               "extension_type": extension_type,
               }
        else:
            mt = wikiutil.MimeType() # initialize dict
            mt.major, mt.minor = url_mimetype.split('/')
            url = target

        # XXX Should better use formatter.embed if available?
        if not mt:
            return _("Unknown mimetype %(mimetype)s of the file %(file)s.") % {"mimetype": url_mimetype,
                                                                               "file": target}

    mime_type = "%s/%s" % (mt.major, mt.minor, )
    dangerous = mime_type in request.cfg.mimetypes_xss_protect

    if not mime_type in request.cfg.mimetypes_embed or dangerous:
        kw = {'src': url}
        return "%s: %s%s%s" % (fmt.text(
                _("Current configuration doesn't allow mimetype %(mimetype)s of the file %(file)s.") % {"mimetype": mime_type,
                                                                                                        "file": target}),
                               fmt.url(1, kw['src']),
                               fmt.text(target),
                               fmt.url(0))

    if not alt:
        alt = "%(text)s %(mime_type)s" % {
                      'text': _("Embedded"),
                      'mime_type': mime_type,
                      }
    embed_src = ''
    if mt.major == 'video':
        if not width and not height:
            width = '400px'
            height = '400px'

        embed_src = '''
<object %(ob_data)s %(ob_type)s %(ob_width)s %(ob_height)s %(ob_align)s %(ob_standby)s %(ob_stop)s>
%(wmode)s%(movie)s%(play)s%(stop)s%(repeat)s%(autostart)s%(op)s%(menu)s
<p>%(alt)s</p>
</object>''' % {
    "ob_data": _check_object_value("data", url),
    "ob_type": _check_object_value("type", mime_type),
    "ob_width": _check_object_value("width", width),
    "ob_height": _check_object_value("height", height),
    "ob_align": _check_object_value("align", align),
    "ob_standby": _check_object_value("standby", alt),
    "ob_stop": _check_object_value("stop", stop),
    "wmode": _check_param_value("wmode", wmode, "data"),
    "movie": _check_param_value("movie", url, "data"),
    "play": _check_param_value("play", play, "data"),
    "stop": _check_param_value("stop", stop, "data"),
    "repeat": _check_param_value("repeat", repeat, "data"),
    "autostart": _check_param_value("autostart", autostart, "data"),
    "op": _check_param_value("op", op, "data"),
    "menu": _check_param_value("menu", menu, "data"),
    "alt": wikiutil.escape(alt),
}

    if mt.major in ['image', 'chemical', 'x-world']:
        embed_src = '''
<object %(ob_data)s %(ob_type)s  %(ob_width)s %(ob_height)s %(ob_align)s>
<param name="%(major)s" value="%(url)s">
<p>%(alt)s</p>
</object>''' % {
    "ob_data": _check_object_value("data", url),
    "ob_width": _check_object_value("width", width),
    "ob_height": _check_object_value("height", height),
    "ob_type": _check_object_value("type", mime_type),
    "ob_align": _check_object_value("align", align),
    "name": _check_param_value("name", url, "data"),
    "alt": wikiutil.escape(alt),
}

    if mt.major == 'audio':
        if not width and not height:
            width = '400px'
            height = '100px'
        embed_src = '''
<object %(ob_data)s %(ob_type)s  %(ob_width)s %(ob_height)s %(ob_align)s>
%(audio)s%(repeat)s%(autostart)s%(op)s%(play)s%(stop)s%(hidden)s<p>%(alt)s</p>
</object>''' % {
    "ob_data": _check_object_value("data", url),
    "ob_width": _check_object_value("width", width or "60"),
    "ob_height": _check_object_value("height", height or "20"),
    "ob_type": _check_object_value("type", mime_type),
    "ob_align": _check_object_value("align", align),
    "audio": _check_param_value("audio", url, "data"),
    "repeat": _check_param_value("repeat", repeat, "data"),
    "autostart": _check_param_value("autostart", autostart, "data"),
    "op": _check_param_value("op", op, "data"),
    "play": _check_param_value("play", play, "data"),
    "stop": _check_param_value("stop", stop, "data"),
    "hidden": _check_param_value("hidden", hidden, "data"),
    "alt": wikiutil.escape(alt),
}

    if mt.major == 'application':
        # workaround for the acroread not knowing the size to embed
        if mt.minor == 'pdf':
            width = width or '800px'
            height = height or '800px'

        embed_src = '''
<object %(ob_data)s %(ob_type)s  %(ob_width)s %(ob_height)s %(ob_align)s>
%(quality)s%(wmode)s%(autostart)s%(play)s%(loop)s%(menu)s<p>%(alt)s</p>
</object>''' % {
    "ob_data": _check_object_value("data", url),
    "ob_width": _check_object_value("width", width),
    "ob_height": _check_object_value("height", height),
    "ob_type": _check_object_value("type", mime_type),
    "ob_align": _check_object_value("align", align),
    "quality": _check_param_value("quality", quality, "data"),
    "wmode": _check_param_value("wmode", wmode, "data"),
    "autostart": _check_param_value("autostart", autostart, "data"),
    "play": _check_param_value("play", play, "data"),
    "loop": _check_param_value("loop", loop, "data"),
    "menu": _check_param_value("menu", menu, "data"),
    "alt": wikiutil.escape(alt),
}

    return embed_src

