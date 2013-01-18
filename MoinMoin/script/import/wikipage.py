# coding: utf-8
"""
MoinMoin - import wiki pages from local files into the wiki.

@copyright: 2010 MoinMoin:PascalVolk,
            2013 MoinMoin:ReimarBauer

@license: GNU GPL, see COPYING for details.
"""
import calendar
import time

from MoinMoin.PageEditor import PageEditor
from MoinMoin.script import MoinScript, fatal, log
from MoinMoin.wikiutil import clean_input, decodeUnknownInput, timestamp2version


class IAmRoot(object):
    def __getattr__(self, name):
        return lambda *args, **kwargs: True


class PluginScript(MoinScript):
    """Purpose:
========
This script imports the wiki page from given file into the wiki.

Detailed Instructions:
======================
General syntax: moin [options] import wikipage [wikipage-options]

[options] usually should be:
    --config-dir=/path/to/cfg --wiki-url=http://wiki.example.org/ --page=Page
"""

    def __init__(self, argv, def_values):
        MoinScript.__init__(self, argv, def_values)
        self.parser.add_option('--acl', dest='acl', default='', metavar='ACL',
                help='Set a specific ACL for the wiki page')
        self.parser.add_option('--author', dest='author', metavar='AUTHOR',
                default='PageImporter',
                help='Use AUTHOR for edit history / RecentChanges')
        self.parser.add_option('--mtime', dest='mtime', metavar='mtime',
                default=None,
                help='Use TIME (YYYY-MM-DD HH:MM:SS) in UTC for edit history / RecentChanges. Default value is the current UTC time')
        self.parser.add_option('--comment', dest='comment', metavar='COMMENT',
                default='', help='COMMENT for edit history / RecentChanges')
        self.parser.add_option('--file', dest='file', default='',
                metavar='FILE', help='Read the wiki page from the given file')
        self.parser.add_option('--no-backup', dest='revision_backup',
                default=True, action='store_false',
                help="Suppress making a page backup per revision")
        self._update_option_help('--page',
                'Name of the wiki page which should be imported')

    def mainloop(self):
        self.init_request()
        request = self.request
        request.user.may = IAmRoot()

        if not self.options.page:
            fatal('You must specify a wiki page name (--page=Page)!')
        if not self.options.file:
            fatal('You must specify a FILE to read from (--file=FILE)!')

        try:
            fileObj = open(self.options.file, 'rb')
        except IOError, err:
            fatal(str(err))
        page_content = decodeUnknownInput(fileObj.read()).rstrip()
        fileObj.close()

        if not self.options.acl:
            acl = ''
        else:
            acl = '#acl %s\n' % self.options.acl
        comment = clean_input(self.options.comment)

        if self.options.mtime:
            mtime = timestamp2version(calendar.timegm(time.strptime(self.options.mtime, "%Y-%m-%d %H:%M:%S")))
        else:
            mtime = timestamp2version(time.time())


        pe = PageEditor(request, self.options.page, do_editor_backup=0,
                        uid_override=self.options.author, mtime=mtime,
                        do_revision_backup=int(self.options.revision_backup))
        try:
            pe.saveText(acl + page_content, 0, comment=comment)
        except PageEditor.Unchanged:
            log("info: wikipage was not modified - ignored update.")
        except PageEditor.SaveError, err:
            log("error: %r" % err)
