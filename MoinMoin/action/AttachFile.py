# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - AttachFile action

    This action lets a page have multiple attachment files.
    It creates a folder <data>/pages/<pagename>/attachments
    and keeps everything in there.

    Form values: action=Attachment
    1. with no 'do' key: returns file upload form
    2. do=attach: accept file upload and saves the file in
       ../attachment/pagename/
    3. /pagename/fname?action=Attachment&do=get[&mimetype=type]:
       return contents of the attachment file with the name fname.
    4. /pathname/fname, do=view[&mimetype=type]:create a page
       to view the content of the file

    To link to an attachment, use [[attachment:file.txt]],
    to embed an attachment, use {{attachment:file.png}}.

    @copyright: 2001 by Ken Sugino (sugino@mediaone.net),
                2001-2004 by Juergen Hermann <jh@web.de>,
                2005 MoinMoin:AlexanderSchremmer,
                2005 DiegoOngaro at ETSZONE (diego@etszone.com),
                2005-2007 MoinMoin:ReimarBauer,
                2007-2008 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import os, time, zipfile, mimetypes, errno

from MoinMoin import config, wikiutil, packages
from MoinMoin.Page import Page
from MoinMoin.util import filesys, timefuncs
from MoinMoin.security.textcha import TextCha
from MoinMoin.events import FileAttachedEvent, send_event
import MoinMoin.events.notification as notification

action_name = __name__.split('.')[-1]

#############################################################################
### External interface - these are called from the core code
#############################################################################

class AttachmentAlreadyExists(Exception):
    pass

def getBasePath(request):
    """ Get base path where page dirs for attachments are stored.
    """
    return request.rootpage.getPagePath('pages')


def getAttachDir(request, pagename, create=0):
    """ Get directory where attachments for page `pagename` are stored.
    """
    if request.page and pagename == request.page.page_name:
        page = request.page # reusing existing page obj is faster
    else:
        page = Page(request, pagename)
    return page.getPagePath("attachments", check_create=create)

def absoluteName(url, pagename):
    """ Get (pagename, filename) of an attachment: link
        @param url: PageName/filename.ext or filename.ext (unicode)
        @param pagename: name of the currently processed page (unicode)
        @rtype: tuple of unicode
        @return: PageName, filename.ext
    """
    url = wikiutil.AbsPageName(pagename, url)
    pieces = url.split(u'/')
    if len(pieces) == 1:
        return pagename, pieces[0]
    else:
        return u"/".join(pieces[:-1]), pieces[-1]

def attachUrl(request, pagename, filename=None, **kw):
    # filename is not used yet, but should be used later to make a sub-item url
    if kw:
        qs = '?%s' % wikiutil.makeQueryString(kw, want_unicode=False)
    else:
        qs = ''
    return "%s/%s%s" % (request.getScriptname(), wikiutil.quoteWikinameURL(pagename), qs)
    
def getAttachUrl(pagename, filename, request, addts=0, escaped=0, do='get', drawing='', upload=False):
    """ Get URL that points to attachment `filename` of page `pagename`. """
    if upload:
        if not drawing:
            url = attachUrl(request, pagename, filename,
                            rename=filename, action=action_name)
        else:
            url = attachUrl(request, pagename, filename,
                            rename=filename, drawing=drawing, action=action_name)
    else:
        if not drawing:
            url = attachUrl(request, pagename, filename,
                            target=filename, action=action_name, do=do)
        else:
            url = attachUrl(request, pagename, filename,
                            drawing=drawing, action=action_name)
    if escaped:
        url = wikiutil.escape(url)
    return url


def getIndicator(request, pagename):
    """ Get an attachment indicator for a page (linked clip image) or
        an empty string if not attachments exist.
    """
    _ = request.getText
    attach_dir = getAttachDir(request, pagename)
    if not os.path.exists(attach_dir):
        return ''

    files = os.listdir(attach_dir)
    if not files:
        return ''

    fmt = request.formatter
    attach_count = _('[%d attachments]') % len(files)
    attach_icon = request.theme.make_icon('attach', vars={'attach_count': attach_count})
    attach_link = (fmt.url(1, attachUrl(request, pagename, action=action_name), rel='nofollow') +
                   attach_icon +
                   fmt.url(0))
    return attach_link


def getFilename(request, pagename, filename):
    """ make complete pathfilename of file "name" attached to some page "pagename"
        @param request: request object
        @param pagename: name of page where the file is attached to (unicode)
        @param filename: filename of attached file (unicode)
        @rtype: string (in config.charset encoding)
        @return: complete path/filename of attached file
    """
    if isinstance(filename, unicode):
        filename = filename.encode(config.charset)
    return os.path.join(getAttachDir(request, pagename, create=1), filename)

def exists(request, pagename, filename):
    """ check if page <pagename> has a file <filename> attached """
    fpath = getFilename(request, pagename, filename)
    return os.path.exists(fpath)

def size(request, pagename, filename):
    """ return file size of file attachment """
    fpath = getFilename(request, pagename, filename)
    return os.path.getsize(fpath)

def info(pagename, request):
    """ Generate snippet with info on the attachment for page `pagename`.
    """
    _ = request.getText

    attach_dir = getAttachDir(request, pagename)
    files = []
    if os.path.isdir(attach_dir):
        files = os.listdir(attach_dir)
    page = Page(request, pagename)
    link = page.url(request, {'action': action_name})
    attach_info = _('There are <a href="%(link)s">%(count)s attachment(s)</a> stored for this page.') % {
        'count': len(files),
        'link': wikiutil.escape(link)
        }
    return "\n<p>\n%s\n</p>\n" % attach_info

def add_attachment(request, pagename, target, filecontent, overwrite=0):
    # replace illegal chars

    _ = request.getText

    target = wikiutil.taintfilename(target)

    # set mimetype from extension, or from given mimetype
    #type, encoding = wikiutil.guess_type(target)
    #if not type:
    #    ext = None
    #    if 'mime' in request.form:
    #        ext = wikiutil.guess_extension(request.form['mime'][0])
    #    if not ext:
    #        type, encoding = wikiutil.guess_type(filename)
    #        if type:
    #            ext = wikiutil.guess_extension(type)
    #        else:
    #            ext = ''
    #    target = target + ext

    # get directory, and possibly create it
    attach_dir = getAttachDir(request, pagename, create=1)
    # save file
    fpath = os.path.join(attach_dir, target).encode(config.charset)
    exists = os.path.exists(fpath)
    if exists and not overwrite:
        msg = _("Attachment '%(target)s' already exists.") % {'target': target, }
    else:
        if exists:
            try:
                os.remove(fpath)
            except:
                pass
        stream = open(fpath, 'wb')
        try:
            stream.write(filecontent)
        finally:
            stream.close()

        _addLogEntry(request, 'ATTNEW', pagename, target)

        event = FileAttachedEvent(request, pagename, target, len(filecontent))
        send_event(event)

        return target


#############################################################################
### Internal helpers
#############################################################################

def _addLogEntry(request, action, pagename, filename):
    """ Add an entry to the edit log on uploads and deletes.

        `action` should be "ATTNEW" or "ATTDEL"
    """
    from MoinMoin.logfile import editlog
    t = wikiutil.timestamp2version(time.time())
    fname = wikiutil.url_quote(filename, want_unicode=True)

    # Write to global log
    log = editlog.EditLog(request)
    log.add(request, t, 99999999, action, pagename, request.remote_addr, fname)

    # Write to local log
    log = editlog.EditLog(request, rootpagename=pagename)
    log.add(request, t, 99999999, action, pagename, request.remote_addr, fname)


def _access_file(pagename, request):
    """ Check form parameter `target` and return a tuple of
        `(filename, filepath)` for an existing attachment.

        Return `(None, None)` if an error occurs.
    """
    _ = request.getText

    error = None
    if not request.form.get('target', [''])[0]:
        error = _("Filename of attachment not specified!")
    else:
        filename = wikiutil.taintfilename(request.form['target'][0])
        fpath = getFilename(request, pagename, filename)

        if os.path.isfile(fpath):
            return (filename, fpath)
        error = _("Attachment '%(filename)s' does not exist!") % {'filename': filename}

    error_msg(pagename, request, error)
    return (None, None)


def _build_filelist(request, pagename, showheader, readonly, mime_type='*'):
    _ = request.getText
    fmt = request.html_formatter

    # access directory
    attach_dir = getAttachDir(request, pagename)
    files = _get_files(request, pagename)

    if mime_type != '*':
        files = [fname for fname in files if mime_type == mimetypes.guess_type(fname)[0]]

    html = ""
    if files:
        if showheader:
            html += _(
                "To refer to attachments on a page, use '''{{{[[attachment:filename]]}}}''', \n"
                "as shown below in the list of files. \n"
                "Do '''NOT''' use the URL of the {{{[get]}}} link, \n"
                "since this is subject to change and can break easily.",
                wiki=True
            )
        html += "<ul>"

        label_del = _("del")
        label_move = _("move")
        label_get = _("get")
        label_edit = _("edit")
        label_view = _("view")
        label_unzip = _("unzip")
        label_install = _("install")

        for file in files:
            mt = wikiutil.MimeType(filename=file)
            st = os.stat(os.path.join(attach_dir, file).encode(config.charset))
            fsize = "%.1f" % (float(st.st_size) / 1024)
            fmtime = request.user.getFormattedDateTime(st.st_mtime)
            baseurl = request.getScriptname()
            base, ext = os.path.splitext(file)
            escaped_fname = wikiutil.escape(file)
            parmdict = {'baseurl': baseurl,
                        'base': base,
                        'file': escaped_fname,
                        'fsize': fsize,
                        'fmtime': fmtime,
                        'pagename': pagename}

            if request.user.may.delete(pagename) and not readonly:
                del_link = (fmt.url(1, getAttachUrl(pagename, file, request, do='del')) +
                            fmt.text(label_del) +
                            fmt.url(0) +
                            fmt.rawHTML('&nbsp;| '))
            else:
                del_link = ''

            if request.user.may.delete(pagename) and not readonly:
                move_link = (fmt.url(1, getAttachUrl(pagename, file, request, do='move')) +
                             fmt.text(label_move) +
                             fmt.url(0) +
                             fmt.rawHTML('&nbsp;| '))
            else:
                move_link = ''

            if ext == '.draw':
                view_link = (fmt.url(1, getAttachUrl(pagename, file, request, drawing=parmdict['base'])) +
                             fmt.text(label_edit) +
                             fmt.url(0))
            else:
                view_link = (fmt.url(1, getAttachUrl(pagename, file, request, do='view')) +
                             fmt.text(label_view) +
                             fmt.url(0))

            is_zipfile = zipfile.is_zipfile(os.path.join(attach_dir, file).encode(config.charset))
            if is_zipfile:
                is_package = packages.ZipPackage(request, os.path.join(attach_dir, file).encode(config.charset)).isPackage()
                if is_package and request.user.isSuperUser():
                    view_link += (' | ' + 
                                  fmt.url(1, getAttachUrl(pagename, file, request, do='install')) +
                                  fmt.text(label_install) +
                                  fmt.url(0))
                elif (not is_package and mt.minor == 'zip' and request.user.may.read(pagename) and request.user.may.delete(pagename)
                      and request.user.may.write(pagename)):
                    view_link += (' | ' + 
                                  fmt.url(1, getAttachUrl(pagename, file, request, do='unzip')) +
                                  fmt.text(label_unzip) +
                                  fmt.url(0))

            get_link = (fmt.url(1, getAttachUrl(pagename, file, request)) +
                        fmt.text(label_get) +
                        fmt.url(0) +
                        fmt.rawHTML('&nbsp;| '))

            parmdict['viewlink'] = view_link
            parmdict['del_link'] = del_link
            parmdict['move_link'] = move_link
            parmdict['get_link'] = get_link

            html += ('<li>[%(del_link)s%(move_link)s%(get_link)s%(viewlink)s]'
                ' (%(fmtime)s, %(fsize)s KB) [[attachment:%(file)s]]</li>') % parmdict
        html += "</ul>"
    else:
        if showheader:
            html += '<p>%s</p>' % (_("No attachments stored for %(pagename)s") % {'pagename': wikiutil.escape(pagename)})

    return html


def _get_files(request, pagename):
    attach_dir = getAttachDir(request, pagename)
    if os.path.isdir(attach_dir):
        files = [fn.decode(config.charset) for fn in os.listdir(attach_dir)]
        files.sort()
        return files
    return []


def _get_filelist(request, pagename):
    return _build_filelist(request, pagename, 1, 0)

def _subdir_exception(zf):
    """
    Checks for the existance of one common subdirectory shared among
    all files in the zip file. If this is the case, returns a dict of
    original names to modified names so that such files can be unpacked
    as the user would expect.
    """

    b = zf.namelist()
    if not '/' in b[0]:
        return False #No directory
    slashoffset = b[0].index('/')
    directory = b[0][:slashoffset]
    for origname in b:
        if origname.rfind('/') != slashoffset or origname[:slashoffset] != directory:
            return False #Multiple directories or different directory
    names = {}
    for origname in b:
        names[origname] = origname[slashoffset+1:]
    return names #Returns dict of {origname: safename}

def error_msg(pagename, request, msg):
    request.theme.add_msg(msg, "error")
    Page(request, pagename).send_page()


#############################################################################
### Create parts of the Web interface
#############################################################################

def send_link_rel(request, pagename):
    files = _get_files(request, pagename)
    for fname in files:
        url = getAttachUrl(pagename, fname, request, do='view', escaped=1)
        request.write(u'<link rel="Appendix" title="%s" href="%s">\n' % (
                      wikiutil.escape(fname), url))


def send_hotdraw(pagename, request):
    _ = request.getText

    now = time.time()
    pubpath = request.cfg.url_prefix_static + "/applets/TWikiDrawPlugin"
    basename = request.form['drawing'][0]
    drawpath = getAttachUrl(pagename, basename + '.draw', request, escaped=1)
    pngpath = getAttachUrl(pagename, basename + '.png', request, escaped=1)
    pagelink = attachUrl(request, pagename, '', action=action_name, ts=now)
    helplink = Page(request, "HelpOnActions/AttachFile").url(request)
    savelink = attachUrl(request, pagename, '', action=action_name, do='savedrawing')
    #savelink = Page(request, pagename).url(request) # XXX include target filename param here for twisted
                                           # request, {'savename': request.form['drawing'][0]+'.draw'}
    #savelink = '/cgi-bin/dumpform.bat'

    timestamp = '&amp;ts=%s' % now

    request.write('<h2>' + _("Edit drawing") + '</h2>')
    request.write("""
<p>
<img src="%(pngpath)s%(timestamp)s">
<applet code="CH.ifa.draw.twiki.TWikiDraw.class"
        archive="%(pubpath)s/twikidraw.jar" width="640" height="480">
<param name="drawpath" value="%(drawpath)s">
<param name="pngpath"  value="%(pngpath)s">
<param name="savepath" value="%(savelink)s">
<param name="basename" value="%(basename)s">
<param name="viewpath" value="%(pagelink)s">
<param name="helppath" value="%(helplink)s">
<strong>NOTE:</strong> You need a Java enabled browser to edit the drawing example.
</applet>
</p>""" % {
    'pngpath': pngpath, 'timestamp': timestamp,
    'pubpath': pubpath, 'drawpath': drawpath,
    'savelink': savelink, 'pagelink': pagelink, 'helplink': helplink,
    'basename': basename
})


def send_uploadform(pagename, request):
    """ Send the HTML code for the list of already stored attachments and
        the file upload form.
    """
    _ = request.getText

    if not request.user.may.read(pagename):
        request.write('<p>%s</p>' % _('You are not allowed to view this page.'))
        return

    writeable = request.user.may.write(pagename)

    # First send out the upload new attachment form on top of everything else.
    # This avoids usability issues if you have to scroll down a lot to upload
    # a new file when the page already has lots of attachments:
    if writeable:
        request.write('<h2>' + _("New Attachment") + '</h2><p>' +
_("""An upload will never overwrite an existing file. If there is a name
conflict, you have to rename the file that you want to upload.
Otherwise, if "Rename to" is left blank, the original filename will be used.""") + '</p>')
        request.write("""
<form action="%(baseurl)s/%(pagename)s" method="POST" enctype="multipart/form-data">
<dl>
<dt>%(upload_label_file)s</dt>
<dd><input type="file" name="file" size="50"></dd>
<dt>%(upload_label_rename)s</dt>
<dd><input type="text" name="rename" size="50" value="%(rename)s"></dd>
<dt>%(upload_label_overwrite)s</dt>
<dd><input type="checkbox" name="overwrite" value="1" %(overwrite_checked)s></dd>
</dl>
%(textcha)s
<p>
<input type="hidden" name="action" value="%(action_name)s">
<input type="hidden" name="do" value="upload">
<input type="submit" value="%(upload_button)s">
</p>
</form>
""" % {
    'baseurl': request.getScriptname(),
    'pagename': wikiutil.quoteWikinameURL(pagename),
    'action_name': action_name,
    'upload_label_file': _('File to upload'),
    'upload_label_rename': _('Rename to'),
    'rename': request.form.get('rename', [''])[0],
    'upload_label_overwrite': _('Overwrite existing attachment of same name'),
    'overwrite_checked': ('', 'checked')[request.form.get('overwrite', ['0'])[0] == '1'],
    'upload_button': _('Upload'),
    'textcha': TextCha(request).render(),
})

#<dt>%(upload_label_mime)s</dt>
#<dd><input type="text" name="mime" size="50"></dd>
#    'upload_label_mime': _('MIME Type (optional)'),

    request.write('<h2>' + _("Attached Files") + '</h2>')
    request.write(_get_filelist(request, pagename))

    if not writeable:
        request.write('<p>%s</p>' % _('You are not allowed to attach a file to this page.'))

    if writeable and request.form.get('drawing', [None])[0]:
        send_hotdraw(pagename, request)


#############################################################################
### Web interface for file upload, viewing and deletion
#############################################################################

def execute(pagename, request):
    """ Main dispatcher for the 'AttachFile' action.
    """
    _ = request.getText

    if action_name in request.cfg.actions_excluded:
        msg = _('File attachments are not allowed in this wiki!')
        error_msg(pagename, request, msg)
        return

    do = request.form.get('do')
    if do is None:
        upload_form(pagename, request)
        return

    msg = None
    do = do[0]

    # First handle read-only access to attachments:
    if do == 'get':
        if request.user.may.read(pagename):
            get_file(pagename, request)
        else:
            msg = _('You are not allowed to get attachments from this page.')
    elif do == 'view':
        if request.user.may.read(pagename):
            view_file(pagename, request)
        else:
            msg = _('You are not allowed to view attachments of this page.')
    elif do == 'move':
        if request.user.may.delete(pagename):
            send_moveform(pagename, request)
        else:
            msg = _('You are not allowed to move attachments from this page.')

    # Second handle write access:
    elif do == 'upload':
        # Currently we only check TextCha for upload (this is what spammers ususally do),
        # but it could be extended to more/all attachment write access
        if not TextCha(request).check_answer_from_form():
            msg = _('TextCha: Wrong answer! Go back and try again...')
        else:
            overwrite = 0
            if 'overwrite' in request.form:
                try:
                    overwrite = int(request.form['overwrite'][0])
                except:
                    pass
            if (not overwrite and request.user.may.write(pagename)) or \
               (overwrite and request.user.may.write(pagename) and request.user.may.delete(pagename)):
                if 'file' in request.form:
                    do_upload(pagename, request, overwrite)
                else:
                    # This might happen when trying to upload file names
                    # with non-ascii characters on Safari.
                    msg = _("No file content. Delete non ASCII characters from the file name and try again.")
            else:
                msg = _('You are not allowed to attach a file to this page.')
    elif do == 'savedrawing':
        if request.user.may.write(pagename):
            save_drawing(pagename, request)
            request.emit_http_headers()
            request.write("OK")
        else:
            msg = _('You are not allowed to save a drawing on this page.')
    elif do == 'del':
        if request.user.may.delete(pagename):
            del_file(pagename, request)
        else:
            msg = _('You are not allowed to delete attachments on this page.')
    elif do == 'attachment_move':
        if 'cancel' in request.form:
            msg = _('Move aborted!')
            error_msg(pagename, request, msg)
            return
        if not wikiutil.checkTicket(request, request.form['ticket'][0]):
            msg = _('Please use the interactive user interface to move attachments!')
            error_msg(pagename, request, msg)
            return
        if request.user.may.delete(pagename):
            attachment_move(pagename, request)
        else:
            msg = _('You are not allowed to move attachments from this page.')
    elif do == 'unzip':
        if request.user.may.delete(pagename) and request.user.may.read(pagename) and request.user.may.write(pagename):
            unzip_file(pagename, request)
        else:
            msg = _('You are not allowed to unzip attachments of this page.')
    elif do == 'install':
        if request.user.isSuperUser():
            install_package(pagename, request)
        else:
            msg = _('You are not allowed to install files.')
    else:
        msg = _('Unsupported AttachFile sub-action: %s') % (wikiutil.escape(do), )

    if msg:
        error_msg(pagename, request, msg)

def upload_form(pagename, request, msg=''):
    _ = request.getText

    request.emit_http_headers()
    # Use user interface language for this generated page
    request.setContentLanguage(request.lang)
    request.theme.add_msg(msg, "dialog")
    request.theme.send_title(_('Attachments for "%(pagename)s"') % {'pagename': pagename}, pagename=pagename)
    request.write('<div id="content">\n') # start content div
    send_uploadform(pagename, request)
    request.write('</div>\n') # end content div
    request.theme.send_footer(pagename)
    request.theme.send_closing_html()

def do_upload(pagename, request, overwrite):
    _ = request.getText

    # make filename
    filename = None
    if 'file__filename__' in request.form:
        filename = request.form['file__filename__']
    rename = None
    if 'rename' in request.form:
        rename = request.form['rename'][0].strip()

    # if we use twisted, "rename" field is NOT optional, because we
    # can't access the client filename
    if rename:
        target = rename
        # clear rename its only once wanted
        request.form['rename'][0] = u''
    elif filename:
        target = filename
    else:
        error_msg(pagename, request, _("Filename of attachment not specified!"))
        return

    # get file content
    filecontent = request.form['file'][0]

    # preprocess the filename
    # strip leading drive and path (IE misbehaviour)
    if len(target) > 1 and (target[1] == ':' or target[0] == '\\'): # C:.... or \path... or \\server\...
        bsindex = target.rfind('\\')
        if bsindex >= 0:
            target = target[bsindex+1:]

    # add the attachment
    try:
        add_attachment(request, pagename, target, filecontent, overwrite=overwrite)

        bytes = len(filecontent)
        msg = _("Attachment '%(target)s' (remote name '%(filename)s')"
                " with %(bytes)d bytes saved.") % {
                'target': target, 'filename': filename, 'bytes': bytes}
    except AttachmentAlreadyExists:
        msg = _("Attachment '%(target)s' (remote name '%(filename)s') already exists.") % {
            'target': target, 'filename': filename}

    # return attachment list
    upload_form(pagename, request, msg)


def save_drawing(pagename, request):

    filename = request.form['filename'][0]
    filecontent = request.form['filepath'][0]

    basepath, basename = os.path.split(filename)
    basename, ext = os.path.splitext(basename)

    # get directory, and possibly create it
    attach_dir = getAttachDir(request, pagename, create=1)

    if ext == '.draw':
        _addLogEntry(request, 'ATTDRW', pagename, basename + ext)
        filecontent = filecontent.replace("\r", "")

    savepath = os.path.join(attach_dir, basename + ext)
    if ext == '.map' and not filecontent.strip():
        # delete map file if it is empty
        try:
            os.unlink(savepath)
        except OSError, err:
            if err.errno != errno.ENOENT: # no such file
                raise
    else:
        stream = open(savepath, 'wb')
        try:
            stream.write(filecontent)
        finally:
            stream.close()

    # touch attachment directory to invalidate cache if new map is saved
    if ext == '.map':
        os.utime(getAttachDir(request, pagename), None)

def del_file(pagename, request):
    _ = request.getText

    filename, fpath = _access_file(pagename, request)
    if not filename:
        return # error msg already sent in _access_file

    # delete file
    os.remove(fpath)
    _addLogEntry(request, 'ATTDEL', pagename, filename)

    if request.cfg.xapian_search:
        from MoinMoin.search.Xapian import Index
        index = Index(request)
        if index.exists:
            index.remove_item(pagename, filename)

    upload_form(pagename, request, msg=_("Attachment '%(filename)s' deleted.") % {'filename': filename})

def move_file(request, pagename, new_pagename, attachment, new_attachment):
    _ = request.getText

    newpage = Page(request, new_pagename)
    if newpage.exists(includeDeleted=1) and request.user.may.write(new_pagename) and request.user.may.delete(pagename):
        new_attachment_path = os.path.join(getAttachDir(request, new_pagename,
                              create=1), new_attachment).encode(config.charset)
        attachment_path = os.path.join(getAttachDir(request, pagename),
                          attachment).encode(config.charset)

        if os.path.exists(new_attachment_path):
            upload_form(pagename, request, msg=_("Attachment '%(filename)s' already exists.") % {
                                   'filename': new_attachment})
            return

        if new_attachment_path != attachment_path:
        # move file
            filesys.rename(attachment_path, new_attachment_path)
            _addLogEntry(request, 'ATTDEL', pagename, attachment)
            _addLogEntry(request, 'ATTNEW', new_pagename, new_attachment)
            upload_form(pagename, request, msg=_("Attachment '%(filename)s' moved to %(page)s.") % {
                                                 'filename': new_attachment,
                                                 'page': new_pagename})
        else:
            upload_form(pagename, request, msg=_("Nothing changed"))
    else:
        upload_form(pagename, request, msg=_("Page %(newpagename)s does not exists or you don't have enough rights.") % {
            'newpagename': new_pagename})

def attachment_move(pagename, request):
    _ = request.getText
    if 'newpagename' in request.form:
        new_pagename = request.form.get('newpagename')[0]
    else:
        upload_form(pagename, request, msg=_("Move aborted because empty page name"))
    if 'newattachmentname' in request.form:
        new_attachment = request.form.get('newattachmentname')[0]
        if new_attachment != wikiutil.taintfilename(new_attachment):
            upload_form(pagename, request, msg=_("Please use a valid filename for attachment '%(filename)s'.") % {
                                  'filename': new_attachment})
            return
    else:
        upload_form(pagename, request, msg=_("Move aborted because empty attachment name"))

    attachment = request.form.get('oldattachmentname')[0]
    move_file(request, pagename, new_pagename, attachment, new_attachment)

def send_moveform(pagename, request):
    _ = request.getText

    filename, fpath = _access_file(pagename, request)
    if not filename:
        return # error msg already sent in _access_file

    # move file
    d = {'action': action_name,
         'baseurl': request.getScriptname(),
         'do': 'attachment_move',
         'ticket': wikiutil.createTicket(request),
         'pagename': pagename,
         'pagename_quoted': wikiutil.quoteWikinameURL(pagename),
         'attachment_name': filename,
         'move': _('Move'),
         'cancel': _('Cancel'),
         'newname_label': _("New page name"),
         'attachment_label': _("New attachment name"),
        }
    formhtml = '''
<form action="%(baseurl)s/%(pagename_quoted)s" method="POST">
<input type="hidden" name="action" value="%(action)s">
<input type="hidden" name="do" value="%(do)s">
<input type="hidden" name="ticket" value="%(ticket)s">
<table>
    <tr>
        <td class="label"><label>%(newname_label)s</label></td>
        <td class="content">
            <input type="text" name="newpagename" value="%(pagename)s" size="80">
        </td>
    </tr>
    <tr>
        <td class="label"><label>%(attachment_label)s</label></td>
        <td class="content">
            <input type="text" name="newattachmentname" value="%(attachment_name)s" size="80">
        </td>
    </tr>
    <tr>
        <td></td>
        <td class="buttons">
            <input type="hidden" name="oldattachmentname" value="%(attachment_name)s">
            <input type="submit" name="move" value="%(move)s">
            <input type="submit" name="cancel" value="%(cancel)s">
        </td>
    </tr>
</table>
</form>''' % d
    thispage = Page(request, pagename)
    request.theme.add_msg(formhtml, "dialog")
    return thispage.send_page()

def get_file(pagename, request):
    import shutil

    filename, fpath = _access_file(pagename, request)
    if not filename:
        return # error msg already sent in _access_file

    timestamp = timefuncs.formathttpdate(int(os.path.getmtime(fpath)))
    if request.if_modified_since == timestamp:
        request.emit_http_headers(["Status: 304 Not modified"])
    else:
        mt = wikiutil.MimeType(filename=filename)
        content_type = mt.content_type()
        mime_type = mt.mime_type()

        # TODO: fix the encoding here, plain 8 bit is not allowed according to the RFCs
        # There is no solution that is compatible to IE except stripping non-ascii chars
        filename_enc = filename.encode(config.charset)

        # for dangerous files (like .html), when we are in danger of cross-site-scripting attacks,
        # we just let the user store them to disk ('attachment').
        # For safe files, we directly show them inline (this also works better for IE).
        dangerous = mime_type in request.cfg.mimetypes_xss_protect
        content_dispo = dangerous and 'attachment' or 'inline'

        request.emit_http_headers([
            'Content-Type: %s' % content_type,
            'Last-Modified: %s' % timestamp,
            'Content-Length: %d' % os.path.getsize(fpath),
            'Content-Disposition: %s; filename="%s"' % (content_dispo, filename_enc),
        ])

        # send data
        shutil.copyfileobj(open(fpath, 'rb'), request, 8192)

def install_package(pagename, request):
    _ = request.getText

    target, targetpath = _access_file(pagename, request)
    if not target:
        return

    package = packages.ZipPackage(request, targetpath)

    if package.isPackage():
        if package.installPackage():
            msg = _("Attachment '%(filename)s' installed.") % {'filename': wikiutil.escape(target)}
        else:
            msg = _("Installation of '%(filename)s' failed.") % {'filename': wikiutil.escape(target)}
        if package.msg:
            msg += "<br><pre>%s</pre>" % wikiutil.escape(package.msg)
    else:
        msg = _('The file %s is not a MoinMoin package file.') % wikiutil.escape(target)

    upload_form(pagename, request, msg=msg)

def unzip_file(pagename, request):
    _ = request.getText
    valid_pathname = lambda name: ('/' not in name) and ('\\' not in name)

    filename, fpath = _access_file(pagename, request)
    if not filename:
        return # error msg already sent in _access_file

    single_file_size = request.cfg.unzip_single_file_size
    attachments_file_space = request.cfg.unzip_attachments_space
    attachments_file_count = request.cfg.unzip_attachments_count

    files = _get_files(request, pagename)

    msg = ""
    if files:
        fsize = 0.0
        fcount = 0
        for f in files:
            fsize += float(size(request, pagename, f))
            fcount += 1

        available_attachments_file_space = attachments_file_space - fsize
        available_attachments_file_count = attachments_file_count - fcount

        if zipfile.is_zipfile(fpath):
            zf = zipfile.ZipFile(fpath)
            sum_size_over_all_valid_files = 0.0
            count_valid_files = 0
            namelist = _subdir_exception(zf)
            if not namelist: #if it's not handled by _subdir_exception()
                #Convert normal zf.namelist() to {origname:finalname} dict
                namelist = {}
                for name in zf.namelist():
                    namelist[name] = name
            for (origname, finalname) in namelist.iteritems():
                if valid_pathname(finalname):
                    sum_size_over_all_valid_files += zf.getinfo(origname).file_size
                    count_valid_files += 1

            if sum_size_over_all_valid_files > available_attachments_file_space:
                msg = _("Attachment '%(filename)s' could not be unzipped because"
                        " the resulting files would be too large (%(space)d kB"
                        " missing).") % {
                            'filename': filename,
                            'space': (sum_size_over_all_valid_files -
                                available_attachments_file_space) / 1000 }
            elif count_valid_files > available_attachments_file_count:
                msg = _("Attachment '%(filename)s' could not be unzipped because"
                        " the resulting files would be too many (%(count)d "
                        "missing).") % {
                            'filename': filename,
                            'count': (count_valid_files -
                                available_attachments_file_count) }
            else:
                valid_name = False
                for (origname, finalname) in namelist.iteritems():
                    if valid_pathname(finalname):
                        zi = zf.getinfo(origname)
                        if zi.file_size < single_file_size:
                            new_file = getFilename(request, pagename, finalname)
                            if not os.path.exists(new_file):
                                outfile = open(new_file, 'wb')
                                outfile.write(zf.read(origname))
                                outfile.close()
                                # it's not allowed to zip a zip file so it is dropped
                                if zipfile.is_zipfile(new_file):
                                    os.unlink(new_file)
                                else:
                                    valid_name = True
                                    _addLogEntry(request, 'ATTNEW', pagename, finalname)

                if valid_name:
                    msg = _("Attachment '%(filename)s' unzipped.") % {'filename': filename}
                else:
                    msg = _("Attachment '%(filename)s' not unzipped because the "
                            "files are too big, .zip files only, exist already or "
                            "reside in folders.") % {'filename': filename}
        else:
            msg = _('The file %(filename)s is not a .zip file.') % {'filename': filename}

    upload_form(pagename, request, msg=wikiutil.escape(msg))

def send_viewfile(pagename, request):
    _ = request.getText
    fmt = request.html_formatter

    filename, fpath = _access_file(pagename, request)
    if not filename:
        return

    request.write('<h2>' + _("Attachment '%(filename)s'") % {'filename': filename} + '</h2>')
    # show a download link above the content
    label = _('Download')
    link = (fmt.url(1, getAttachUrl(pagename, filename, request, do='get')) +
            fmt.text(label) +
            fmt.url(0))
    request.write('%s<br><br>' % link)

    mt = wikiutil.MimeType(filename=filename)
    if mt.major == 'image':
        request.write('<img src="%s" alt="%s">' % (
            getAttachUrl(pagename, filename, request, escaped=1),
            wikiutil.escape(filename, 1)))
        return
    elif mt.major == 'text':
        ext = os.path.splitext(filename)[1]
        Parser = wikiutil.getParserForExtension(request.cfg, ext)
        if Parser is not None:
            try:
                content = file(fpath, 'r').read()
                content = wikiutil.decodeUnknownInput(content)
                colorizer = Parser(content, request, filename=filename)
                colorizer.format(request.formatter)
                return
            except IOError:
                pass


        request.write(request.formatter.preformatted(1))
        # If we have text but no colorizing parser we try to decode file contents.
        content = open(fpath, 'r').read()
        content = wikiutil.decodeUnknownInput(content)
        content = wikiutil.escape(content)
        request.write(request.formatter.text(content))
        request.write(request.formatter.preformatted(0))
        return

    package = packages.ZipPackage(request, fpath)
    if package.isPackage():
        request.write("<pre><b>%s</b>\n%s</pre>" % (_("Package script:"), wikiutil.escape(package.getScript())))
        return

    if zipfile.is_zipfile(fpath) and mt.minor == 'zip':
        zf = zipfile.ZipFile(fpath, mode='r')
        request.write("<pre>%-46s %19s %12s\n" % (_("File Name"), _("Modified")+" "*5, _("Size")))
        for zinfo in zf.filelist:
            date = "%d-%02d-%02d %02d:%02d:%02d" % zinfo.date_time
            request.write(wikiutil.escape("%-46s %s %12d\n" % (zinfo.filename, date, zinfo.file_size)))
        request.write("</pre>")
        return

    # reuse class tmp from Despam to define macro
    from MoinMoin.action.Despam import tmp
    macro = tmp()
    macro.request = request
    macro.formatter = request.html_formatter

    # use EmbedObject to view valid mime types
    from MoinMoin.macro.EmbedObject import EmbedObject
    if mt is None:
        request.write('<p>' + _("Unknown file type, cannot display this attachment inline.") + '</p>')
        link = (fmt.url(1, getAttachUrl(pagename, filename, request)) +
                fmt.text(filename) +
                fmt.url(0))
        request.write('For using an external program follow this link %s' % link)
        return

    url = getAttachUrl(pagename, filename, request, escaped=1)

    request.write(request.formatter.rawHTML(EmbedObject.embed(EmbedObject(macro, wikiutil.escape(filename)), mt, url)))
    return


def view_file(pagename, request):
    _ = request.getText

    filename, fpath = _access_file(pagename, request)
    if not filename:
        return

    # send header & title
    request.emit_http_headers()
    # Use user interface language for this generated page
    request.setContentLanguage(request.lang)
    title = _('attachment:%(filename)s of %(pagename)s') % {
        'filename': filename, 'pagename': pagename}
    request.theme.send_title(title, pagename=pagename)

    # send body
    request.write(request.formatter.startContent())
    send_viewfile(pagename, request)
    send_uploadform(pagename, request)
    request.write(request.formatter.endContent())

    request.theme.send_footer(pagename)
    request.theme.send_closing_html()

#############################################################################
### File attachment administration
#############################################################################

def do_admin_browser(request):
    """ Browser for SystemAdmin macro.
    """
    from MoinMoin.util.dataset import TupleDataset, Column
    _ = request.getText

    data = TupleDataset()
    data.columns = [
        Column('page', label=('Page')),
        Column('file', label=('Filename')),
        Column('size', label=_('Size'), align='right'),
        #Column('action', label=_('Action')),
    ]

    # iterate over pages that might have attachments
    pages = request.rootpage.getPageList()
    for pagename in pages:
        # check for attachments directory
        page_dir = getAttachDir(request, pagename)
        if os.path.isdir(page_dir):
            # iterate over files of the page
            files = os.listdir(page_dir)
            for filename in files:
                filepath = os.path.join(page_dir, filename)
                data.addRow((
                    Page(request, pagename).link_to(request, querystr="action=AttachFile"),
                    wikiutil.escape(filename.decode(config.charset)),
                    os.path.getsize(filepath),
                    # '',
                ))

    if data:
        from MoinMoin.widget.browser import DataBrowserWidget

        browser = DataBrowserWidget(request)
        browser.setData(data)
        return browser.toHTML()

    return ''

