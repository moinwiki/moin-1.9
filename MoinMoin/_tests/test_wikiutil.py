# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.wikiutil Tests

    @copyright: 2003-2004 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import unittest
from MoinMoin._tests import TestConfig
from MoinMoin import wikiutil


class SystemPageTestCase(unittest.TestCase):
    systemPages = (
        # First level, on SystemPagesGroup
        'SystemPagesInEnglishGroup',
        # Second level, on one of the pages above
        'RecentChanges',
        'TitleIndex',
        )
    notSystemPages = (
        'NoSuchPageYetAndWillNeverBe',
        )

    def testSystemPage(self):
        """wikiutil: good system page names accepted, bad rejected"""
        for name in self.systemPages:
            self.assert_(wikiutil.isSystemPage(self.request, name),
                '"%(name)s" is a system page' % locals())
        for name in self.notSystemPages:
            self.failIf(wikiutil.isSystemPage(self.request, name),
                '"%(name)s" is NOT a system page' % locals())


class TemplatePageTestCase(unittest.TestCase):
    good = (
        'aTemplate',
        'MyTemplate',
    )
    bad = (
        'Template',
        'ATemplate',
        'TemplateInFront',
        'xTemplateInFront',
        'XTemplateInFront',
    )

    # require default page_template_regex config
    def setUp(self):
        self.config = TestConfig(self.request,
                                 defaults=['page_template_regex'])
    def tearDown(self):
        del self.config

    def testTemplatePage(self):
        """wikiutil: good template names accepted, bad rejected"""
        for name in self.good:
            self.assert_(wikiutil.isTemplatePage(self.request, name),
                '"%(name)s" is a valid template name' % locals())
        for name in self.bad:
            self.failIf(wikiutil.isTemplatePage(self.request, name),
                '"%(name)s" is NOT a valid template name' % locals())


