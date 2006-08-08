# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - edit a page

    This either calls the text or the GUI page editor.

    @copyright: 2000-2004 by Jürgen Hermann <jh@web.de>,
                2006 by MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""
from MoinMoin import wikiutil
from MoinMoin.Page import Page

def execute(pagename, request):
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
            still_conflict = wikiutil.containsConflictMarker(savetext)
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
            # msg contains a unicode string
            savemsg = unicode(msg)

        # Send new page after save or after unsuccessful conflict merge.
        request.reset()
        backto = request.form.get('backto', [None])[0]
        if backto:
            pg = Page(request, backto)

        pg.send_page(request, msg=savemsg)

