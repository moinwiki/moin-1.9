#! /usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""check_i18n - compare texts in the source with the language files

Searches in the MoinMoin sources for calls of _() and tries to extract
the parameter.  Then it checks the language modules if those parameters
are in the dictionary.

Usage: check_i18n.py [lang ...]

Without arguments, checks all languages in i18n or the specified
languages. Look into MoinMoin.i18n.__init__ for availeable language
names.

The script will run from the moin root directory, where the MoinMoin
package lives, or from MoinMoin/i18n where this script lives.

TextFinder class based on code by Seo Sanghyeon and the python compiler
package.

TODO: fix it for the changed i18n stuff of moin 1.6

@copyright: 2003 Florian Festi, Nir Soffer, Thomas Waldmann
@license: GNU GPL, see COPYING for details.
"""

output_encoding = 'utf-8'

# These lead to crashes (MemoryError - due to missing codecs?)
#blacklist_files = ["ja.py", "zh.py", "zh_tw.py"]
#blacklist_langs = ["ja", "zh", "zh-tw"]

# If you have cjkcodecs installed, use this:
blacklist_files = []
blacklist_langs = []

import sys, os, compiler
from compiler.ast import Name, Const, CallFunc, Getattr

class TextFinder:
    """ Walk through AST tree and collect text from gettext calls

    Find all calls to gettext function in the source tree and collect
    the texts in a dict. Use compiler to create an abstract syntax tree
    from each source file, then find the nodes for gettext function
    call, and get the text from the call.

    Localized texts are used usually translated during runtime by
    gettext functions and apear in the source as
    _('text...'). TextFinder class finds calls to the '_' function in
    any namespace, or your prefered gettext function.

    Note that TextFinder will only retrieve text from function calls
    with a constant argument like _('text'). Calls like _('text' % locals()),
    _('text 1' + 'text 2') are marked as bad call in the report, and the
    text is not retrieved into the dictionary.

    Note also that texts in source can appear several times in the same
    file or different files, but they will only apear once in the
    dictionary that this tool creates.

    The dictionary value for each text is a dictionary of filenames each
    containing a list of (best guess) lines numbers containning the text.
    """

    def __init__(self, name='_'):
        """ Init with the gettext function name or '_'"""
        self._name = name       # getText function name
        self._dictionary = {}   # Unique texts in the found texts
        self._found = 0         # All good calls including duplicates
        self._bad = 0           # Bad calls: _('%s' % var) or _('a' + 'b')

    def setFilename(self, filename):
        """Remember the filename we are parsing"""
        self._filename = filename

    def visitModule(self, node):
        """ Start the search from the top node of a module

        This is the entry point into the search. When compiler.walk is
        called it calls this method with the module node.

        This is the place to initialize module specific data.
        """
        self._visited = {}  # init node cache - we will visit each node once
        self._lineno = 'NA' # init line number

        # Start walking in the module node
        self.walk(node)

    def walk(self, node):
        """ Walk through all nodes """
        if node in self._visited:
            # We visited this node already
            return

        self._visited[node] = 1
        if not self.parseNode(node):
            for child in node.getChildNodes():
                self.walk(child)

    def parseNode(self, node):
        """ Parse function call nodes and collect text """

        # Get the current line number. Since not all nodes have a line number
        # we save the last line number - it should be close to the gettext call
        if node.lineno is not None:
            self._lineno = node.lineno

        if node.__class__ == CallFunc and node.args:
            child = node.node
            klass = child.__class__
            if (# Standard call _('text')
                (klass == Name and child.name == self._name) or
                # A call to an object attribute: object._('text')
                (klass == Getattr and child.attrname == self._name)):
                if node.args[0].__class__ == Const:
                    # Good call with a constant _('text')
                    self.addText(node.args[0].value)
                else:
                    self.addBadCall(node)
                return 1
        return 0

    def addText(self, text):
        """ Add text to dictionary and count found texts.

        Note that number of texts in dictionary could be different from
        the number of texts found, because some texts appear several
        times in the code.

        Each text value is a dictionary of filenames that contain the
        text and each filename value is the list of line numbers with
        the text. Missing line numbers are recorded as 'NA'.

        self._lineno is the last line number we checked. It may be the line
        number of the text, or near it.
        """

        self._found = self._found + 1

        # Create key for this text if needed
        if text not in self._dictionary:
            self._dictionary[text] = {}

        # Create key for this filename if needed
        textInfo = self._dictionary[text]
        if self._filename not in textInfo:
            textInfo[self._filename] = [self._lineno]
        else:
            textInfo[self._filename].append(self._lineno)

    def addBadCall(self, node):
        """Called when a bad call like _('a' + 'b') is found"""
        self._bad = self._bad + 1
        print
        print "<!> Warning: non-constant _ call:"
        print " `%s`" % str(node)
        print " `%s`:%s" % (self._filename, self._lineno)

    # Accessors

    def dictionary(self):
        return self._dictionary

    def bad(self):
        return self._bad

    def found(self):
        return self._found


def visit(path, visitor):
    visitor.setFilename(path)
    tree = compiler.parseFile(path)
    compiler.walk(tree, visitor)


# MoinMoin specific stuff follows


class Report:
    """Language status report"""
    def __init__(self, lang, sourceDict):
        self.__lang = lang
        self.__sourceDict = sourceDict
        self.__langDict = None
        self.__missing = {}
        self.__unused = {}
        self.__error = None
        self.__ready = 0
        self.create()

    def loadLanguage(self):
        filename = i18n.filename(self.__lang)
        self.__langDict = pysupport.importName("MoinMoin.i18n." + filename, "text")

    def create(self):
        """Compare language text dict against source dict"""
        self.loadLanguage()
        if not self.__langDict:
            self.__error = "Language %s not found!" % self.__lang
            self.__ready = 1
            return

        # Collect missing texts
        for text in self.__sourceDict:
            if text not in self.__langDict:
                self.__missing[text] = self.__sourceDict[text]

        # Collect unused texts
        for text in self.__langDict:
            if text not in self.__sourceDict:
                self.__unused[text] = self.__langDict[text]
        self.__ready = 1

    def summary(self):
        """Return summary dict"""
        summary = {
            'name': i18n.languages[self.__lang][i18n.ENAME].encode(output_encoding),
            'maintainer': i18n.languages[self.__lang][i18n.MAINTAINER],
            'total': len(self.__langDict),
            'missing': len(self.__missing),
            'unused': len(self.__unused),
            'error': self.__error
            }
        return summary

    def missing(self):
        return self.__missing

    def unused(self):
        return self.__unused


if __name__ == '__main__':
    import time

    # Check that we run from the root directory where MoinMoin package lives
    # or from the i18n directory when this script lives
    if os.path.exists('MoinMoin/__init__.py'):
        # Running from the root directory
        MoinMoin_dir = os.curdir
    elif os.path.exists(os.path.join(os.pardir, 'i18n')):
        # Runing from i18n
        MoinMoin_dir = os.path.join(os.pardir, os.pardir)
    else:
        print __doc__
        sys.exit(1)

    # Insert MoinMoin_dir into sys.path
    sys.path.insert(0, MoinMoin_dir)
    from MoinMoin import i18n
    from MoinMoin.util import pysupport

    textFinder = TextFinder()
    found = 0
    unique = 0
    bad = 0

    # Find gettext calls in the source
    for root, dirs, files in os.walk(os.path.join(MoinMoin_dir, 'MoinMoin')):
        for name in files:
            if name.endswith('.py'):
                if name in blacklist_files: continue
                path = os.path.join(root, name)
                #print '%(path)s:' % locals(),
                visit(path, textFinder)

                # Report each file's results
                new_unique = len(textFinder.dictionary()) - unique
                new_found = textFinder.found() - found
                #print '%(new_unique)d (of %(new_found)d)' % locals()

                # Warn about bad calls - these should be fixed!
                new_bad = textFinder.bad() - bad
                #if new_bad:
                #    print '### Warning: %(new_bad)d bad call(s)' % locals()

                unique = unique + new_unique
                bad = bad + new_bad
                found = found + new_found

    # Print report using wiki markup, so we can publish this on MoinDev
    # !!! Todo:
    #     save executive summary for the wiki
    #     save separate report for each language to be sent to the
    #     language translator.
    #     Update the wiki using XML-RPC??

    print "This page is generated by `MoinMoin/i18n/check_i18n.py`."
    print "To recreate this report run `make check-i18n` and paste here"
    print
    print '----'
    print
    print '<<TableOfContents(2)>>'
    print
    print
    print "= Translation Report ="
    print
    print "== Summary =="
    print
    print 'Created on %s' % time.asctime()
    print

    print ('\n%(unique)d unique texts in dictionary of %(found)d texts '
           'in source.') % locals()
    if bad:
        print '\n%(bad)d bad calls.' % locals()
    print

    # Check languages from the command line or from moin.i18n against
    # the source
    if sys.argv[1:]:
        languages = sys.argv[1:]
    else:
        languages = i18n.languages.keys()
        for lang in blacklist_langs:
            # problems, maybe due to encoding?
            if lang in languages:
                languages.remove(lang)
    if 'en' in languages:
        languages.remove('en') # there is no en lang file
    languages.sort()

    # Create report for all languages
    report = {}
    for lang in languages:
        report[lang] = Report(lang, textFinder.dictionary())

    # Print summary for all languages
    print ("||<:>'''Language'''||<:>'''Texts'''||<:>'''Missing'''"
           "||<:>'''Unused'''||")
    for lang in languages:
        print ("||%(name)s||<)>%(total)s||<)>%(missing)s||<)>%(unused)s||"
               ) % report[lang].summary()

    # Print details
    for lang in languages:
        dict = report[lang].summary()
        print
        print "== %(name)s ==" % dict
        print
        print "Maintainer: <<MailTo(%(maintainer)s)>>" % dict

        # Print missing texts, if any
        if report[lang].missing():
            print """
=== Missing texts ===

These items should ''definitely'' get fixed.

Maybe the corresponding english text in the source code was only changed
slightly, then you want to look for a similar text in the ''unused''
section below and modify i18n, so that it will match again.
"""
            for text in report[lang].missing():
                print " 1. `%r`" % text

        # Print unused texts, if any
        if report[lang].unused():
            print """
=== Possibly unused texts ===

Be ''very careful'' and double-check before removing any of these
potentially unused items.

This program can't detect references done from wiki pages, from
userprefs options, from Icon titles etc.!
"""
            for text in report[lang].unused():
                print " 1. `%r`" % text


