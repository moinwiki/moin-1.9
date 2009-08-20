# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin.search.Xapian.tokenizer Tests

    @copyright: 2009 MoinMoin:DmitrijsMilajevs
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin._tests import wikiconfig


class TestWikiAnalyzer(object):

    word = u'HelpOnMoinTesting'
    words = {word: u'',
             u'Help': u'',
             u'On': u'',
             u'Moin': u'',
             u'Testing': u''}

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

    def test_first_token(self):
        tokens = list(self.analyzer.tokenize(self.word))
        assert tokens[0][0] == self.word, 'The first token must be the word itself'


class TestWikiAnalyzerStemmed(TestWikiAnalyzer):

    word = u'HelpOnMoinTesting'
    words = {word: u'HelpOnMoinTest',
             u'Help': u'',
             u'On': u'',
             u'Moin': u'',
             u'Testing': u'Test'}

    class Config(wikiconfig.Config):

        xapian_stemming = True


class TestWikiAnalyzerSeveralWords(TestWikiAnalyzer):

    word = u'HelpOnMoinTesting OtherWikiWord'
    words = {u'HelpOnMoinTesting': u'',
             u'Help': u'',
             u'On': u'',
             u'Moin': u'',
             u'Testing': u'',
             u'OtherWikiWord': u'',
             u'Other': u'',
             u'Wiki': u'',
             u'Word': u''}

    def test_first_token(self):
        pass

class TestWikiAnalyzerStemmedSeveralWords(TestWikiAnalyzer):

    word = u'HelpOnMoinTesting OtherWikiWord'
    words = {u'HelpOnMoinTesting': u'HelpOnMoinTest',
             u'Help': u'',
             u'On': u'',
             u'Moin': u'',
             u'Testing': u'Test',
             u'OtherWikiWord': u'',
             u'Other': u'',
             u'Wiki': u'',
             u'Word': u''}

    class Config(wikiconfig.Config):

        xapian_stemming = True

    def test_first_token(self):
        pass
