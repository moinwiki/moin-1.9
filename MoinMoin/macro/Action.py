# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Create an action link

    Usage:

        [[Action(action)]]

        Create a link to page with ?action=action and the text action

        [[Action(action, text)]]

        Same with custom text.

    @copyright: 2004 by Johannes Berg <johannes@sipsolutions.de>
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import wikiutil
from MoinMoin.Page import Page

Dependencies = ["language"]


class ActionLink:
    """ ActionLink - link to page with action """

    arguments = ['action', 'text']

    def __init__(self, macro, args):
        self.macro = macro
        self.request = macro.request
        self.args = self.getArgs(args)

    def getArgs(self, string):
        """ Temporary function until Oliver Graf args parser is finished

        @param string: string from the wiki markup [[NewPage(string)]]
        @rtype: dict
        @return: dictionary with macro options
        """
        if not string:
            return {}
        args = [s.strip() for s in string.split(',')]
        args = dict(zip(self.arguments, args))
        return args

    def renderInText(self):
        """ Render macro in text context

        The parser should decide what to do if this macro is placed in a
        paragraph context.
        """
        _ = self.request.getText

        # Default to show page instead of an error message (too lazy to
        # do an error message now).
        action = self.args.get('action', 'show')
        
        # Use translated text or action name
        text = self.args.get('text', action)
        text = _(text, formatted=False)        

        # Escape user input
        action = wikiutil.escape(action, 1)
        text = wikiutil.escape(text, 1)

        # Create link
        formatter = self.macro.formatter
        page = wikiutil.quoteWikinameURL(formatter.page.page_name)
        url = '%s?action=%s' % (page, action)
        link = wikiutil.link_tag(self.request, url, text=text,
                                 formatter=formatter)
        return link


def execute(macro, args):
    """ Temporary glue code to use with moin current macro system """
    return ActionLink(macro, args).renderInText()


