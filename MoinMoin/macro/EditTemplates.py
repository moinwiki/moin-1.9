# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Create an action link

    @copyright: 2004 by Johannes Berg <johannes@sipsolutions.de>
    @license: GNU GPL, see COPYING for details.
"""

import re

Dependencies = ["language"]
from MoinMoin import wikiutil

def execute(self, args):
    # Get list of template pages readable by current user
    filter = re.compile(self.request.cfg.page_template_regex, re.UNICODE).search
    templates = self.request.rootpage.getPageList(filter=filter)
    result = []
    if templates:
        templates.sort()
        page = self.formatter.page
        # send list of template pages
        result.append(self.formatter.bullet_list(1))
        for template in templates:
            result.append(self.formatter.listitem(1))
            result.append(page.link_to(self.request, template, querystr={'action': 'edit', 'template': template}))
            result.append(self.formatter.listitem(0))
        result.append(self.formatter.bullet_list(0))
    return ''.join(result)

