# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.search.Xapian.tokenizer Tests

    @copyright: 2009 MoinMoin:DmitrijsMilajevs
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin._tests import wikiconfig


class TestWikiAnalyzer(object):

    word = u'HelpOnMoinTesting'
    words = {word.lower(): u'',
             u'help': u'',
             u'on': u'',
             u'moin': u'',
             u'testing': u''}

    def setup_class(self):
        try:
            from MoinMoin.search import Xapian
            self.analyzer = Xapian.WikiAnalyzer(request=self.request, language=self.request.cfg.language_default)
        except ImportError:
            py.test.skip('xapian is not installed')

    def test_tokenize(self):
        words = self.words
        tokens = list(self.analyzer.tokenize(self.word))

        assert len(tokens) == len(words)

        for token, stemmed in tokens:
            assert token in words
            assert words[token] == stemmed


class TestWikiAnalyzerStemmed(TestWikiAnalyzer):

    word = u'HelpOnMoinTesting'
    words = {word.lower(): u'helponmointest',
             u'help': u'',
             u'on': u'',
             u'moin': u'',
             u'testing': u'test'}

    class Config(wikiconfig.Config):

        xapian_stemming = True


class TestWikiAnalyzerSeveralWords(TestWikiAnalyzer):

    word = u'HelpOnMoinTesting OtherWikiWord'
    words = {u'helponmointesting': u'',
             u'help': u'',
             u'on': u'',
             u'moin': u'',
             u'testing': u'',
             u'otherwikiword': u'',
             u'other': u'',
             u'wiki': u'',
             u'word': u''}


class TestWikiAnalyzerStemmedSeveralWords(TestWikiAnalyzer):

    word = u'HelpOnMoinTesting OtherWikiWord'
    words = {u'helponmointesting': u'helponmointest',
             u'help': u'',
             u'on': u'',
             u'moin': u'',
             u'testing': u'test',
             u'otherwikiword': u'',
             u'other': u'',
             u'wiki': u'',
             u'word': u''}

    class Config(wikiconfig.Config):

        xapian_stemming = True

