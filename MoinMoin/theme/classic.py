# -*- coding: iso-8859-1 -*-
"""
    MoinMoin classic theme

    This class can also be used as base class for other themes -
    if you make an empty child class, you will get classic behaviour.

    If you want modified behaviour, just override the stuff you
    want to change in the child class.

    @copyright: 2003-2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import caching
from MoinMoin.action import get_available_actions
from MoinMoin.theme import ThemeBase


class Theme(ThemeBase):
    """ here are the functions generating the html responsible for
        the look and feel of your wiki site
    """

    name = "classic"

    def footer(self, d, **keywords):
        """ Assemble wiki footer

        @param d: parameter dictionary
        @keyword ...:...
        @rtype: unicode
        @return: page footer html
        """
        page = d['page']
        parts = [# End of page
                 self.pageinfo(page),
                 self.endPage(),

                 # Pre footer custom html (not recommended!)
                 self.emit_custom_html(self.cfg.page_footer1),

                 # Footer
                 self.editbar(d, **keywords),
                 self.credits(d),
                 self.showversion(d, **keywords),

                 # Post footer custom html
                 self.emit_custom_html(self.cfg.page_footer2), ]
        return u'\n'.join(parts)

    def editbar(self, d, **keywords):
        if not self.shouldShowEditbar(d['page']):
            return ''
        parts = [u'<div id="footer">',
                 self.edit_link(d, **keywords),
                 self.availableactions(d),
                 u'</div>', ]
        return ''.join(parts)

    def iconbar(self, d):
        """
        Assemble the iconbar

        @param d: parameter dictionary
        @rtype: string
        @return: iconbar html
        """
        iconbar = []
        if self.cfg.page_iconbar and self.request.user.show_toolbar and d['page_name']:
            iconbar.append('<ul id="iconbar">\n')
            icons = self.cfg.page_iconbar[:]
            for icon in icons:
                if icon == "up":
                    if d['page_parent_page']:
                        iconbar.append('<li>%s</li>\n' % self.make_iconlink(icon, d))
                elif icon == "subscribe" and (self.cfg.mail_enabled or self.cfg.jabber_enabled):
                    iconbar.append('<li>%s</li>\n' % self.make_iconlink(
                        ["subscribe", "unsubscribe"][self.request.user.isSubscribedTo([d['page_name']])], d))
                else:
                    iconbar.append('<li>%s</li>\n' % self.make_iconlink(icon, d))
            iconbar.append('</ul>\n')
        return ''.join(iconbar)

    def header(self, d):
        """
        Assemble page header

        @param d: parameter dictionary
        @rtype: string
        @return: page header html
        """
        newdict = {
            'config_header1_html': self.emit_custom_html(self.cfg.page_header1),
            'config_header2_html': self.emit_custom_html(self.cfg.page_header2),
            'search_form_html': self.searchform(d),
            'logo_html': self.logo(),
            'interwiki_html': self.interwiki(d),
            'title_html': self.title(d),
            'username_html': self.username(d),
            'navibar_html': self.navibar(d),
            'iconbar_html': self.iconbar(d),
            'msg_html': self.msg(d),
            'trail_html': self.trail(d),
            'startpage_html': self.startPage(),
        }
        newdict.update(d)

        html = """
%(config_header1_html)s

<div id="header">
%(logo_html)s
%(search_form_html)s
%(username_html)s
<div id="locationline">
%(interwiki_html)s
%(title_html)s
</div>
%(trail_html)s
%(iconbar_html)s
%(navibar_html)s
%(msg_html)s
</div>

%(config_header2_html)s

%(startpage_html)s
""" % newdict
        return html

    def editorheader(self, d):
        """
        Assemble page header for editor

        @param d: parameter dictionary
        @rtype: string
        @return: page header html
        """
        dict = {
            'config_header1_html': self.emit_custom_html(self.cfg.page_header1),
            'config_header2_html': self.emit_custom_html(self.cfg.page_header2),
            'title_html': self.title(d),
            'msg_html': self.msg(d),
            'startpage_html': self.startPage(),
        }
        dict.update(d)

        html = """
%(config_header1_html)s

%(title_html)s
%(msg_html)s

%(config_header2_html)s

%(startpage_html)s
""" % dict
        return html

    # Footer stuff #######################################################

    def edit_link(self, d, **keywords):
        """
        Assemble EditText link (or indication that page cannot be edited)

        @param d: parameter dictionary
        @rtype: string
        @return: edittext link html
        """
        page = d['page']
        return  u'<ul class="editbar"><li>%s</li></ul>' % self.editorLink(page)

    def availableactions(self, d):
        """
        assemble HTML code for the available actions

        @param d: parameter dictionary
        @rtype: string
        @return: available actions html
        """
        request = self.request
        _ = request.getText
        rev = d['rev']
        html = []
        page = d['page']
        available = get_available_actions(request.cfg, page, request.user)
        if available:
            available = list(available)
            available.sort()
            for action in available:
                # Always add spaces: AttachFile -> Attach File
                # XXX do not make a page object just for split_title
                #title = Page(request, action).split_title(force=1)
                title = action
                # Use translated version if available
                title = _(title)
                querystr = {'action': action}
                if rev:
                    querystr['rev'] = str(rev)
                link = page.link_to(request, text=title, querystr=querystr, rel='nofollow')
                html.append(link)

        title = _("DeleteCache")
        link = page.link_to(request, text=title, querystr={'action': 'refresh'}, rel='nofollow')

        cache = caching.CacheEntry(request, page, page.getFormatterName(), scope='item')
        date = request.user.getFormattedDateTime(cache.mtime())
        deletecache = u'<p>%s %s</p>' % (link, _('(cached %s)') % date)

        html = deletecache + u'<p>%s %s</p>\n' % (_('Or try one of these actions:'),
                                       u', '.join(html))
        return html


def execute(request):
    """
    Generate and return a theme object

    @param request: the request object
    @rtype: MoinTheme
    @return: Theme object
    """
    return Theme(request)

