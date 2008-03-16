# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - UserPreferences action

    This is a simple plugin, that adds a "UserPreferences" action.

    @copyright: 2006 Radomir Dopieralski
                2007 MoinMoin:JohannesBerg
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import wikiutil
from MoinMoin.widget import html

def _handle_submission(request):
    """ Handle GET and POST requests of preferences forms.

    Return error msg or None.
    """
    _ = request.getText
    sub = request.form.get('handler', [None])[0]

    if sub in request.cfg.disabled_userprefs:
        return None

    try:
        cls = wikiutil.importPlugin(request.cfg, 'userprefs', sub, 'Settings')
    except wikiutil.PluginMissingError:
        # we never show this plugin to click on so no need to
        # give a message here
        return None

    obj = cls(request)
    if not obj.allowed():
        return None
    return obj.handle_form()

def _create_prefs_page(request, sel=None):
    _ = request.getText
    plugins = wikiutil.getPlugins('userprefs', request.cfg)
    ret = html.P()
    ret.append(html.Text(_("Please choose:")))
    ret.append(html.BR())
    items = html.UL()
    ret.append(items)
    for sub in plugins:
        if sub in request.cfg.disabled_userprefs:
            continue
        cls = wikiutil.importPlugin(request.cfg, 'userprefs', sub, 'Settings')
        obj = cls(request)
        if not obj.allowed():
            continue
        url = request.page.url(request, {'action': 'userprefs', 'sub': sub})
        lnk = html.LI().append(html.A(href=url).append(html.Text(obj.title)))
        items.append(lnk)
    return unicode(ret)


def _create_page(request, cancel=False):
    # returns text, title, msg
    pagename = request.page.page_name

    if 'handler' in request.form:
        msg = _handle_submission(request)
    else:
        msg = None

    sub = request.form.get('sub', [''])[0]
    cls = None
    if sub and not sub in request.cfg.disabled_userprefs:
        try:
            cls = wikiutil.importPlugin(request.cfg, 'userprefs', sub, 'Settings')
        except wikiutil.PluginMissingError:
            # cls is already None
            pass

    obj = cls and cls(request)

    if not obj or not obj.allowed():
        return _create_prefs_page(request), None, msg

    return obj.create_form(), obj.title, msg


def execute(pagename, request):
    _ = request.getText
    text, title, msg = _create_page(request)
    if not title:
        title = _("Settings")
    else:
        lnk = html.A(href='xx').append(html.Text(_("Settings")))
        lnk = unicode(lnk)
        title = _("Settings") + "/" + title
    request.emit_http_headers()
    request.theme.add_msg(msg, "dialog")
    request.theme.send_title(title, page=request.page, pagename=pagename)
    # Start content (important for RTL support)
    request.write(request.formatter.startContent("content"))
    request.write(text)
    request.write(request.formatter.endContent())
    request.theme.send_footer(pagename)
    request.theme.send_closing_html()
