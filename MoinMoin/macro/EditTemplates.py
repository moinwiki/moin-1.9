# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Create an action link

    @copyright: 2004 Johannes Berg <johannes@sipsolutions.de>
    @license: GNU GPL, see COPYING for details.
"""

Dependencies = ["language"]

def execute(self, args):
    result = ''
    # we don't want to spend much CPU for spiders requesting nonexisting pages
    if not self.request.isSpiderAgent:
        # Get list of template pages readable by current user
        filterfn = self.request.cfg.cache.page_template_regex.search
        templates = self.request.rootpage.getPageList(filter=filterfn)
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
        result = ''.join(result)
    return result

