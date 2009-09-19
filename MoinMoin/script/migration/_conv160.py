# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - migration from 1.5.8 to 1.6.0 (creole link style)

    What it does:

    a) reverse underscore == blank stuff in pagenames (introducing this was a fault)

                   pagename            quoted pagename
       -----------------------------------------------------
       old         MainPage/Sub_Page   MainPage(2f)Sub_Page
       new         MainPage/Sub Page   MainPage(2f)Sub(20)Page    or
       new         MainPage/Sub_Page   MainPage(2f)Sub_Page       (user has to decide by editing rename1.txt)


                   markup
       ----------------------------------------------------
       old         MoinMoin:MainPage/Sub_Page      ../Sub_Page2
       new         [[MoinMoin:MainPage/Sub Page]]  [[../Sub Page2]]


    b) decode url encoded chars in attachment names (and quote the whole fname):

                   markup
       ----------------------------------------------------
       old         attachment:file%20with%20blanks.txt
       new         [[attachment:file with blanks.txt]]

    c) users: move bookmarks from separate files into user profile
    d) users: generate new name[] for lists and name{} for dicts

    e) kill all */MoinEditorBackup pages (replaced by drafts functionality)

    @copyright: 2007 by Thomas Waldmann
    @license: GNU GPL, see COPYING for details.
"""

import os.path
import re
import time
import codecs, urllib, glob

from MoinMoin import config, wikiutil
from MoinMoin.script.migration.migutil import opj, listdir, copy_file, move_file, copy_dir

import mimetypes # this MUST be after wikiutil import!

from _conv160_wiki import convert_wiki

create_rev = True # create a <new> rev with the converted content of <new-1> rev?

def markup_converter(request, pagename, text, renames):
    """ Convert the <text> content of page <pagename>, using <renames> dict
        to rename links correctly. Additionally, convert some changed markup.
    """
    if text.startswith('<?xml'):
        # would be done with xslt processor
        return text

    pis, body = wikiutil.get_processing_instructions(text)
    for pi, val in pis:
        if pi == 'format' and val != 'wiki':
            # not wiki page
            return text

    text = convert_wiki(request, pagename, text, renames)
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
        try:
            lineno = 0
            f = file(self.fname, 'r')
            for line in f:
                lineno += 1
                line = line.replace('\r', '').replace('\n', '')
                if not line.strip(): # skip empty lines
                    continue
                fields = line.split('\t')
                try:
                    timestamp, action, kvpairs = fields[:3]
                    timestamp = int(timestamp)
                    kvdict = wikiutil.parseQueryString(kvpairs)
                    data.append((timestamp, action, kvdict))
                except ValueError, err:
                    # corrupt event log line, log error and skip it
                    print "Error: invalid event log (%s) line %d, err: %s, SKIPPING THIS LINE!" % (self.fname, lineno, str(err))
            f.close()
        except IOError, err:
            # no event-log
            pass
        self.data = data

    def write(self, fname):
        """ write complete event-log to disk """
        if self.data:
            f = file(fname, 'w')
            for timestamp, action, kvdict in self.data:
                pagename = kvdict.get('pagename')
                if pagename and ('PAGE', pagename) in self.renames:
                    kvdict['pagename'] = self.renames[('PAGE', pagename)]
                kvpairs = wikiutil.makeQueryString(kvdict)
                fields = str(timestamp), action, kvpairs
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
        try:
            lineno = 0
            f = file(self.fname, 'r')
            for line in f:
                lineno += 1
                line = line.replace('\r', '').replace('\n', '')
                if not line.strip(): # skip empty lines
                    continue
                fields = line.split('\t') + [''] * 9
                timestamp, rev, action, pagename, ip, hostname, userid, extra, comment = fields[:9]
                try:
                    timestamp = int(timestamp)
                    rev = int(rev)
                except ValueError, err:
                    print "Error: %r has a damaged timestamp or revision number in log line %d [%s] - skipping this entry" % (
                        self.fname, lineno, str(err))
                    continue # ignore this line, do not terminate - to find all those errors in one go
                pagename = wikiutil.unquoteWikiname(pagename)
                data[(timestamp, rev, pagename)] = (timestamp, rev, action, pagename, ip, hostname, userid, extra, comment)
            f.close()
        except IOError, err:
            # no edit-log
            pass
        self.data = data

    def write(self, fname, deleted=False):
        """ write complete edit-log to disk """
        if self.data:
            editlog = self.data.items()
            editlog.sort()
            f = file(fname, "w")
            max_rev = 0
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
                if rev != 99999999:
                    max_rev = max(rev, max_rev)
                revstr = '%08d' % rev
                pagename = wikiutil.quoteWikinameFS(pagename)
                fields = timestamp, revstr, action, pagename, ip, hostname, userid, extra, comment
                log_str = '\t'.join(fields) + '\n'
                f.write(log_str)
            if create_rev and not deleted:
                timestamp = str(wikiutil.timestamp2version(time.time()))
                revstr = '%08d' % (max_rev + 1)
                action = 'SAVE'
                ip = '127.0.0.1'
                hostname = 'localhost'
                userid = ''
                extra = ''
                comment = "converted to 1.6 markup"
                fields = timestamp, revstr, action, pagename, ip, hostname, userid, extra, comment
                log_str = '\t'.join(fields) + '\n'
                f.write(log_str)
            f.close()

    def copy(self, destfname, renames, deleted=False):
        self.renames = renames
        self.read()
        self.write(destfname, deleted)


class PageRev:
    """ a single revision of a page """
    def __init__(self, request, pagename, rev_dir, rev):
        self.request = request
        self.pagename = pagename
        self.rev_dir = rev_dir
        self.rev = rev

    def read(self):
        fname = opj(self.rev_dir, '%08d' % self.rev)
        f = file(fname, "rb")
        data = f.read()
        f.close()
        data = data.decode(config.charset)
        return data

    def write(self, data, rev_dir, convert, rev=None):
        if rev is None:
            rev = self.rev
        if convert:
            data = markup_converter(self.request, self.pagename, data, self.renames)
        fname = opj(rev_dir, '%08d' % rev)
        data = data.encode(config.charset)
        f = file(fname, "wb")
        f.write(data)
        f.close()

    def copy(self, rev_dir, renames, convert=False, new_rev=None):
        self.renames = renames
        data = self.read()
        self.write(data, rev_dir, convert, new_rev)


class Attachment:
    """ a single attachment """
    def __init__(self, request, attach_dir, attfile):
        self.request = request
        self.path = opj(attach_dir, attfile)
        self.name = attfile.decode('utf-8', 'replace')

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
            try:
                self.current = int(current_rev)
            except ValueError:
                print "Error: invalid current file %s, SKIPPING THIS PAGE!" % current_fname
                return
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
                self.revisions[rev] = PageRev(self.request, self.name_old, rev_dir, rev)
        # set deleted status
        self.is_deleted = not self.revisions or self.current not in self.revisions
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
        current = self.current
        if current is not None:
            if create_rev and not self.is_deleted:
                current += 1
            current_fname = opj(page_dir, 'current')
            current_file = file(current_fname, "w")
            current_str = '%08d\n' % current
            current_file.write(current_str)
            current_file.close()
        # copy edit-log
        if self.editlog is not None:
            editlog_fname = opj(page_dir, 'edit-log')
            self.editlog.copy(editlog_fname, self.renames, deleted=self.is_deleted)
        # copy page revisions
        if self.revisions is not None:
            rev_dir = opj(page_dir, 'revisions')
            os.makedirs(rev_dir)
            for rev in self.revlist:
                if create_rev:
                    self.revisions[rev].copy(rev_dir, self.renames)
                else:
                    if int(rev) == self.current:
                        self.revisions[rev].copy(rev_dir, self.renames, convert=True)
                    else:
                        self.revisions[rev].copy(rev_dir, self.renames)
            if create_rev and not self.is_deleted:
                self.revisions[rev].copy(rev_dir, self.renames, convert=True, new_rev=rev+1)

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
        f = codecs.open(fname, 'r', config.charset)
        for line in f:
            line = line.replace(u'\r', '').replace(u'\n', '')
            if not line.strip() or line.startswith(u'#'): # skip empty or comment lines
                continue
            try:
                key, value = line.split(u'=', 1)
            except Exception, err:
                print "Error: User reader can not parse line %r from profile %r (%s)" % (line, fname, str(err))
                continue
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
        f = codecs.open(fname, 'w', config.charset)
        for key, value in self.profile.items():
            if key in (u'subscribed_pages', u'quicklinks'):
                pages = value.split(u'\t')
                for i in range(len(pages)):
                    pagename = pages[i]
                    try:
                        interwiki, pagename = pagename.split(u':', 1)
                    except:
                        interwiki, pagename = u'Self', pagename
                    if interwiki == u'Self' or interwiki == self.request.cfg.interwikiname:
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
        self.complete = {}
        self.renames = {}
        self.complete_fname = opj(self.sdata, 'complete.txt')
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
            if pn.endswith('/MoinEditorBackup'):
                continue # we don't care for old editor backups
            self.complete[('PAGE', pn)] = None
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
                    self.complete[('FILE', pn, fn)] = None
                    if log:
                        # log all strange attachment filenames
                        fn_str = fn.encode('utf-8')
                        self.renames[('FILE', pn, fn)] = None
        self.save_list(self.complete_fname, self.complete)
        self.save_list(self.rename_fname1, self.renames)

    LIST_FIELDSEP = u'|' # in case | makes trouble, one can use \t tab char

    def save_list(self, fname, what):
        what_sorted = what.keys()
        # make sure we have 3-tuples:
        what_sorted = [(k + (None, ))[:3] for k in what_sorted]
        # we only have python 2.3, thus no cmp keyword for the sort() call,
        # thus we need to do it the more complicated way:
        what_sorted = [(pn, fn, rtype) for rtype, pn, fn in what_sorted] # shuffle
        what_sorted.sort() # sort
        what_sorted = [(rtype, pn, fn) for pn, fn, rtype in what_sorted] # shuffle
        f = codecs.open(fname, 'w', 'utf-8')
        for rtype, pn, fn in what_sorted:
            if rtype == 'PAGE':
                line = (rtype, pn, pn)
            elif rtype == 'FILE':
                line = (rtype, pn, fn, fn)
            line = self.LIST_FIELDSEP.join(line)
            f.write(line + u'\n')
        f.close()

    def load_list(self, fname, what):
        f = codecs.open(fname, 'r', 'utf-8')
        for line in f:
            line = line.rstrip()
            if not line:
                continue
            t = line.split(self.LIST_FIELDSEP)
            rtype, p1, p2, p3 = (t + [None]*3)[:4]
            if rtype == u'PAGE':
                what[(str(rtype), p1)] = p2
            elif rtype == u'FILE':
                what[(str(rtype), p1, p2)] = p3
        f.close()

    def pass2(self):
        """ Second, read the (user edited) rename list and do the renamings everywhere. """
        self.read_src()
        #self.load_list(self.complete_fname, self.complete)
        self.load_list(self.rename_fname2, self.renames)
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
        user_re = re.compile(r'^\d+\.\d+(\.\d+)?$')
        userlist = listdir(users_dir)
        userlist = [f for f in userlist if user_re.match(f)]
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
        for pn, page in self.pages.items():
            if pn.endswith('/MoinEditorBackup'):
                continue # we don't care for old editor backups
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


