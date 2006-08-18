# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - New Page macro

    Thanks to Jos Yule's "blogpost" action and his modified Form for
    giving me the pieces I needed to figure all this stuff out:
    http://moinmoin.wikiwikiweb.de/JosYule

    @copyright: 2004 Vito Miliano (vito_moinnewpagewithtemplate@perilith.com)
    @copyright: 2004 by Nir Soffer <nirs@freeshell.org>
    @copyright: 2004 Alexander Schremmer <alex AT alexanderweb DOT de>
    @copyright: 2006 MoinMoin:ReimarBauer
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import wikiutil

Dependencies = ["language"]

class NewPage:
    """ NewPage - create new pages

    Let you create new page using optional template, button text
    and parent page (for automatic subpages).

    Usage:

        [[NewPage(template, buttonLabel, parentPage)]]
        
    Examples:

        [[NewPage]]

            Create an input field with 'Create New Page' button. The new
            page will not use a template.

        [[NewPage(BugTemplate, Create New Bug, MoinMoinBugs)]]
        
            Create an input field with button labeled 'Create New
            Bug'.  The new page will use the BugTemplate template,
            and create the page as a subpage of MoinMoinBugs.
    """

    arguments = ['template', 'buttonLabel', 'parentPage', 'nameTemplate']

    def __init__(self, macro, args):
        self.macro = macro
        self.request = macro.request
        self.formatter = macro.formatter
        self.args = self.getArgs(args)

    def getArgs(self, argstr):
        """ Temporary function until Oliver Graf args parser is finished

        @param string: string from the wiki markup [[NewPage(string)]]
        @rtype: dict
        @return: dictionary with macro options
        """
        if not string:
            return {}
        args = [s.strip() for s in argstr.split(',')]
        args = dict(zip(self.arguments, args))
        return args

    def renderInPage(self):
        """ Render macro in page context

        The parser should decide what to do if this macro is placed in a
        paragraph context.
        """
        f = self.formatter
        _ = self.request.getText

        parent = self.args.get('parentPage') or ''
        template = self.args.get('template') or ''
        label = self.args.get('buttonLabel')
        nametemplate = self.args.get('nameTemplate') or u'%s'

        if parent == '@ME' and self.request.user.valid:
            parent = self.request.user.name

        requires_input = '%s' in nametemplate

        if label:
            # Try to get a translation, this will probably not work in
            # most case, but better than nothing.
            label = _(label)
        else:
            label = _("Create New Page")

        # TODO: better abstract this using the formatter
        html = [
            u'<form class="macro" method="get" action=""><div>',
            u'<input type="hidden" name="action" value="newpage">',
            u'<input type="hidden" name="parent" value="%s">' % wikiutil.escape(parent, 1),
            u'<input type="hidden" name="template" value="%s">' % wikiutil.escape(template, 1),
            u'<input type="hidden" name="nametemplate" value="%s">' % wikiutil.escape(nametemplate, 1),
        ]

        if requires_input:
            html += [
                u'<input type="text" name="pagename" size="30">',
            ]
        html += [
            u'<input type="submit" value="%s">' % wikiutil.escape(label, 1),
            u'</div></form>',
            ]
        return self.formatter.rawHTML('\n'.join(html))

def execute(macro, args):
    """ Temporary glue code to use with moin current macro system """
    return NewPage(macro, args).renderInPage()

