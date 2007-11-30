# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.search Tests

    @copyright: 2005 by Nir Soffer <nirs@freeshell.org>
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import search


class TestQuotingBug:
    """search: quoting bug tests

    http://moinmoin.wikiwikiweb.de/MoinMoinBugs/SearchOneCharString
    """

    def testIsQuoted(self):
        """ search: quoting bug - quoted terms """
        parser = search.QueryParser()
        for case in ('"yes"', "'yes'"):
            assert parser.isQuoted(case)

    def testIsNotQuoted(self):
        """ search: quoting bug - unquoted terms """
        tests = ('', "'", '"', '""', "''", "'\"", '"no', 'no"', "'no", "no'", '"no\'')
        parser = search.QueryParser()
        for case in tests:
            assert not parser.isQuoted(case)


coverage_modules = ['MoinMoin.search']

