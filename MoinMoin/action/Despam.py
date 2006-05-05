# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Despam action
    
    Mass revert changes done by some specific author / bot.

    @copyright: 2005 by ???, Thomas Waldmann
    @license: GNU GPL, see COPYING for details.
"""

import time

from MoinMoin.logfile import editlog
from MoinMoin.util.dataset import TupleDataset, Column
from MoinMoin.widget.browser import DataBrowserWidget
from MoinMoin import wikiutil, Page, PageEditor
from MoinMoin.macro import RecentChanges
from MoinMoin.formatter.text_html import Formatter

def show_editors(request, pagename, timestamp):
    _ =  request.getText
    
    timestamp = int(timestamp * 1000000)
    log = editlog.EditLog(request)
    editors = {}
    pages = {}
    for line in log.reverse():
        if line.ed_time_usecs < timestamp:
            break
        
        if not request.user.may.read(line.pagename):
            continue
        
        editor = line.getEditor(request)
        if not line.pagename in pages:
            pages[line.pagename] = 1
            editors[editor] = editors.get(editor, 0) + 1
            
    editors = [(nr, editor) for editor, nr in editors.iteritems()]
    editors.sort()

    pg = Page.Page(request, pagename)

    dataset = TupleDataset()
    dataset.columns = [Column('editor', label=_("Editor"), align='left'),
                       Column('pages', label=_("Pages"), align='right'),
                       Column('link', label='', align='left')]
    for nr, editor in editors:
        dataset.addRow((editor, unicode(nr), pg.link_to(request, text=_("Select Author"), querystr="action=Despam&editor=%s" % wikiutil.url_quote_plus(editor))))
    
    table = DataBrowserWidget(request)
    table.setData(dataset)
    table.render()

class tmp:
    pass

def show_pages(request, pagename, editor, timestamp):
    _ =  request.getText
    
    timestamp = int(timestamp * 1000000)
    log = editlog.EditLog(request)
    lines = []
    pages = {}
    #  mimic macro object for use of RecentChanges subfunctions
    macro = tmp()
    macro.request = request
    macro.formatter = Formatter(request)

    request.write("<table>")
    for line in log.reverse():
        if line.ed_time_usecs < timestamp:
            break
        
        if not request.user.may.read(line.pagename):
            continue

        if not line.pagename in pages:
            pages[line.pagename] = 1
            if line.getEditor(request) == editor:
                line.time_tuple = request.user.getTime(wikiutil.version2timestamp(line.ed_time_usecs))
                request.write(RecentChanges.format_page_edits(macro, [line], timestamp))

    request.write('''
</table>
<p>
<form method="post" action="%s/%s">
<input type="hidden" name="action" value="Despam">
<input type="hidden" name="editor" value="%s">
<input type="submit" name="ok" value="%s">
</form>
</p>
''' % (request.getScriptname(), wikiutil.quoteWikinameURL(pagename),
       wikiutil.url_quote(editor), _("Revert all!")))

def revert_page(request, pagename, editor):
    if not request.user.may.revert(pagename):
        return 

    log = editlog.EditLog(request, rootpagename=pagename)

    first = True
    rev = u"00000000"
    for line in log.reverse():
        if first:
            first = False
            if line.getEditor(request) != editor:
                return
        else:
            if line.getEditor(request) != editor:
                rev = line.rev
                break

    if rev == u"00000000": # page created by spammer 
        comment = u"Page deleted by Despam action"
        pg = PageEditor.PageEditor(request, pagename, do_editor_backup=0)
        try:
            savemsg = pg.deletePage(comment)
        except pg.SaveError, msg:
            savemsg = unicode(msg)
    else: # page edited by spammer
        oldpg = Page.Page(request, pagename, rev=int(rev))
        pg = PageEditor.PageEditor(request, pagename, do_editor_backup=0)
        try:
            savemsg = pg.saveText(oldpg.get_raw_body(), 0, extra=rev, action="SAVE/REVERT")
        except pg.SaveError, msg:
            savemsg = unicode(msg)
    return savemsg
    
def revert_pages(request, editor, timestamp):
    _ =  request.getText

    editor = wikiutil.url_unquote(editor, want_unicode=False)
    timestamp = int(timestamp * 1000000)
    log = editlog.EditLog(request)
    pages = {}
    revertpages = []
    for line in log.reverse():
        if line.ed_time_usecs < timestamp:
            break

        if not request.user.may.read(line.pagename):
            continue

        if not line.pagename in pages:
            pages[line.pagename] = 1
            if line.getEditor(request) == editor:
                revertpages.append(line.pagename)

    request.write("Debug: Pages to revert:<br>%s" % "<br>".join(revertpages))
    for pagename in revertpages:
        request.write("Debug: Begin reverting %s ...<br>" % pagename)
        msg = revert_page(request, pagename, editor)
        if msg:
            request.write("<p>%s: %s</p>" % (
                Page.Page(request, pagename).link_to(request), msg))
        request.write("Debug: Finished reverting %s.<br>" % pagename)

def execute(pagename, request):
    _ = request.getText
    # be extra paranoid in dangerous actions
    actname = __name__.split('.')[-1]
    if actname in request.cfg.actions_excluded or \
       not request.user.isSuperUser():
        return Page.Page(request, pagename).send_page(request,
            msg = _('You are not allowed to use this action.'))

    editor = request.form.get('editor', [None])[0]
    timestamp = time.time() - 24 * 3600
       # request.form.get('timestamp', [None])[0]
    ok = request.form.get('ok', [0])[0]

    request.http_headers()
    request.theme.send_title("Despam", pagename=pagename)    
    # Start content (important for RTL support)
    request.write(request.formatter.startContent("content"))
    
    if ok:
        revert_pages(request, editor, timestamp)
    elif editor:
        show_pages(request, pagename, editor, timestamp)
    else:
        show_editors(request, pagename, timestamp)

    # End content and send footer
    request.write(request.formatter.endContent())
    request.theme.send_footer(pagename)
    request.theme.send_closing_html()

