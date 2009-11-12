# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Call the GUI editor (FCKeditor)

    Same as PageEditor, but we use the HTML based GUI editor here.

    TODO:
    * see PageEditor.py

    @copyright: 2006 Bastian Blank, Florian Festi,
                2006-2007 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""
import re

from MoinMoin import PageEditor
from MoinMoin import wikiutil
from MoinMoin.Page import Page
from MoinMoin.widget import html
from MoinMoin.widget.dialog import Status
from MoinMoin.util import web
from MoinMoin.parser.text_moin_wiki import Parser as WikiParser

def execute(pagename, request):
    if not request.user.may.write(pagename):
        _ = request.getText
        request.theme.add_msg_('You are not allowed to edit this page.', "error")
        Page(request, pagename).send_page()
        return

    PageGraphicalEditor(request, pagename).sendEditor()


class PageGraphicalEditor(PageEditor.PageEditor):
    """ Same as PageEditor, but use the GUI editor (FCKeditor) """
    def word_rule(self):
        regex = re.compile(r"\(\?<![^)]*?\)")
        word_rule = regex.sub("", WikiParser.word_rule_js)
        return repr(word_rule)[1:]

    def sendEditor(self, **kw):
        """ Send the editor form page.

        @keyword preview: if given, show this text in preview mode
        @keyword staytop: don't go to #preview
        @keyword comment: comment field (when preview is true)
        """
        from MoinMoin import i18n
        from MoinMoin.action import SpellCheck

        request = self.request
        form = request.form
        _ = self._

        raw_body = ''
        msg = None
        conflict_msg = None
        edit_lock_message = None
        preview = kw.get('preview', None)
        staytop = kw.get('staytop', 0)

        # check edit permissions
        if not request.user.may.write(self.page_name):
            msg = _('You are not allowed to edit this page.')
        elif not self.isWritable():
            msg = _('Page is immutable!')
        elif self.rev:
            # Trying to edit an old version, this is not possible via
            # the web interface, but catch it just in case...
            msg = _('Cannot edit old revisions!')
        else:
            # try to acquire edit lock
            ok, edit_lock_message = self.lock.acquire()
            if not ok:
                # failed to get the lock
                if preview is not None:
                    edit_lock_message = _('The lock you held timed out. Be prepared for editing conflicts!'
                        ) + "<br>" + edit_lock_message
                else:
                    msg = edit_lock_message

        # Did one of the prechecks fail?
        if msg:
            request.theme.add_msg(msg, "error")
            self.send_page()
            return

        # Emit http_headers after checks (send_page)
        request.disableHttpCaching(level=2)

        # check if we want to load a draft
        use_draft = None
        if 'button_load_draft' in form:
            wanted_draft_timestamp = int(form.get('draft_ts', '0'))
            if wanted_draft_timestamp:
                draft = self._load_draft()
                if draft is not None:
                    draft_timestamp, draft_rev, draft_text = draft
                    if draft_timestamp == wanted_draft_timestamp:
                        use_draft = draft_text

        # Check for draft / normal / preview submit
        if use_draft is not None:
            title = _('Draft of "%(pagename)s"')
            # Propagate original revision
            rev = int(form['draft_rev'])
            self.set_raw_body(use_draft, modified=1)
            preview = use_draft
        elif preview is None:
            title = _('Edit "%(pagename)s"')
        else:
            title = _('Preview of "%(pagename)s"')
            # Propagate original revision
            rev = request.rev
            self.set_raw_body(preview, modified=1)

        # send header stuff
        lock_timeout = self.lock.timeout / 60
        lock_page = wikiutil.escape(self.page_name, quote=1)
        lock_expire = _("Your edit lock on %(lock_page)s has expired!") % {'lock_page': lock_page}
        lock_mins = _("Your edit lock on %(lock_page)s will expire in # minutes.") % {'lock_page': lock_page}
        lock_secs = _("Your edit lock on %(lock_page)s will expire in # seconds.") % {'lock_page': lock_page}

        # get request parameters
        try:
            text_rows = int(form['rows'])
        except StandardError:
            text_rows = self.cfg.edit_rows
            if request.user.valid:
                text_rows = int(request.user.edit_rows)

        if preview is not None:
            # Check for editing conflicts
            if not self.exists():
                # page does not exist, are we creating it?
                if rev:
                    conflict_msg = _('Someone else deleted this page while you were editing!')
            elif rev != self.current_rev():
                conflict_msg = _('Someone else changed this page while you were editing!')
                if self.mergeEditConflict(rev):
                    conflict_msg = _("""Someone else saved this page while you were editing!
Please review the page and save then. Do not save this page as it is!""")
                    rev = self.current_rev()
            if conflict_msg:
                # We don't show preview when in conflict
                preview = None

        elif self.exists():
            # revision of existing page
            rev = self.current_rev()
        else:
            # page creation
            rev = 0

        self.setConflict(bool(conflict_msg))

        # Page editing is done using user language
        request.setContentLanguage(request.lang)

        # Get the text body for the editor field.
        # TODO: what about deleted pages? show the text of the last revision or use the template?
        if preview is not None:
            raw_body = self.get_raw_body()
            if use_draft:
                request.write(_("[Content loaded from draft]"), '<br>')
        elif self.exists():
            # If the page exists, we get the text from the page.
            # TODO: maybe warn if template argument was ignored because the page exists?
            raw_body = self.get_raw_body()
        elif 'template' in request.values:
            # If the page does not exist, we try to get the content from the template parameter.
            template_page = wikiutil.unquoteWikiname(request.values['template'])
            if request.user.may.read(template_page):
                raw_body = Page(request, template_page).get_raw_body()
                if raw_body:
                    request.write(_("[Content of new page loaded from %s]") % (template_page, ), '<br>')
                else:
                    request.write(_("[Template %s not found]") % (template_page, ), '<br>')
            else:
                request.write(_("[You may not read %s]") % (template_page, ), '<br>')

        # Make backup on previews - but not for new empty pages
        if not use_draft and preview and raw_body:
            self._save_draft(raw_body, rev)

        draft_message = None
        loadable_draft = False
        if preview is None:
            draft = self._load_draft()
            if draft is not None:
                draft_timestamp, draft_rev, draft_text = draft
                if draft_text != raw_body:
                    loadable_draft = True
                    page_rev = rev
                    draft_timestamp_str = request.user.getFormattedDateTime(draft_timestamp)
                    draft_message = _(u"'''<<BR>>Your draft based on revision %(draft_rev)d (saved %(draft_timestamp_str)s) can be loaded instead of the current revision %(page_rev)d by using the load draft button - in case you lost your last edit somehow without saving it.''' A draft gets saved for you when you do a preview, cancel an edit or unsuccessfully save.", wiki=True, percent=True) % locals()

        # Setup status message
        status = [kw.get('msg', ''), conflict_msg, edit_lock_message, draft_message]
        status = [msg for msg in status if msg]
        status = ' '.join(status)
        status = Status(request, content=status)

        request.theme.add_msg(status, "error")
        request.theme.send_title(
            title % {'pagename': self.split_title(), },
            page=self,
            html_head=self.lock.locktype and (
                PageEditor._countdown_js % {
                     'countdown_script': request.theme.externalScript('countdown'),
                     'lock_timeout': lock_timeout,
                     'lock_expire': lock_expire,
                     'lock_mins': lock_mins,
                     'lock_secs': lock_secs,
                    }) or '',
            editor_mode=1,
        )

        request.write(request.formatter.startContent("content"))

        # Generate default content for new pages
        if not raw_body:
            raw_body = _('Describe %s here.') % (self.page_name, )

        # send form
        request.write('<form id="editor" method="post" action="%s#preview">' % (
                request.href(self.page_name)
            ))

        # yet another weird workaround for broken IE6 (it expands the text
        # editor area to the right after you begin to type...). IE sucks...
        # http://fplanque.net/2003/Articles/iecsstextarea/
        request.write('<fieldset style="border:none;padding:0;">')

        request.write(unicode(html.INPUT(type="hidden", name="action", value="edit")))

        # Send revision of the page our edit is based on
        request.write('<input type="hidden" name="rev" value="%d">' % (rev, ))

        # Add src format (e.g. 'wiki') into a hidden form field, so that
        # we can load the correct converter after POSTing.
        request.write('<input type="hidden" name="format" value="%s">' % self.pi['format'])

        # Create and send a ticket, so we can check the POST
        request.write('<input type="hidden" name="ticket" value="%s">' % wikiutil.createTicket(request))

        # Save backto in a hidden input
        backto = request.values.get('backto')
        if backto:
            request.write(unicode(html.INPUT(type="hidden", name="backto", value=backto)))

        # button bar
        button_spellcheck = '<input class="button" type="submit" name="button_spellcheck" value="%s">' % _('Check Spelling')

        save_button_text = _('Save Changes')
        cancel_button_text = _('Cancel')

        if self.cfg.page_license_enabled:
            request.write('<p><em>', _(
"""By hitting '''%(save_button_text)s''' you put your changes under the %(license_link)s.
If you don't want that, hit '''%(cancel_button_text)s''' to cancel your changes.""", wiki=True) % {
                'save_button_text': save_button_text,
                'cancel_button_text': cancel_button_text,
                'license_link': wikiutil.getLocalizedPage(request, self.cfg.page_license_page).link_to(request),
            }, '</em></p>')

        request.write('''
<input class="button" type="submit" name="button_save" value="%s">
<input class="button" type="submit" name="button_preview" value="%s">
<input class="button" type="submit" name="button_switch" value="%s">
''' % (save_button_text, _('Preview'), _('Text mode'), ))

        if loadable_draft:
            request.write('''
<input class="button" type="submit" name="button_load_draft" value="%s" onClick="flgChange = false;">
<input type="hidden" name="draft_ts" value="%d">
<input type="hidden" name="draft_rev" value="%d">
''' % (_('Load Draft'), draft_timestamp, draft_rev))

        request.write('''
%s
<input class="button" type="submit" name="button_cancel" value="%s">
<input type="hidden" name="editor" value="gui">
''' % (button_spellcheck, cancel_button_text, ))
        if self.cfg.mail_enabled:
            request.write('''
<script type="text/javascript">
    function toggle_trivial(CheckedBox)
    {
        TrivialBoxes = document.getElementsByName("trivial");
        for (var i = 0; i < TrivialBoxes.length; i++)
            TrivialBoxes[i].checked = CheckedBox.checked;
    }
</script>
&nbsp;
<input type="checkbox" name="trivial" id="chktrivialtop" value="1" %(checked)s onclick="toggle_trivial(this)">
<label for="chktrivialtop">%(label)s</label>
''' % {
          'checked': ('', 'checked')[form.get('trivial', '0') == '1'],
          'label': _("Trivial change"),
       })

        from MoinMoin.security.textcha import TextCha
        request.write(TextCha(request).render())

        self.sendconfirmleaving() # TODO update state of flgChange to make this work, see PageEditor

        # Add textarea with page text
        lang = self.pi.get('language', request.cfg.language_default)
        contentlangdirection = i18n.getDirection(lang) # 'ltr' or 'rtl'
        uilanguage = request.lang
        url_prefix_static = request.cfg.url_prefix_static
        url_prefix_local = request.cfg.url_prefix_local
        wikipage = wikiutil.quoteWikinameURL(self.page_name)
        fckbasepath = request.cfg.url_prefix_fckeditor
        wikiurl = request.script_root + '/'
        themepath = '%s/%s' % (url_prefix_static, request.theme.name)
        smileypath = themepath + '/img'
        # auto-generating a list for SmileyImages does NOT work from here!
        editor_size = int(request.user.edit_rows) * 22 # 22 height_pixels/line
        word_rule = self.word_rule()

        request.write("""
<script type="text/javascript" src="%(fckbasepath)s/fckeditor.js"></script>
<script type="text/javascript">
<!--
    var oFCKeditor = new FCKeditor( 'savetext', '100%%', %(editor_size)s, 'MoinDefault' ) ;
    oFCKeditor.BasePath= '%(fckbasepath)s/' ;
    oFCKeditor.Config['WikiBasePath'] = '%(wikiurl)s' ;
    oFCKeditor.Config['WikiPage'] = '%(wikipage)s' ;
    oFCKeditor.Config['PluginsPath'] = '%(url_prefix_local)s/applets/moinFCKplugins/' ;
    oFCKeditor.Config['CustomConfigurationsPath'] = '%(url_prefix_local)s/applets/moinfckconfig.js'  ;
    oFCKeditor.Config['WordRule'] = %(word_rule)s ;
    oFCKeditor.Config['SmileyPath'] = '%(smileypath)s/' ;
    oFCKeditor.Config['EditorAreaCSS'] = '%(themepath)s/css/common.css' ;
    oFCKeditor.Config['SkinPath'] = '%(fckbasepath)s/editor/skins/silver/' ;
    oFCKeditor.Config['AutoDetectLanguage'] = false ;
    oFCKeditor.Config['DefaultLanguage'] = '%(uilanguage)s' ;
    oFCKeditor.Config['ContentLangDirection']  = '%(contentlangdirection)s' ;
    oFCKeditor.Value= """ % locals())

        from MoinMoin.formatter.text_gedit import Formatter
        self.formatter = Formatter(request)
        self.formatter.page = self
        output = request.redirectedOutput(self.send_page_content, request, raw_body, format=self.pi['format'], do_cache=False)
        output = repr(output)
        if output[0] == 'u':
            output = output[1:]
        request.write(output)
        request.write(""" ;
    oFCKeditor.Create() ;
//-->
</script>
""")
        request.write("<p>")
        request.write(_("Comment:"),
            ' <input id="editor-comment" type="text" name="comment" value="%s" size="80" maxlength="200">' % (
                wikiutil.escape(kw.get('comment', ''), 1), ))
        request.write("</p>")

        # Category selection
        filterfn = self.cfg.cache.page_category_regexact.search
        cat_pages = request.rootpage.getPageList(filter=filterfn)
        cat_pages.sort()
        cat_pages = [wikiutil.pagelinkmarkup(p) for p in cat_pages]
        cat_pages.insert(0, ('', _('<No addition>')))
        request.write("<p>")
        request.write(_('Add to: %(category)s') % {
            'category': unicode(web.makeSelection('category', cat_pages)),
        })
        if self.cfg.mail_enabled:
            request.write('''
&nbsp;
<input type="checkbox" name="trivial" id="chktrivial" value="1" %(checked)s onclick="toggle_trivial(this)">
<label for="chktrivial">%(label)s</label> ''' % {
                'checked': ('', 'checked')[form.get('trivial', '0') == '1'],
                'label': _("Trivial change"),
                })

        request.write('''
&nbsp;
<input type="checkbox" name="rstrip" id="chkrstrip" value="1" %(checked)s>
<label for="chkrstrip">%(label)s</label>
</p> ''' % {
            'checked': ('', 'checked')[form.get('rstrip', '0') == '1'],
            'label': _('Remove trailing whitespace from each line')
            })

        request.write("</p>")

        badwords_re = None
        if preview is not None:
            if 'button_spellcheck' in form or 'button_newwords' in form:
                badwords, badwords_re, msg = SpellCheck.checkSpelling(self, request, own_form=0)
                request.write("<p>%s</p>" % msg)
        request.write('</fieldset>')
        request.write("</form>")

        if preview is not None:
            if staytop:
                content_id = 'previewbelow'
            else:
                content_id = 'preview'
            self.send_page(content_id=content_id, content_only=1, hilite_re=badwords_re)

        request.write(request.formatter.endContent()) # end content div
        request.theme.send_footer(self.page_name)
        request.theme.send_closing_html()

