# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Load I18N Text and format it

    @copyright: 2004 by Johannes Berg <johannes@sipsolutions.de>
    @license: GNU GPL, see COPYING for details.
"""

Dependencies = ["language"]

from MoinMoin import config

def execute(macro, args):
    d = {
        ## add other allowed stuff here
        'page_template_regex': config.page_template_regex,
    }

    return macro.formatter.text(
        macro.request.getText(args).replace('<br>', '\n') % d
    )

