# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Wiki Synchronisation

    @copyright: 2006 by MoinMoin:AlexanderSchremmer
    @license: GNU GPL, see COPYING for details.
"""

try:
    import cpickle as pickle
except ImportError:
    import pickle


class Tag(object):
    """ This class is used to store information about merging state. """
    
    def __init__(self, remote_wiki, remote_rev, current_rev):
        self.remote_wiki = remote_wiki
        self.remote_rev = remote_rev
        self.current_rev = current_rev


class AbstractTagStore(object):
    """ This class is an abstract base class that shows how to implement classes
        that manage the storage of tags. """

    def __init__(self, page):
        pass

    def add(self, **kwargs):
        print "Got tag for page %r: %r" % (self.page, kwargs)


class PickleTagStore(AbstractTagStore):
    """ This class manages the storage of tags in pickle files. """

    def __init__(self, page):
        self.page = page
        self.filename = page.getPagePath('synctags', use_underlay=0, check_create=1, isfile=1)
        self.load()

    def load(self):
        try:
            datafile = file(self.filename, "rb")
        except IOError:
            self.tags = []
        else:
            self.tags = pickle.load(datafile)
            datafile.close()
    
    def commit(self):
        datafile = file(self.filename, "wb")
        pickle.dump(self.tags, datafile, protocol=pickle.HIGHEST_PROTOCOL)
        datafile.close()

    # public methods
    def add(self, **kwargs):
        print "Got tag for page %r: %r" % (self.page, kwargs)
        self.tags.append(Tag(**kwargs))
        self.commit()

TagStore = PickleTagStore