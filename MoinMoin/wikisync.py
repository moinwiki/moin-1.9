# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Wiki Synchronisation

    @copyright: 2006 by MoinMoin:AlexanderSchremmer
    @license: GNU GPL, see COPYING for details.
"""

try:
    import cPickle as pickle
except ImportError:
    import pickle


class Tag(object):
    """ This class is used to store information about merging state. """
    
    def __init__(self, remote_wiki, remote_rev, current_rev):
        """ Creates a new Tag.
        
        @param remote_wiki: The identifier of the remote wiki.
        @param remote_rev: The revision number on the remote end.
        @param current_rev: The related local revision.
        """
        self.remote_wiki = remote_wiki
        self.remote_rev = remote_rev
        self.current_rev = current_rev

    def __repr__(self):
        return u"<Tag remote_wiki=%r remote_rev=%r current_rev=%r>" % (self.remote_wiki, self.remote_rev, self.current_rev)


class AbstractTagStore(object):
    """ This class is an abstract base class that shows how to implement classes
        that manage the storage of tags. """

    def __init__(self, page):
        """ Subclasses don't need to call this method. It is just here to enforce
        them having accept a page argument at least. """
        pass

    def add(self, **kwargs):
        """ Adds a Tag object to the current TagStore. """
        print "Got tag for page %r: %r" % (self.page, kwargs)
        return NotImplemented

    def get_all_tags(self):
        """ Returns a list of all Tag objects associated to this page. """
        return NotImplemented
    
    def clear(self):
        """ Removes all tags. """
        return NotImplemented


class PickleTagStore(AbstractTagStore):
    """ This class manages the storage of tags in pickle files. """

    def __init__(self, page):
        """ Creates a new TagStore that uses pickle files.
        
        @param page: a Page object where the tags should be related to
        """
        
        self.page = page
        self.filename = page.getPagePath('synctags', use_underlay=0, check_create=1, isfile=1)
        self.load()

    def load(self):
        """ Loads the tags from the data file. """
        try:
            datafile = file(self.filename, "rb")
        except IOError:
            self.tags = []
        else:
            self.tags = pickle.load(datafile)
            datafile.close()
    
    def commit(self):
        """ Writes the memory contents to the data file. """
        datafile = file(self.filename, "wb")
        pickle.dump(self.tags, datafile, protocol=pickle.HIGHEST_PROTOCOL)
        datafile.close()

    # public methods ---------------------------------------------------
    def add(self, **kwargs):
        self.tags.append(Tag(**kwargs))
        self.commit()
    
    def get_all_tags(self):
        return self.tags

    def clear(self):
        self.tags = []
        self.commit()

# currently we just have one implementation, so we do not need
# a factory method
TagStore = PickleTagStore