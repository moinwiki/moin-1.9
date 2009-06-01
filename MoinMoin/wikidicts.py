# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Dictionary / Group Functions

    @copyright: 2003-2007 MoinMoin:ThomasWaldmann,
                2003 by Gustavo Niemeyer
    @license: GNU GPL, see COPYING for details.
"""
import re, time

from MoinMoin import Page


class DictBase(dict):
    """ Base class for wiki dicts

    To use this class, subclass it and override regex and initFromText.
    """
    def __init__(self, request=None, pagename=None):
        dict.__init__(self)
        self.name = None
        if request is not None and pagename is not None:
            self.loadFromPage(request, pagename)

    # Regular expression used to parse text - subclass must override this
    regex = None  # re.compile(u'...', re.MULTILINE | re.UNICODE)

    def loadFromPage(self, request, name):
        """ load the dict from wiki page <name>'s content """
        self.name = name
        text = Page.Page(request, name).get_raw_body()
        self.initFromText(text)

    def initFromText(self, text):
        """ parse the wiki page text and init the dict from it """
        raise NotImplementedError('subclasses should override this')


class Dict(DictBase):
    """ Mapping of keys to values in a wiki page.

       How a Dict definition page should look like:

       any text ignored
        key1:: value1
        * ignored, too
        key2:: value2 containing spaces
        ...
        keyn:: ....
       any text ignored
    """
    # Key:: Value - ignore all but key:: value pairs, strip whitespace, exactly one space after the :: is required
    regex = re.compile(ur'^ (?P<key>.+?):: (?P<val>.*?) *$', re.MULTILINE | re.UNICODE)

    def initFromText(self, text):
        for match in self.regex.finditer(text):
            key, val = match.groups()
            self[key] = val

    def __repr__(self):
        return "<Dict name=%r items=%r>" % (self.name, self.items())


class DictDict:
    """ a dictionary of Dict objects

       Config:
           cfg.page_dict_regex
               Default: ".*Dict$"  Defs$ Vars$ ???????????????????
    """

    def __init__(self):
        self.reset()

    def reset(self):
        self.dictdict = {}
        self.namespace_timestamp = 0
        self.pageupdate_timestamp = 0
        self.base_timestamp = 0
        self.picklever = DICTS_PICKLE_VERSION

    def has_key(self, dictname, key):
        """ check if we have key <key> in dict <dictname> """
        d = self.dictdict.get(dictname)
        return d and d.has_key(key)

    def keys(self, dictname):
        """ get keys of dict <dictname> """
        try:
            d = self.dictdict[dictname]
        except KeyError:
            return []
        return d.keys()

    def values(self, dictname):
        """ get values of dict <dictname> """
        try:
            d = self.dictdict[dictname]
        except KeyError:
            return []
        return d.values()

    def dict(self, dictname):
        """ get dict <dictname> """
        try:
            d = self.dictdict[dictname]
        except KeyError:
            return {}
        return d

    def adddict(self, request, dictname):
        """ add a new dict (will be read from the wiki page) """
        self.dictdict[dictname] = Dict(request, dictname)

    def has_dict(self, dictname):
        """ check if we have a dict <dictname> """
        return self.dictdict.has_key(dictname)

    def keydict(self, key):
        """ list all dicts that contain key """
        dictlist = []
        for d in self.dictdict.values():
            if d.has_key(key):
                dictlist.append(d.name)
        return dictlist
