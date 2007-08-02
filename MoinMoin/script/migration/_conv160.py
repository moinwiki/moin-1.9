#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - migration from base rev 105xxyy

    What it should do when it is ready:

    a) reverse underscore == blank stuff in pagenames (introducing this was a fault)

                   pagename            quoted pagename
       -----------------------------------------------------
       old         MainPage/Sub_Page   MainPage(2f)Sub_Page
       new         MainPage/Sub Page   MainPage(2f)Sub(20)Page    or
       new         MainPage/Sub_Page   MainPage(2f)Sub_Page       (user has to decide by editing rename1.txt)


                   markup
       ----------------------------------------------------
       old         MoinMoin:MainPage/Sub_Page    ../Sub_Page2
       new         MoinMoin:"MainPage/Sub Page"  "../Sub Page2"???? (TODO check if this works)


    b) decode url encoded chars in attachment names (and quote the whole fname):

                   markup
       ----------------------------------------------------
       old         attachment:file%20with%20blanks.txt
       new         attachment:"file with blanks.txt"

    c) users: move bookmarks from separate files into user profile
    d) users: generate new name[] for lists and name{} for dicts

    TODO:
        * process page content / convert markup

    DONE:
        pass 1
        * creating the rename.txt works
        pass 2
        * renaming of pages works
         * renamed pagedirs
         * renamed page names in global edit-log
         * renamed page names in local edit-log
         * renamed page names in event-log
         * renamed pages in user subscribed pages
         * renamed pages in user quicklinks
        * renaming of attachments works
         * renamed attachment files
         * renamed attachment names in global edit-log
         * renamed attachment names in local edit-log
        * migrate separate user bookmark files into user profiles
        * support new dict/list syntax in user profiles

    @copyright: 2007 by Thomas Waldmann
    @license: GNU GPL, see COPYING for details.
"""

import os.path, sys
import codecs, urllib, glob

# Insert THIS moin dir first into sys path, or you would run another version of moin!
sys.path.insert(0, '../../..')

from MoinMoin import config, wikiutil
from MoinMoin.script.migration.migutil import opj, listdir, copy_file, move_file, copy_dir

import mimetypes # this MUST be after wikiutil import!

def markup_converter(text, renames):
    """ Convert the <text> content of some Page, using <renames> dict to rename
        links correctly. Additionally, convert some changed markup.
    """
    if "#format wiki" not in text and "#format" in text:
        return text # this is not a wiki page, leave it as is
    # TODO convert markup of page
    return text


class EventLog:
    def __init__(self, request, fname):
        self.request = request
        self.fname = fname
        self.data = None
        self.renames = {}

    def read(self):
        """ read complete event-log from disk """
        data = []
        f = file(self.fname, 'r')
        for line in f:
            line = line.replace('\r', '').replace('\n', '')
            if not line.strip(): # skip empty lines
                continue
            fields = line.split('\t')
            timestamp, action, kvpairs = fields
            timestamp = int(timestamp)
            kvpairs = kvpairs.split('&')
            kvdict = {}
            for kvpair in kvpairs:
                key, val = kvpair.split('=')
                key = urllib.unquote(key).decode('utf-8')
                val = urllib.unquote(val).decode('utf-8')
                kvdict[key] = val
            data.append((timestamp, action, kvdict))
        self.data = data

    def write(self, fname):
        """ write complete event-log to disk """
        f = file(fname, 'w')
        for timestamp, action, kvdict in self.data:
            kvlist = []
            for k, v in kvdict.items():
                if k == 'pagename' and ('PAGE', v) in self.renames:
                    v = self.renames[('PAGE', v)]
                k = urllib.quote(k.encode('utf-8'))
                v = urllib.quote(v.encode('utf-8'))
                kvlist.append("%s=%s" % (k, v))
            fields = str(timestamp), action, '&'.join(kvlist)
            line = '\t'.join(fields) + '\n'
            f.write(line)
        f.close()

    def copy(self, destfname, renames):
        self.renames = renames
        self.read()
        self.write(destfname)


class EditLog:
    def __init__(self, request, fname):
        self.request = request
        self.fname = fname
        self.data = None
        self.renames = {}

    def read(self):
        """ read complete edit-log from disk """
        data = {}
        f = file(self.fname, 'r')
        for line in f:
            line = line.replace('\r', '').replace('\n', '')
            if not line.strip(): # skip empty lines
                continue
            fields = line.split('\t') + [''] * 9
            timestamp, rev, action, pagename, ip, hostname, userid, extra, comment = fields[:9]
            timestamp = int(timestamp)
            rev = int(rev)
            pagename = wikiutil.unquoteWikiname(pagename)
            data[(timestamp, rev, pagename)] = (timestamp, rev, action, pagename, ip, hostname, userid, extra, comment)
        self.data = data

    def write(self, fname):
        """ write complete edit-log to disk """
        editlog = self.data.items()
        editlog.sort()
        f = file(fname, "w")
        for key, fields in editlog:
            timestamp, rev, action, pagename, ip, hostname, userid, extra, comment = fields
            if action.startswith('ATT'):
                try:
                    fname = urllib.unquote(extra).decode('utf-8')
                except UnicodeDecodeError:
                    fname = urllib.unquote(extra).decode('iso-8859-1')
                if ('FILE', pagename, fname) in self.renames:
                    fname = self.renames[('FILE', pagename, fname)]
                extra = urllib.quote(fname.encode('utf-8'))
            if ('PAGE', pagename) in self.renames:
                pagename = self.renames[('PAGE', pagename)]
            timestamp = str(timestamp)
            rev = '%08d' % rev
            pagename = wikiutil.quoteWikinameFS(pagename)
            fields = timestamp, rev, action, pagename, ip, hostname, userid, extra, comment
            log_str = '\t'.join(fields) + '\n'
            f.write(log_str)
        f.close()

    def copy(self, destfname, renames):
        self.renames = renames
        self.read()
        self.write(destfname)


class PageRev:
    """ a single revision of a page """
    def __init__(self, request, rev_dir, rev):
        self.request = request
        self.rev_dir = rev_dir
        self.rev = rev

    def read(self):
        fname = opj(self.rev_dir, '%08d' % self.rev)
        f = file(fname, "rb")
        data = f.read()
        f.close()
        data = data.decode(config.charset)
        return data

    def write(self, data, rev_dir, rev=None):
        if rev is None:
            rev = self.rev
        data = markup_converter(data, self.renames)
        fname = opj(rev_dir, '%08d' % rev)
        data = data.encode(config.charset)
        f = file(fname, "wb")
        f.write(data)
        f.close()

    def copy(self, rev_dir, renames):
        self.renames = renames
        data = self.read()
        self.write(data, rev_dir)


class Attachment:
    """ a single attachment """
    def __init__(self, request, attach_dir, attfile):
        self.request = request
        self.path = opj(attach_dir, attfile)
        self.name = attfile.decode('utf-8')

    def copy(self, attach_dir):
        """ copy attachment file from orig path to new destination """
        attfile = self.name.encode('utf-8')
        dest = opj(attach_dir, attfile)
        copy_file(self.path, dest)


class Page:
    """ represents a page with all related data """
    def __init__(self, request, pages_dir, qpagename):
        self.request = request
        self.name = wikiutil.unquoteWikiname(qpagename)
        self.name_old = self.name # renaming: still original name when self.name has the new name
        self.page_dir = opj(pages_dir, qpagename)
        self.current = None # int current
        self.editlog = None # dict (see read_editlog)
        self.revlist = None # list of ints (page text revisions)
        self.revisions = None # dict int: pagerev obj
        self.attachments = None # dict of unicode fname: full path
        self.renames = {} # info for renaming pages/attachments

    def read(self):
        """ read a page, including revisions, log, attachments from disk """
        page_dir = self.page_dir
        # read current file
        current_fname = opj(page_dir, 'current')
        if os.path.exists(current_fname):
            current_file = file(current_fname, "r")
            current_rev = current_file.read()
            current_file.close()
            self.current = int(current_rev)
        # read edit-log
        editlog_fname = opj(page_dir, 'edit-log')
        if os.path.exists(editlog_fname):
            self.editlog = EditLog(self.request, editlog_fname)
        # read page revisions
        rev_dir = opj(page_dir, 'revisions')
        if os.path.exists(rev_dir):
            revlist = listdir(rev_dir)
            revlist = [int(rev) for rev in revlist]
            revlist.sort()
            self.revlist = revlist
            self.revisions = {}
            for rev in revlist:
                self.revisions[rev] = PageRev(self.request, rev_dir, rev)
        # read attachment filenames
        attach_dir = opj(page_dir, 'attachments')
        if os.path.exists(attach_dir):
            self.attachments = {}
            attlist = listdir(attach_dir)
            for attfile in attlist:
                a = Attachment(self.request, attach_dir, attfile)
                self.attachments[a.name] = a

    def write(self, pages_dir):
        """ write a page, including revisions, log, attachments to disk """
        if ('PAGE', self.name) in self.renames:
            name_new = self.renames[('PAGE', self.name)]
            if name_new != self.name:
                print "Renaming page %r -> %r" % (self.name, name_new)
                self.name_old = self.name
                self.name = name_new
        qpagename = wikiutil.quoteWikinameFS(self.name)
        page_dir = opj(pages_dir, qpagename)
        os.makedirs(page_dir)
        # write current file
        if self.current is not None:
            current_fname = opj(page_dir, 'current')
            current_file = file(current_fname, "w")
            current_str = '%08d\n' % self.current
            current_file.write(current_str)
            current_file.close()
        # copy edit-log
        if self.editlog is not None:
            editlog_fname = opj(page_dir, 'edit-log')
            self.editlog.copy(editlog_fname, self.renames)
        # copy page revisions
        if self.revisions is not None:
            rev_dir = opj(page_dir, 'revisions')
            os.makedirs(rev_dir)
            for rev in self.revlist:
                self.revisions[rev].copy(rev_dir, self.renames)
        # copy attachments
        if self.attachments is not None:
            attach_dir = opj(page_dir, 'attachments')
            os.makedirs(attach_dir)
            for fn, att in self.attachments.items():
                # we have to check for renames here because we need the (old) pagename, too:
                if ('FILE', self.name_old, fn) in self.renames:
                    fn_new = self.renames[('FILE', self.name_old, fn)]
                    if fn_new != fn:
                        print "Renaming file %r %r -> %r" % (self.name_old, fn, fn_new)
                        att.name = fn_new
                att.copy(attach_dir)

    def copy(self, pages_dir, renames):
            self.renames = renames
            self.read()
            self.write(pages_dir)


class User:
    """ represents a user with all related data """
    def __init__(self, request, users_dir, uid):
        self.request = request
        self.uid = uid
        self.users_dir = users_dir
        self.profile = None
        self.bookmarks = None

    def read(self):
        """ read profile and bookmarks data from disk """
        self.profile = {}
        fname = opj(self.users_dir, self.uid)
        # read user profile
        f = codecs.open(fname, 'r', 'utf-8')
        for line in f:
            line = line.replace(u'\r', '').replace(u'\n', '')
            if not line.strip() or line.startswith(u'#'): # skip empty or comment lines
                continue
            key, value = line.split(u'=', 1)
            self.profile[key] = value
        f.close()
        # read bookmarks
        self.bookmarks = {}
        fname_pattern = opj(self.users_dir, "%s.*.bookmark" % self.uid)
        for fname in glob.glob(fname_pattern):
            f = file(fname, "r")
            bookmark = f.read()
            f.close()
            wiki = fname.replace('.bookmark', '').replace(opj(self.users_dir, self.uid+'.'), '')
            self.bookmarks[wiki] = int(bookmark)
        # don't care about trail

    def write(self, users_dir):
        """ write profile and bookmarks data to disk """
        fname = opj(users_dir, self.uid)
        f = codecs.open(fname, 'w', 'utf-8')
        for key, value in self.profile.items():
            if key in (u'subscribed_pages', u'quicklinks'):
                pages = value.split(u'\t')
                for i in range(len(pages)):
                    pagename = pages[i]
                    try:
                        interwiki, pagename = pagename.split(u':', 1)
                    except:
                        interwiki, pagename = u'Self', pagename
                    # XXX we should check that interwiki == own wikiname
                    if ('PAGE', pagename) in self.renames:
                        pagename = self.renames[('PAGE', pagename)]
                        pages[i] = u'%s:%s' % (interwiki, pagename)
                key += '[]' # we have lists here
                value = u'\t'.join(pages)
                f.write(u"%s=%s\n" % (key, value))
            else:
                f.write(u"%s=%s\n" % (key, value))
        bookmark_entries = [u'%s:%s' % item for item in self.bookmarks.items()]
        key = u"bookmarks{}"
        value = u'\t'.join(bookmark_entries)
        f.write(u"%s=%s\n" % (key, value))
        f.close()
        # don't care about trail

    def copy(self, users_dir, renames):
        self.renames = renames
        self.read()
        self.write(users_dir)


class DataConverter(object):
    def __init__(self, request, src_data_dir, dest_data_dir):
        self.request = request
        self.sdata = src_data_dir
        self.ddata = dest_data_dir
        self.pages = {}
        self.users = {}
        self.renames = {}
        self.rename_fname1 = opj(self.sdata, 'rename1.txt')
        self.rename_fname2 = opj(self.sdata, 'rename2.txt')

    def pass1(self):
        """ First create the rename list - the user has to review/edit it as
            we can't decide about page/attachment names automatically.
        """
        self.read_src()
        # pages
        for pn, p in self.pages.items():
            p.read()
            if not p.revisions:
                continue # we don't care for pages with no revisions (trash)
            if "_" in pn:
                # log all pagenames with underscores
                self.renames[('PAGE', pn)] = None
            if p.attachments is not None:
                for fn in p.attachments:
                    try:
                        fn_str = fn.encode('ascii')
                        log = False # pure ascii filenames are no problem
                    except UnicodeEncodeError:
                        log = True # this file maybe has a strange representation in wiki markup
                    else:
                        if ' ' in fn_str or '%' in fn_str: # files with blanks need quoting
                            log = True
                    if log:
                        # log all strange attachment filenames
                        fn_str = fn.encode('utf-8')
                        self.renames[('FILE', pn, fn)] = None
        self.save_renames()

    def save_renames(self):
        f = codecs.open(self.rename_fname1, 'w', 'utf-8')
        for k in self.renames:
            rtype, pn, fn = (k + (None, ))[:3]
            if rtype == 'PAGE':
                line = u"%s\t%s\t%s\r\n" % (rtype, pn, pn)
            elif rtype == 'FILE':
                line = u"%s\t%s\t%s\t%s\r\n" % (rtype, pn, fn, fn)
            f.write(line)
        f.close()

    def load_renames(self):
        f = codecs.open(self.rename_fname2, 'r', 'utf-8')
        for line in f:
            line = line.rstrip()
            if not line:
                continue
            t = line.split(u'\t')
            rtype, p1, p2, p3 = (t + [None]*3)[:4]
            if rtype == u'PAGE':
                self.renames[(str(rtype), p1)] = p2
            elif rtype == u'FILE':
                self.renames[(str(rtype), p1, p2)] = p3
        f.close()

    def pass2(self):
        """ Second, read the (user edited) rename list and do the renamings everywhere. """
        self.read_src()
        self.load_renames()
        self.write_dest()

    def read_src(self):
        # create Page objects in memory
        pages_dir = opj(self.sdata, 'pages')
        pagelist = listdir(pages_dir)
        for qpagename in pagelist:
            p = Page(self.request, pages_dir, qpagename)
            self.pages[p.name] = p

        # create User objects in memory
        users_dir = opj(self.sdata, 'user')
        userlist = listdir(users_dir)
        userlist = [fn for fn in userlist if not fn.endswith(".trail") and not fn.endswith(".bookmark")]
        for userid in userlist:
            u = User(self.request, users_dir, userid)
            self.users[u.uid] = u

        # create log objects in memory
        self.editlog = EditLog(self.request, opj(self.sdata, 'edit-log'))
        self.eventlog = EventLog(self.request, opj(self.sdata, 'event-log'))

    def write_dest(self):
        self.init_dest()
        # copy pages
        pages_dir = opj(self.ddata, 'pages')
        for page in self.pages.values():
            page.copy(pages_dir, self.renames)

        # copy users
        users_dir = opj(self.ddata, 'user')
        for user in self.users.values():
            user.copy(users_dir, self.renames)

        # copy logs
        self.editlog.copy(opj(self.ddata, 'edit-log'), self.renames)
        self.eventlog.copy(opj(self.ddata, 'event-log'), self.renames)

    def init_dest(self):
        try:
            os.makedirs(self.ddata)
        except:
            pass
        os.makedirs(opj(self.ddata, 'pages'))
        os.makedirs(opj(self.ddata, 'user'))
        copy_dir(opj(self.sdata, 'plugin'), opj(self.ddata, 'plugin'))
        copy_file(opj(self.sdata, 'intermap.txt'), opj(self.ddata, 'intermap.txt'))


