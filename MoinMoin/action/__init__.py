# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Action Implementation

    Actions are triggered by the user clicking on special links on the page
    (e.g. the "edit" link). The name of the action is passed in the "action"
    CGI parameter.

    The sub-package "MoinMoin.action" contains external actions, you can
    place your own extensions there (similar to extension macros). User
    actions that start with a capital letter will be displayed in a list
    at the bottom of each page.

    User actions starting with a lowercase letter can be used to work
    together with a user macro; those actions a likely to work only if
    invoked BY that macro, and are thus hidden from the user interface.
    
    Additionally to the usual stuff, we provide an ActionBase class here with
    some of the usual base functionality for an action, like checking
    actions_excluded, making and checking tickets, rendering some form,
    displaying errors and doing stuff after an action.
    
    @copyright: 2000-2004 by Jürgen Hermann <jh@web.de>,
                2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.util import pysupport
from MoinMoin import wikiutil
from MoinMoin.Page import Page

# create a list of extension actions from the subpackage directory
extension_actions = pysupport.getPackageModules(__file__)
modules = extension_actions

class ActionBase:
    """ action base class with some generic stuff to inherit

    Note: the action name is the class name of the derived class
    """
    def __init__(self, pagename, request):
        self.request = request
        self.form = request.form
        self.cfg = request.cfg
        self._ = _ = request.getText
        self.pagename = pagename
        self.actionname = self.__class__.__name__
        self.use_ticket = False # set this to True if you want to use a ticket
        self.user_html = '''Just checking.''' # html fragment for make_form
        self.form_cancel = "cancel" # form key for cancelling action
        self.form_cancel_label = _("Cancel") # label for the cancel button
        self.form_trigger = "doit" # form key for triggering action (override with e.g. 'rename')
        self.form_trigger_label = _("Do it.") # label for the trigger button
        self.page = Page(request, pagename)
        self.error = ''

    # CHECKS -----------------------------------------------------------------
    def is_excluded(self):
        """ Return True if action is excluded """
        return self.actionname in self.cfg.actions_excluded

    def is_allowed(self):
        """ Return True if action is allowed (by ACL) """
        return True

    def check_condition(self):
        """ Check if some other condition is not allowing us to do that action,
            return error msg or None if there is no problem.

            You can use this to e.g. check if a page exists.
        """
        return None

    def ticket_ok(self):
        """ Return True if we check for tickets and there is some valid ticket
            in the form data or if we don't check for tickets at all.
            Use this to make sure someone really used the web interface.
        """
        if not self.use_ticket:
            return True
        # Require a valid ticket. Make outside attacks harder by
        # requiring two full HTTP transactions
        ticket = self.form.get('ticket', [''])[0]
        return wikiutil.checkTicket(ticket)

    # UI ---------------------------------------------------------------------
    def get_form_html(self, buttons_html):
        """ Override this to assemble the inner part of the form,
            for convenience we give him some pre-assembled html for the buttons.
        """
        _ = self._
        prompt = _("Execute action %(actionname)s?") % {'actionname': self.actionname}
        return "<p>%s</p>%s" % (prompt, buttons_html)

    def make_buttons(self):
        """ return a list of form buttons for the action form """
        return [
            (self.form_trigger, self.form_trigger_label),
            (self.form_cancel, self.form_cancel_label),
        ]

    def make_form(self):
        """ Make some form html for later display.

        The form might contain an error that happened when trying to do the action.
        """
        from MoinMoin.widget.dialog import Dialog
        _ = self._

        if self.error:
            error_html = u'<p class="error">%s</p>\n' % self.error
        else:
            error_html = ''

        buttons = self.make_buttons()
        buttons_html = []
        for button in buttons:
            buttons_html.append('<input type="submit" name="%s" value="%s">' % button)
        buttons_html = "".join(buttons_html)

        if self.use_ticket:
            ticket_html = '<input type="hidden" name="ticket" value="%s">' % wikiutil.createTicket()
        else:
            ticket_html = ''

        d = {
            'error_html': error_html,
            'actionname': self.actionname,
            'pagename': self.pagename,
            'ticket_html': ticket_html,
            'user_html': self.get_form_html(buttons_html),
        }

        form_html = '''
%(error_html)s
<form method="post" action="">
<input type="hidden" name="action" value="%(actionname)s">
%(ticket_html)s
%(user_html)s
</form>''' % d

        return Dialog(self.request, content=form_html)

    def render_msg(self, msg):
        """ Called to display some message (can also be the action form) """
        self.page.send_page(self.request, msg=msg)

    def render_success(self, msg):
        """ Called to display some message when the action succeeded """
        self.page.send_page(self.request, msg=msg)

    def render_cancel(self):
        """ Called when user has hit the cancel button """
        self.page.send_page(self.request) # we don't tell user he has hit cancel :)

    def render(self):
        """ Render action - this is the main function called by action's
            execute() function.

            We usually render a form here, check for posted forms, etc.
        """
        _ = self._
        form = self.form

        if form.has_key(self.form_cancel):
            self.render_cancel()
            return

        # Validate allowance, user rights and other conditions.
        error = None
        if self.is_excluded():
            error = _('Action %(actionname)s is excluded in this wiki!') % {'actionname': self.actionname }
        elif not self.is_allowed():
            error = _('You are not allowed to use action %(actionname)s on this page!') % {'actionname': self.actionname }
        if error is None:
            error = self.check_condition()
        if error:
            self.render_msg(error)
        elif form.has_key(self.form_trigger): # user hit the trigger button
            if self.ticket_ok():
                success, self.error = self.do_action()
            else:
                success = False
                self.error = _('Please use the interactive user interface to use action %(actionname)s!') % {'actionname': self.actionname }
            self.do_action_finish(success)
        else:
            # Return a new form
            self.render_msg(self.make_form())

    # Executing the action ---------------------------------------------------
    def do_action(self):
        """ Do the action and either return error msg or None, if there was no error. """
        return None

    # AFTER the action -------------------------------------------------------
    def do_action_finish(self, success):
        """ Override this to handle success or failure (with error in self.error) of your action.
        """
        if success:
            self.render_success(self.error)
        else:
            self.render_msg(self.make_form()) # display the form again

# from wikiaction.py ---------------------------------------------------------

import os, re, time
from MoinMoin import config, util
from MoinMoin.logfile import editlog

#############################################################################
### Misc Actions
#############################################################################

def do_raw(pagename, request):
    """ send raw content of a page (e.g. wiki markup) """
    if not request.user.may.read(pagename):
        Page(request, pagename).send_page(request)
    else:
        try:
            rev = int(request.form.get('rev', [0])[0])
        except StandardError:
            rev = 0
        Page(request, pagename, rev=rev).send_raw()

def do_show(pagename, request, count_hit=1, cacheable=1):
    """ show a page, either current revision or the revision given by rev form value.
        if count_hit is non-zero, we count the request for statistics.
    """
    # We must check if the current page has different ACLs.
    if not request.user.may.read(pagename):
        Page(request, pagename).send_page(request)
    else:
        mimetype = request.form.get('mimetype', [u"text/html"])[0]
        try:
            rev = int(request.form.get('rev', [0])[0])
        except StandardError:
            rev = 0
        if rev == 0:
            request.cacheable = cacheable
        Page(request, pagename, rev=rev, formatter=mimetype).send_page(request, count_hit=count_hit)

def do_format(pagename, request):
    """ send a page using a specific formatter given by mimetype form key.
        Since 5.5.2006 this functionality is also done by do_show, but do_format
        has a default of text/plain when no format is given.
        It also does not count in statistics and also does not set the cacheable flag.
        DEPRECATED: remove this action when we don't need it any more for compatibility.
    """
    if not request.form.has_key('mimetype'):
        request.form['mimetype'] = [u"text/plain"]
    do_show(pagename, request, count_hit=0, cacheable=0)

def do_content(pagename, request):
    """ same as do_show, but we only show the content """
    request.http_headers()
    page = Page(request, pagename)
    request.write('<!-- Transclusion of %s -->' % request.getQualifiedURL(page.url(request)))
    page.send_page(request, count_hit=0, content_only=1)

def do_print(pagename, request):
    """ same as do_show, but send_page will notice the print mode """
    do_show(pagename, request)

def do_recall(pagename, request):
    """ same as do_show, but never caches and never counts hits """
    do_show(pagename, request, count_hit=0, cacheable=0)

def do_refresh(pagename, request):
    """ Handle refresh action """
    # Without arguments, refresh action will refresh the page text_html cache.
    arena = request.form.get('arena', ['Page.py'])[0]
    if arena == 'Page.py':
        arena = Page(request, pagename)
    key = request.form.get('key', ['text_html'])[0]

    # Remove cache entry (if exists), and send the page
    from MoinMoin import caching
    caching.CacheEntry(request, arena, key, scope='item').remove()
    caching.CacheEntry(request, arena, "pagelinks", scope='item').remove()
    do_show(pagename, request)

def do_revert(pagename, request):
    """ restore another revision of a page as a new current revision """
    from MoinMoin.PageEditor import PageEditor
    _ = request.getText

    if not request.user.may.revert(pagename):
        return Page(request, pagename).send_page(request,
            msg=_('You are not allowed to revert this page!'))

    rev = int(request.form['rev'][0])
    revstr = '%08d' % rev
    oldpg = Page(request, pagename, rev=rev)
    pg = PageEditor(request, pagename)

    try:
        savemsg = pg.saveText(oldpg.get_raw_body(), 0, extra=revstr,
                              action="SAVE/REVERT")
    except pg.SaveError, msg:
        # msg contain a unicode string
        savemsg = unicode(msg)
    request.reset()
    pg.send_page(request, msg=savemsg)
    return None

def do_edit(pagename, request):
    """ edit a page """
    _ = request.getText

    if not request.user.may.write(pagename):
        Page(request, pagename).send_page(request,
            msg=_('You are not allowed to edit this page.'))
        return

    valideditors = ['text', 'gui', ]
    editor = ''
    if request.user.valid:
        editor = request.user.editor_default
    if editor not in valideditors:
        editor = request.cfg.editor_default

    editorparam = request.form.get('editor', [editor])[0]
    if editorparam == "guipossible":
        lasteditor = editor
    elif editorparam == "textonly":
        editor = lasteditor = 'text'
    else:
        editor = lasteditor = editorparam

    if request.cfg.editor_force:
        editor = request.cfg.editor_default

    # if it is still nothing valid, we just use the text editor
    if editor not in valideditors:
        editor = 'text'

    savetext = request.form.get('savetext', [None])[0]
    rev = int(request.form.get('rev', ['0'])[0])
    comment = request.form.get('comment', [u''])[0]
    category = request.form.get('category', [None])[0]
    rstrip = int(request.form.get('rstrip', ['0'])[0])
    trivial = int(request.form.get('trivial', ['0'])[0])

    if request.form.has_key('button_switch'):
        if editor == 'text':
            editor = 'gui'
        else: # 'gui'
            editor = 'text'

    # load right editor class
    if editor == 'gui':
        from MoinMoin.PageGraphicalEditor import PageGraphicalEditor
        pg = PageGraphicalEditor(request, pagename)
    else: # 'text'
        from MoinMoin.PageEditor import PageEditor
        pg = PageEditor(request, pagename)

    # is invoked without savetext start editing
    if savetext is None:
        pg.sendEditor()
        return

    # did user hit cancel button?
    cancelled = request.form.has_key('button_cancel')

    # convert input from Graphical editor
    from MoinMoin.converter.text_html_text_moin_wiki import convert, ConvertError
    try:
        if lasteditor == 'gui':
            savetext = convert(request, pagename, savetext)

        # IMPORTANT: normalize text from the form. This should be done in
        # one place before we manipulate the text.
        savetext = pg.normalizeText(savetext, stripspaces=rstrip)
    except ConvertError:
        # we don't want to throw an exception if user cancelled anyway
        if not cancelled:
            raise

    if cancelled:
        pg.sendCancel(savetext or "", rev)
        return

    comment = wikiutil.clean_comment(comment)

    # Add category

    # TODO: this code does not work with extended links, and is doing
    # things behind your back, and in general not needed. Either we have
    # a full interface for categories (add, delete) or just add them by
    # markup.

    if category and category != _('<No addition>', formatted=False): # opera 8.5 needs this
        # strip trailing whitespace
        savetext = savetext.rstrip()

        # Add category separator if last non-empty line contains
        # non-categories.
        lines = filter(None, savetext.splitlines())
        if lines:

            #TODO: this code is broken, will not work for extended links
            #categories, e.g ["category hebrew"]
            categories = lines[-1].split()

            if categories:
                confirmed = wikiutil.filterCategoryPages(request, categories)
                if len(confirmed) < len(categories):
                    # This was not a categories line, add separator
                    savetext += u'\n----\n'

        # Add new category
        if savetext and savetext[-1] != u'\n':
            savetext += ' '
        savetext += category + u'\n' # Should end with newline!

    # Preview, spellcheck or spellcheck add new words
    if (request.form.has_key('button_preview') or
        request.form.has_key('button_spellcheck') or
        request.form.has_key('button_newwords')):
        pg.sendEditor(preview=savetext, comment=comment)

    # Preview with mode switch
    elif request.form.has_key('button_switch'):
        pg.sendEditor(preview=savetext, comment=comment, staytop=1)

    # Save new text
    else:
        try:
            still_conflict = r"/!\ '''Edit conflict" in savetext
            pg.setConflict(still_conflict)
            savemsg = pg.saveText(savetext, rev, trivial=trivial, comment=comment)
        except pg.EditConflict, e:
            msg = e.message

            # Handle conflict and send editor
            pg.set_raw_body(savetext, modified=1)

            pg.mergeEditConflict(rev)
            # We don't send preview when we do merge conflict
            pg.sendEditor(msg=msg, comment=comment)
            return

        except pg.SaveError, msg:
            # msg contain a unicode string
            savemsg = unicode(msg)

        # Send new page after save or after unsuccessful conflict merge.
        request.reset()
        backto = request.form.get('backto', [None])[0]
        if backto:
            pg = Page(request, backto)

        pg.send_page(request, msg=savemsg)

def do_goto(pagename, request):
    """ redirect to another page """
    target = request.form.get('target', [''])[0]
    request.http_redirect(Page(request, target).url(request))

def do_diff(pagename, request):
    """ Handle "action=diff"
        checking for either a "rev=formerrevision" parameter
        or rev1 and rev2 parameters
    """
    if not request.user.may.read(pagename):
        Page(request, pagename).send_page(request)
        return

    try:
        date = request.form['date'][0]
        try:
            date = long(date) # must be long for py 2.2.x
        except StandardError:
            date = 0
    except KeyError:
        date = 0

    try:
        rev1 = int(request.form.get('rev1', [-1])[0])
    except StandardError:
        rev1 = 0
    try:
        rev2 = int(request.form.get('rev2', [0])[0])
    except StandardError:
        rev1 = 0

    if rev1 == -1 and rev2 == 0:
        try:
            rev1 = int(request.form.get('rev', [-1])[0])
        except StandardError:
            rev1 = -1

    # spacing flag?
    ignorews = int(request.form.get('ignorews', [0])[0])

    _ = request.getText

    # get a list of old revisions, and back out if none are available
    currentpage = Page(request, pagename)
    revisions = currentpage.getRevList()
    if len(revisions) < 2:
        currentpage.send_page(request, msg=_("No older revisions available!"))
        return

    if date: # this is how we get called from RecentChanges
        rev1 = 0
        log = editlog.EditLog(request, rootpagename=pagename)
        for line in log.reverse():
            if date >= line.ed_time_usecs and int(line.rev) != 99999999:
                rev1 = int(line.rev)
                break
        else:
            rev1 = 1
        rev2 = 0

    # Start output
    # This action generate content in the user language
    request.setContentLanguage(request.lang)

    request.http_headers()
    request.theme.send_title(_('Diff for "%s"') % (pagename,), pagename=pagename, allow_doubleclick=1)

    if rev1 > 0 and rev2 > 0 and rev1 > rev2 or rev1 == 0 and rev2 > 0:
        rev1, rev2 = rev2, rev1

    oldrev1, oldcount1 = None, 0
    oldrev2, oldcount2 = None, 0

    # get the filename of the version to compare to
    edit_count = 0
    for rev in revisions:
        edit_count += 1
        if rev <= rev1:
            oldrev1, oldcount1 = rev, edit_count
        if rev2 and rev >= rev2:
            oldrev2, oldcount2 = rev, edit_count
        if oldrev1 and oldrev2 or oldrev1 and not rev2:
            break

    if rev1 == -1:
        oldpage = Page(request, pagename, rev=revisions[1])
        oldcount1 -= 1
    elif rev1 == 0:
        oldpage = currentpage
        # oldcount1 is still on init value 0
    else:
        if oldrev1:
            oldpage = Page(request, pagename, rev=oldrev1)
        else:
            oldpage = Page(request, "$EmptyPage$") # hack
            oldpage.set_raw_body("")    # avoid loading from disk
            oldrev1 = 0 # XXX

    if rev2 == 0:
        newpage = currentpage
        # oldcount2 is still on init value 0
    else:
        if oldrev2:
            newpage = Page(request, pagename, rev=oldrev2)
        else:
            newpage = Page(request, "$EmptyPage$") # hack
            newpage.set_raw_body("")    # avoid loading from disk
            oldrev2 = 0 # XXX

    edit_count = abs(oldcount1 - oldcount2)

    # this should use the formatter, but there is none?
    request.write('<div id="content">\n') # start content div
    request.write('<p class="diff-header">')
    request.write(_('Differences between revisions %d and %d') % (oldpage.get_real_rev(), newpage.get_real_rev()))
    if edit_count > 1:
        request.write(' ' + _('(spanning %d versions)') % (edit_count,))
    request.write('</p>')

    if request.user.show_fancy_diff:
        from MoinMoin.util.diff import diff
        request.write(diff(request, oldpage.get_raw_body(), newpage.get_raw_body()))
        newpage.send_page(request, count_hit=0, content_only=1, content_id="content-below-diff")
    else:
        lines = wikiutil.linediff(oldpage.getlines(), newpage.getlines())
        if not lines:
            msg = _("No differences found!")
            if edit_count > 1:
                msg = msg + '<p>' + _('The page was saved %(count)d times, though!') % {
                    'count': edit_count}
            request.write(msg)
        else:
            if ignorews:
                request.write(_('(ignoring whitespace)') + '<br>')
            else:
                qstr = 'action=diff&ignorews=1'
                if rev1: qstr = '%s&rev1=%s' % (qstr, rev1)
                if rev2: qstr = '%s&rev2=%s' % (qstr, rev2)
                request.write(Page(request, pagename).link_to(request,
                    text=_('Ignore changes in the amount of whitespace'),
                    querystr=qstr, rel='nofollow') + '<p>')

            request.write('<pre>')
            for line in lines:
                if line[0] == "@":
                    request.write('<hr>')
                request.write(wikiutil.escape(line)+'\n')
            request.write('</pre>')

    request.write('</div>\n') # end content div
    request.theme.send_footer(pagename)
    request.theme.send_closing_html()

def do_info(pagename, request):
    """ show misc. infos about a page """
    if not request.user.may.read(pagename):
        Page(request, pagename).send_page(request)
        return

    def general(page, pagename, request):
        _ = request.getText

        request.write('<h2>%s</h2>\n' % _('General Information'))

        # show page size
        request.write(("<p>%s</p>" % _("Page size: %d")) % page.size())

        # show SHA digest fingerprint
        import sha
        digest = sha.new(page.get_raw_body().encode(config.charset)).hexdigest().upper()
        request.write('<p>%(label)s <tt>%(value)s</tt></p>' % {
            'label': _("SHA digest of this page's content is:"),
            'value': digest,
            })

        # show attachments (if allowed)
        attachment_info = getHandler(request, 'AttachFile', 'info')
        if attachment_info:
            request.write(attachment_info(pagename, request))

        # show subscribers
        subscribers = page.getSubscribers(request, include_self=1, return_users=1)
        if subscribers:
            request.write('<p>', _('The following users subscribed to this page:'))
            for lang in subscribers.keys():
                request.write('<br>[%s] ' % lang)
                for user in subscribers[lang]:
                    # do NOT disclose email addr, only WikiName
                    userhomepage = Page(request, user.name)
                    if userhomepage.exists():
                        request.write(userhomepage.link_to(request) + ' ')
                    else:
                        request.write(user.name + ' ')
            request.write('</p>')

        # show links
        links = page.getPageLinks(request)
        if links:
            request.write('<p>', _('This page links to the following pages:'), '<br>')
            for linkedpage in links:
                request.write("%s%s " % (Page(request, linkedpage).link_to(request), ",."[linkedpage == links[-1]]))
            request.write("</p>")

    def history(page, pagename, request):
        # show history as default
        _ = request.getText

        # open log for this page
        from MoinMoin.util.dataset import TupleDataset, Column

        history = TupleDataset()
        history.columns = [
            Column('rev', label='#', align='right'),
            Column('mtime', label=_('Date'), align='right'),
            Column('size', label=_('Size'), align='right'),
            Column('diff', label='<input type="submit" value="%s">' % (_("Diff"))),
            Column('editor', label=_('Editor'), hidden=not request.cfg.show_names),
            Column('comment', label=_('Comment')),
            Column('action', label=_('Action')),
            ]

        # generate history list
        revisions = page.getRevList()
        versions = len(revisions)

        may_revert = request.user.may.revert(pagename)

        # read in the complete log of this page
        log = editlog.EditLog(request, rootpagename=pagename)
        count = 0
        for line in log.reverse():
            rev = int(line.rev)
            actions = ""
            if line.action in ['SAVE', 'SAVENEW', 'SAVE/REVERT', ]:
                size = page.size(rev=rev)
                if count == 0: # latest page
                    actions = '%s&nbsp;%s' % (actions, page.link_to(request,
                        text=_('view'),
                        querystr=''))
                    actions = '%s&nbsp;%s' % (actions, page.link_to(request,
                        text=_('raw'),
                        querystr='action=raw', rel='nofollow'))
                    actions = '%s&nbsp;%s' % (actions, page.link_to(request,
                        text=_('print'),
                        querystr='action=print', rel='nofollow'))
                else:
                    actions = '%s&nbsp;%s' % (actions, page.link_to(request,
                        text=_('view'),
                        querystr='action=recall&rev=%d' % rev, rel='nofollow'))
                    actions = '%s&nbsp;%s' % (actions, page.link_to(request,
                        text=_('raw'),
                        querystr='action=raw&rev=%d' % rev, rel='nofollow'))
                    actions = '%s&nbsp;%s' % (actions, page.link_to(request,
                        text=_('print'),
                        querystr='action=print&rev=%d' % rev, rel='nofollow'))
                    if may_revert and size: # you can only revert to nonempty revisions
                        actions = '%s&nbsp;%s' % (actions, page.link_to(request,
                            text=_('revert'),
                            querystr='action=revert&rev=%d' % rev, rel='nofollow'))
                if count == 0:
                    rchecked = ' checked="checked"'
                    lchecked = ''
                elif count == 1:
                    lchecked = ' checked="checked"'
                    rchecked = ''
                else:
                    lchecked = rchecked = ''
                diff = '<input type="radio" name="rev1" value="%d"%s><input type="radio" name="rev2" value="%d"%s>' % (rev, lchecked, rev, rchecked)
                comment = line.comment
                if not comment and '/REVERT' in line.action:
                        comment = _("Revert to revision %(rev)d.") % {'rev': int(line.extra)}
            else: # ATT*
                rev = '-'
                diff = '-'

                filename = wikiutil.url_unquote(line.extra)
                comment = "%s: %s %s" % (line.action, filename, line.comment)
                size = 0
                if line.action != 'ATTDEL':
                    from MoinMoin.action import AttachFile
                    page_dir = AttachFile.getAttachDir(request, pagename)
                    filepath = os.path.join(page_dir, filename)
                    try:
                        # FIXME, wrong path on non-std names
                        size = os.path.getsize(filepath)
                    except:
                        pass
                    if line.action == 'ATTNEW':
                        actions = '%s&nbsp;%s' % (actions, page.link_to(request,
                            text=_('view'),
                            querystr='action=AttachFile&do=view&target=%s' % filename, rel='nofollow'))
                    elif line.action == 'ATTDRW':
                        actions = '%s&nbsp;%s' % (actions, page.link_to(request,
                            text=_('edit'),
                            querystr='action=AttachFile&drawing=%s' % filename.replace(".draw", ""), rel='nofollow'))

                    actions = '%s&nbsp;%s' % (actions, page.link_to(request,
                        text=_('get'),
                        querystr='action=AttachFile&do=get&target=%s' % filename, rel='nofollow'))
                    actions = '%s&nbsp;%s' % (actions, page.link_to(request,
                        text=_('del'),
                        querystr='action=AttachFile&do=del&target=%s' % filename, rel='nofollow'))
                    # XXX use?: wikiutil.escape(filename)

            history.addRow((
                rev,
                request.user.getFormattedDateTime(wikiutil.version2timestamp(line.ed_time_usecs)),
                str(size),
                diff,
                line.getEditor(request) or _("N/A"),
                wikiutil.escape(comment) or '&nbsp;',
                actions,
            ))
            count += 1
            if count >= 100:
                break

        # print version history
        from MoinMoin.widget.browser import DataBrowserWidget

        request.write('<h2>%s</h2>\n' % _('Revision History'))

        if not count: # there was no entry in logfile
            request.write(_('No log entries found.'))
            return

        # TODO: this form activates revert, which should use POST, but
        # other actions should use get. Maybe we should put the revert
        # into the page view itself, and not in this form.
        request.write('<form method="GET" action="">\n')
        request.write('<div id="page-history">\n')
        request.write('<input type="hidden" name="action" value="diff">\n')

        history_table = DataBrowserWidget(request)
        history_table.setData(history)
        history_table.render()
        request.write('</div>\n')
        request.write('</form>\n')

    # main function
    _ = request.getText
    page = Page(request, pagename)
    qpagename = wikiutil.quoteWikinameURL(pagename)
    title = page.split_title(request)

    request.http_headers()

    # This action uses page or wiki language TODO: currently
    # page.language is broken and not available now, when we fix it,
    # this will be automatically fixed.
    lang = page.language or request.cfg.language_default
    request.setContentLanguage(lang)

    request.theme.send_title(_('Info for "%s"') % (title,), pagename=pagename)

    historylink = wikiutil.link_tag(request, '%s?action=info' % qpagename,
        _('Show "%(title)s"') % {'title': _('Revision History')}, request.formatter, rel='nofollow')
    generallink = wikiutil.link_tag(request, '%s?action=info&amp;general=1' % qpagename,
        _('Show "%(title)s"') % {'title': _('General Page Infos')}, request.formatter, rel='nofollow')
    hitcountlink = wikiutil.link_tag(request, '%s?action=info&amp;hitcounts=1' % qpagename,
        _('Show chart "%(title)s"') % {'title': _('Page hits and edits')}, request.formatter, rel='nofollow')

    request.write('<div id="content">\n') # start content div
    request.write("<p>[%s]  [%s]  [%s]</p>" % (historylink, generallink, hitcountlink))

    show_hitcounts = int(request.form.get('hitcounts', [0])[0]) != 0
    show_general = int(request.form.get('general', [0])[0]) != 0

    if show_hitcounts:
        from MoinMoin.stats import hitcounts
        request.write(hitcounts.linkto(pagename, request, 'page=' + wikiutil.url_quote_plus(pagename)))
    elif show_general:
        general(page, pagename, request)
    else:
        history(page, pagename, request)

    request.write('</div>\n') # end content div
    request.theme.send_footer(pagename)
    request.theme.send_closing_html()

def do_quicklink(pagename, request):
    """ Add the current wiki page to the user quicklinks 
    
    TODO: what if add or remove quicklink fail? display an error message?
    """
    _ = request.getText
    msg = None

    if not request.user.valid:
        msg = _("You must login to add a quicklink.")
    elif request.user.isQuickLinkedTo([pagename]):
        if request.user.removeQuicklink(pagename):
            msg = _('Your quicklink to this page has been removed.')
    else:
        if request.user.addQuicklink(pagename):
            msg = _('A quicklink to this page has been added for you.')

    Page(request, pagename).send_page(request, msg=msg)

def do_subscribe(pagename, request):
    """ Subscribe or unsubscribe the user to pagename
    
    TODO: what if subscribe failed? no message is displayed.
    """
    _ = request.getText
    cfg = request.cfg
    msg = None

    if not request.user.may.read(pagename):
        msg = _("You are not allowed to subscribe to a page you can't read.")

    # Check if mail is enabled
    elif not cfg.mail_enabled:
        msg = _("This wiki is not enabled for mail processing.")

    # Suggest visitors to login
    elif not request.user.valid:
        msg = _("You must log in to use subscribtions.")

    # Suggest users without email to add their email address
    elif not request.user.email:
        msg = _("Add your email address in your UserPreferences to use subscriptions.")

    elif request.user.isSubscribedTo([pagename]):
        # Try to unsubscribe
        if request.user.unsubscribe(pagename):
            msg = _('Your subscribtion to this page has been removed.')
        else:
            msg = _("Can't remove regular expression subscription!") + u' ' + \
                  _("Edit the subscription regular expressions in your "
                    "UserPreferences.")

    else:
        # Try to subscribe
        if request.user.subscribe(pagename):
            msg = _('You have been subscribed to this page.')

    Page(request, pagename).send_page(request, msg=msg)

def do_userform(pagename, request):
    """ save data posted from UserPreferences """
    from MoinMoin import userform
    savemsg = userform.savedata(request)
    Page(request, pagename).send_page(request, msg=savemsg)

def do_bookmark(pagename, request):
    """ set bookmarks (in time) for RecentChanges or delete them """
    timestamp = request.form.get('time', [None])[0]
    if timestamp is not None:
        if timestamp == 'del':
            tm = None
        else:
            try:
                tm = int(timestamp)
            except StandardError:
                tm = wikiutil.timestamp2version(time.time())
    else:
        tm = wikiutil.timestamp2version(time.time())

    if tm is None:
        request.user.delBookmark()
    else:
        request.user.setBookmark(tm)
    Page(request, pagename).send_page(request)


#############################################################################
### Special Actions
#############################################################################

def do_chart(pagename, request):
    """ Show page charts """
    _ = request.getText
    if not request.user.may.read(pagename):
        msg = _("You are not allowed to view this page.")
        return request.page.send_page(request, msg=msg)

    if not request.cfg.chart_options:
        msg = _("Charts are not available!")
        return request.page.send_page(request, msg=msg)

    chart_type = request.form.get('type', [''])[0].strip()
    if not chart_type:
        msg = _('You need to provide a chart type!')
        return request.page.send_page(request, msg=msg)

    try:
        func = pysupport.importName("MoinMoin.stats." + chart_type, 'draw')
    except (ImportError, AttributeError):
        msg = _('Bad chart type "%s"!') % chart_type
        return request.page.send_page(request, msg=msg)

    func(pagename, request)

def do_dumpform(pagename, request):
    """ dump the form data we received in this request for debugging """
    data = util.dumpFormData(request.form)

    request.http_headers()
    request.write("<html><body>%s</body></html>" % data)


#############################################################################
### Dispatching
#############################################################################

def getPlugins(request):
    """ return the path to the action plugin directory and a list of plugins there """
    dir = os.path.join(request.cfg.plugin_dir, 'action')
    plugins = []
    if os.path.isdir(dir):
        plugins = pysupport.getPackageModules(os.path.join(dir, 'dummy'))
    return dir, plugins

def getHandler(request, action, identifier="execute"):
    """ return a handler function for a given action or None """
    # check for excluded actions
    if action in request.cfg.actions_excluded:
        return None

    try:
        handler = wikiutil.importPlugin(request.cfg, "action", action, identifier)
    except wikiutil.PluginMissingError:
        handler = globals().get('do_' + action)

    return handler

