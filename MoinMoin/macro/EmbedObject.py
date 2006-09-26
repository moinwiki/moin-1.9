# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - EmbedObject Macro

    PURPOSE:
        This macro is used to embed an object into a wiki page. Optionally, the
        size of the object can get adjusted. Further keywords are dependent on
        the kind of application.

    CALLING SEQUENCE:
        [[EmbedObject(attachment[,width=width][,height=height])]]

    SUPPORTED MIMETYPES:
         application/x-shockwave-flash 
         image/svg+xml
         application/pdf
         audio/mpeg
         application/vnd.visio

    INPUTS:
        attachment: name of attachment

    KEYWORD PARAMETERS:
        width: width of the embedded object, default is 100% of window
        height: height of the embedded object, default is 100% of window

        application/x-shockwave-flash:
          play: true is default
          loop: true is default
          quality: high is default (medium,low)

    EXAMPLE:
        [[EmbedObject]]
        [[EmbedObject(example.swf)]]
        [[EmbedObject(example.pdf]]
        [[EmbedObject(example.svg]]
        [[EmbedObject(example.mp3]]
        [[EmbedObject(example.vss]]
         
        [[EmbedObject(example.swf,width=637,height=392)]]
        [[EmbedObject(SlideShow/example.swf,width=637,height=392)]]
        [[EmbedObject(SlideShow/example.swf,width=637,height=392,play=false)]]
        [[EmbedObject(SlideShow/example.swf,width=637,height=392,play=false,loop=false)]]
        [[EmbedObject(SlideShow/example.swf,width=637,height=392,play=false,loop=low)]]

 
    PROCEDURE:
        If the attachment file isn't uploaded yet the attachment line will be shown.
        If you give only one size argument, e.g. width only, the other one will be calculated.

        By the swftools it is possible to get the swf size returned. I don't know if it is 
        possible to get sizes for svg, pdf and others detected too, that's the reason why 
        I haven't added it by now.

        Please add needed mimetypes as objects.


    MODIFICATION HISTORY:
        @copyright: 2006 by Reimar Bauer (R.Bauer@fz-juelich.de)      
        @license: GNU GPL, see COPYING for details.
        initial version: 1.5.0-1
        svg was added by AndrewArmstrong
        2006-05-04 TomSi: added mp3 support
        2006-05-09 RB code refactored, fixed a taintfilename bug
        2006-06-29 visio from OwenJones added but not tested,
                   RB code reviewed, taintfile removed
"""
import os, mimetypes

from MoinMoin import wikiutil
from MoinMoin.action import AttachFile

def execute(macro, args):
    request = macro.request
    _ = request.getText
    formatter = macro.formatter
    if args:
        args = args.split(',')
        args = [arg.strip() for arg in args]
    else:
        args = []

    argc = len(args)
    kw_count = 0
    kw = {}
    kw["width"] = "100%"
    kw["height"] = "100%"
    kw["play"] = "true"
    kw["loop"] = "true"
    kw["quality"] = "high"

    for arg in args:
        if '=' in arg:
            kw_count += 1
            key, value = arg.split('=', 1)
            kw[str(key)] = wikiutil.escape(value, quote=1)
    argc -= kw_count

    if not argc:
       msg = 'Not enough arguments to EmbedObject macro! Try [[EmbedObject(attachment [,width=width] [,height=heigt])]]'
       return "%s%s%s" % (formatter.sysmsg(1), formatter.text(msg), formatter.sysmsg(0))
    else:
        target = args[0]

    #target = wikiutil.taintfilename(target)
    pagename, attname = AttachFile.absoluteName(target, formatter.page.page_name)
    attachment_fname = AttachFile.getFilename(request, pagename, attname)

    if not os.path.exists(attachment_fname):
        linktext = _('Upload new attachment "%(filename)s"')
        return wikiutil.link_tag(request,
            ('%s?action=AttachFile&rename=%s' % (
            wikiutil.quoteWikinameURL(pagename),
            wikiutil.url_quote_plus(attname))),
            linktext % {'filename': attname})

    url = AttachFile.getAttachUrl(pagename, attname, request)
    mime_type, enc = mimetypes.guess_type(attname)
    if mime_type == "application/x-shockwave-flash":
        return '''
<OBJECT CLASSID="clsid:D27CDB6E-AE6D-11cf-96B8-444553540000" 
WIDTH="%(width)s"
HEIGHT="%(height)s"
CODEBASE="http://active.macromedia.com/flash5/cabs/swflash.cab#version=6,0,23,0">
<PARAM NAME="MOVIE" VALUE="%(file)s">
<PARAM NAME="PLAY" VALUE="%(play)s">
<PARAM NAME="LOOP" VALUE="%(loop)s">
<PARAM NAME="QUALITY" VALUE="%(quality)s">
<EMBED SRC="%(file)s" WIDTH="%(width)s" HEIGHT="%(height)s"
PLAY="%(play)s" ALIGN="" LOOP="%(loop)s" QUALITY="%(quality)s"
TYPE="application/x-shockwave-flash"
PLUGINSPAGE="http://www.macromedia.com/go/getflashplayer">
</EMBED>
</OBJECT>''' % {
    "width": kw["width"],
    "height": kw["height"],
    "play": kw["play"],
    "loop": kw["loop"],
    "quality": kw["quality"],
    "file": url,
}
    elif mime_type == "image/svg+xml":
        return '''
<OBJECT CLASSID="" 
WIDTH="%(width)s"
HEIGHT="%(height)s"
CODEBASE="http://purl.org/dc/dcmitype/StillImage">
<EMBED SRC="%(file)s" WIDTH="%(width)s" HEIGHT="%(height)s"
TYPE="image/svg+xml">
</EMBED>
</OBJECT>''' % {
    "width": kw["width"],
    "height": kw["height"],
    "file": url,
}
    elif mime_type == "application/pdf":
        return '''
<OBJECT CLASSID=""
WIDTH="%(width)s"
HEIGHT="%(height)s"
CODEBASE="http://www.adobe.com">
<EMBED SRC="%(file)s" WIDTH="%(width)s" HEIGHT="%(height)s"
TYPE="application/pdf">
</EMBED>
</OBJECT>''' % {
    "width": kw["width"],
    "height": kw["height"],
    "file": url,
}
    elif mime_type == "audio/mpeg":
        return '''
<OBJECT CLASSID=""
WIDTH="%(width)s"
HEIGHT="%(height)s"
<EMBED SRC="%(file)s" HEIGHT="0" REPEAT="TRUE" AUTOSTART="TRUE" WIDTH="0" OP="TRUE"
TYPE="audio/mpeg">
</EMBED>
</OBJECT>''' % {
    "width": kw["width"],
    "height": kw["height"],
    "file": url,
}
    elif mime_type == "application/vnd.visio":
        return  '''
<OBJECT CLASSID="CLSID:279D6C9A-652E-4833-BEFC-312CA8887857" 
CODEBASE="http://www.microsoft.com/technet/prodtechnol/office/visio2003/depvisvw.mspx"
ID="viewer1" WIDTH="%(width)s" HEIGHT="%(height)s"> <PARAM NAME="CurrentPageIndex" VALUE="0"> 
<PARAM NAME="Zoom" VALUE="-1"> <PARAM NAME = "SRC" 
VALUE = "%(file)s">Your browser cannot display Visio</OBJECT>''' % {
    "width": kw['width'],
    "height": kw['height'],
    "file": url,
}
    elif mime_type == "audio/midi":
        return '''
<OBJECT CLASSID="clsid:02BF25D5-8C17-4B23-BC80-D3488ABDDC6B"
WIDTH="%(width)s"
HEIGHT="%(height)s"
<EMBED SRC="%(file)s" HEIGHT="0" REPEAT="TRUE" AUTOSTART="TRUE" WIDTH="0" OP="TRUE"
TYPE="audio/midi">
</EMBED>
</OBJECT>''' % {
    "width": kw["width"],
    "height": kw["height"],
    "file": url,
}
    elif mime_type == "video/mpeg":
        return '''
<OBJECT CLASSID="CLSID:05589FA1-C356-11CE-BF01-00AA0055595A"
WIDTH="%(width)s"
HEIGHT="%(height)s"
<EMBED SRC="%(file)s" HEIGHT="0" REPEAT="TRUE" AUTOSTART="TRUE" WIDTH="0" OP="TRUE"
TYPE="application/x-mplayer2">
</EMBED>
</OBJECT>''' % {
   "width": kw["width"],
   "height": kw["height"],
   "file": url,
}
    elif mime_type == "video/quicktime":
        return '''
<OBJECT CLASSID="clsid:02BF25D5-8C17-4B23-BC80-D3488ABDDC6B"
WIDTH="%(width)s"
HEIGHT="%(height)s"
<EMBED SRC="%(file)s" HEIGHT="0" REPEAT="TRUE" AUTOSTART="TRUE" WIDTH="0" OP="TRUE"
TYPE="video/quicktime">
</EMBED>
</OBJECT>''' % {
   "width": kw["width"],
   "height": kw["height"],
   "file": url,
}
    else:
        msg = 'Not supported mimetype %(mimetype)s ' % {"mimetype": mime_type}
        return "%s%s%s" % (macro.formatter.sysmsg(1),
                   macro.formatter.text(msg),
                   macro.formatter.sysmsg(0))

