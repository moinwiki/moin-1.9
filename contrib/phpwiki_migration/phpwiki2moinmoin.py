#! /usr/bin/env python

"""
  Copyright (C) 2004 The Anarcat <anarcat@anarcat.ath.cx>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

 See also http://www.fsf.org

------------------------------------------------------------------------
PhpWikiMoinMoinConverter

= Usage =

Call this script directly from the wiki directory. You must have write
access to ./data and subdirectories to create pages. You will need to
chagne the CONFIGURATION DIRECTIVES, below, to have this script
connect properly to the MySQL database.

= Special considerations =

This script will happily destroy existing wikis if it feels like it,
so backups are of course advised before performing a phptomy. Note
that this script attempts to use saveText() to create the new pages,
and will not save over existing pages (see editExistingPages, below),
so it should still be pretty safe to run. But, again, backup or die.

= Limitations =

This script is also crucially incomplete, and lacks several phpwiki
features. Some are due to inherent limitations of MoinMoin, others are
due to the inherent ambiguity of the phpwiki syntax. In particular,
links within headers are translated but will not be parsed by
MoinMoin. Also, bold, italic, definition lists, <code> tags and newstyle
tables are not converted. See MoinMoin:PhpWikiMoinMoinConverter for
details and updates.

= Dependencies =

This script needs MySQL access, so the python-mysqldb (debian) package
(or equivalent) should be installed.
"""

# CONFIGURATION DIRECTIVES
#
# Those are the directives that allows this script to access the MySQL
# database containing the phpwiki
host = "localhost"
db = "wiki"
user = "wiki"
passwd = "wiki"
#
# This is a part of an SQL request (part of the WHERE, actually) that
# allows you to select which pages get moved over
#
# do only those pages:
pagename = ""
# Example:
#pagename = "pagename='ParseTest' AND"
#
# the path to the moinmoin wiki, leave empty if you know what you're
# doing
wikipath = '/var/local/lib/wiki'

# by default, we do not edit existing wiki pages, to avoid conflict
#
# this will override this behavior and allow the edition of those
# pages. normally, a new revision should be created, so this is pretty
# safe.
editExistingPages = 0

#
# END OF CONFIGURATION DIRECTIVES
#
# XXX: the interactive way will be something like this:
#
# print "I will need the host/database/username/password of the phpwiki"
# print "Host:",
# host = raw_input()
# print "Database:",
# db = raw_input()
# print "Username:",
# user = raw_input()
# print "Password:",
# passwd = getpass()
# print "Pagename:"
# pagename = raw_input()
#
# But right now this script DOES NOT COMPLETELY WORK, so it often has
# to be ran and reran.

import MySQLdb
import re
import os
import sys

if wikipath:
        sys.path.append(wikipath)

from MoinMoin.PageEditor import PageEditor
from MoinMoin.request.CLI import Request

# the block parser deals with the whole text to be converted
#
# it will call the line parser for each line in the text
#
# markup is just passed along to lineparser
def blockparser(text, markup):
        result = []
        pre = 0
        for line in text.split("\n"):
                # pre mode is where no parsing takes place
                #
                # XXX: we actually treat <pre> and <verbatim> the same
                # here, but we should not: they are different
                # constructs with different semantics in phpwiki.
                #
                # <verbatim> is the direct equivalent of Moin's {{{ }}}
                #
                # <pre> is almost that with the difference that it
                # allows linking
                if pre:
                        # look for the end of the pre tag
                        match = re.compile('^(.*?)[ \t\r\f\v]*(?<!~)</'+pre+'>(.*)$').search(line)
                        if match:
                                # don't add the groups as lines if they are empty
                                if match.group(1) != '':
                                        result += [match.group(1)]
                                result += ['}}}']
                                if match.group(2) != '':
                                        result += [lineparser(match.group(2), markup)]
                                pre = 0
                        else:
                                # don't parse pre data
                                result += [line]
                else:
                        # look for a pre tag
                        match = re.compile('^(.*)(?<!~)<(verbatim|pre)>[ \t\r\f\v]*(.*?)$').search(line)
                        if match:
                                # found a starting pre tag
                                #
                                # remember it, parse what's before but
                                # not what's after
                                pre = match.group(2)
                                if match.group(1) != '':
                                        result += [lineparser(match.group(1), markup)]
                                result += ['{{{']
                                if match.group(3) != '':
                                        result += [match.group(3)]

                        else:
                                # "common case": normal line parsing
                                result += [lineparser(line, markup)]

        text = "\n".join(result)
        return text

# the line parser deals with text as handed to it by blockparser
#
# the blockparser should send the text line per line to the line
# parser
#
# markup is 1 (old style) or 2 (new style)
def lineparser(text, markup):
        # headlines
        p = re.compile('^!!!(.*)$', re.MULTILINE)
        text = p.sub(r'= \1 =', text)
        p = re.compile('^!!(.*)$', re.MULTILINE)
        text = p.sub(r'== \1 ==', text)
        p = re.compile('^!(.*)$', re.MULTILINE)
        text = p.sub(r'=== \1 ===', text)

        # pictures
        p = re.compile('^\s*\[(http:.*(png|jpg|gif))\]', re.MULTILINE)
        text = p.sub(r'\n\1', text)

        # links
        # the links like [http://]
        p = re.compile('(?<!~)\[(http|https|ftp|nntp|news|mailto|telnet|file)(://.*?)\]', re.MULTILINE)
        text = p.sub(r'\1\2', text)

        # the [links like this]
        p = re.compile('(?<!~|#)\[([^]\|]*)\]', re.MULTILINE)
        text = p.sub(r'["\1"]', text)

        # links like [foo | http://...]
        q = re.compile('(?<!~|#)\[([^]#]*?)\s*\|\s*([^]#\s]+?://[^]\s]+?)\]', re.MULTILINE)
        text = q.sub(r'[\2 \1]', text)

        # [fooo | bar]
        p = re.compile('(?<!~|#)\[([^]]*?)\s*\|\s*([^]\s]+?)\]', re.MULTILINE)
        text = p.sub(r'[:\2:\1]', text)

        # XXX: the following constructs are broken. I don't know how
        # to express that in Moin
        # [OtherPage#foo] [named|OtherPage#foo]

        # anchors
        # #[foo] => [[Anchor(foo)]]foo
        # #[|foo] => [[Anchor(foo)]]
        # #[howdy|foo] => [[Anchor(foo)]]howdy
        #
        # rest should just go along
        p = re.compile('#\[([^]|]*)\]', re.MULTILINE)
        text = p.sub(r'[[Anchor(\1)]]\1', text)
        p = re.compile('#\[\|+([^]\|]*)\]', re.MULTILINE)
        text = p.sub(r'[[Anchor(\1)]]', text)
        p = re.compile('#\[([^]\|]*)\|+([^]\|]*)\]', re.MULTILINE)
        text = p.sub(r'[[Anchor(\2)]]\1', text)

        # indented text
        # this might work for old style
        if markup == 1:
                p = re.compile('^ (.*)$')
                text = p.sub(r'{{{\n\1\n}}}', text)

        # lists (regexp taken from phpwiki/lib/BlockParser.php:1.37)
        p = re.compile('^\ {0,4}\
                (?: \+\
                  | -(?!-)\
                  | [o](?=\ )\
                  | [*] (?!(?=\S)[^*]*(?<=\S)[*](?:\\s|[-)}>"\'\\/:.,;!?_*=]) )\
                )\ *(?=\S)', re.MULTILINE|re.VERBOSE)
        text = p.sub(r' * ', text)
        p = re.compile(' {0,4}(?:\\# (?!\[.*\])) *(?=\S)', re.MULTILINE)
        text = p.sub(r' 1. ', text)

        if markup == 1:
                # bold (old style)
                p = re.compile('__(\w*)', re.MULTILINE)
                text = p.sub(r"'''\1", text)
                p = re.compile('(\w*)__', re.MULTILINE)
                text = p.sub(r"\1'''", text)
                # emphasis is the same
        else:
                # XXX: this doesn't do anything yet
                #
                # translated from getStartRegexp() in
                # phpwiki/lib/InlineParser.php:418
                i = "_ (?! _)"
                b = "\\* (?! \\*)"
                tt = "= (?! =)"

                # any of the three.
                any = "(?: " + i + "|" + b + "|" + tt + ")"

                # Any of [_*=] is okay if preceded by space or one of [-"'/:]
                # _ or * is okay after = as long as not immediately followed by =
                # any delimiter okay after an opening brace ( [{<(] )
                # as long as it's not immediately followed by the matching closing
                # brace.
                start = "(?:" + \
                        "(?<= \\s|^|[-\"'\\/:]) " + any + "|" + \
                        "(?<= =) (?: " + i + "|" + b + ") (?! =)|" + \
                        "(?<= _) (?: " + b + "|" + tt + ") (?! _)|" + \
                        "(?<= \\*) (?: " + i + "|" + tt + ") (?! \\*)|" + \
                        "(?<= { ) " + any + " (?! } )|" + \
                        "(?<= < ) " + any + " (?! > )|" + \
                        "(?<= \\( ) " + any + " (?! \\) )" + \
                        ")"

                # Any of the above must be immediately followed by non-whitespace.
                start_regexp = start + "(?= \S)"


        # PLUGINS

        # calendar plugin
        p = re.compile('<\?plugin Calendar month=(\d*) year=(\d*)\?>', re.MULTILINE)
        text = p.sub(r'[[MonthCalendar(,\2,\1)]]', text)
        p = re.compile('<\?plugin Calendar\?>', re.MULTILINE)
        text = p.sub(r'[[MonthCalendar]]', text)

        # BackLinks
        p = re.compile('<\?plugin\s+BackLinks.*?\?>', re.MULTILINE)
        text = p.sub(r"[[FullSearch()]]", text)

        # FullSearch
        p = re.compile('<\?plugin\s+FullTextSearch.*?(s=.*?)?\?>', re.MULTILINE)
        text = p.sub(r'[[FullSearch()]]', text)

        # RecentChanges
        p = re.compile('<\?plugin\s+RecentChanges.*?\?>', re.MULTILINE)
        text = p.sub(r'[[RecentChanges]]', text)

        # tables (old style)
        p = re.compile('^(\|.*)$', re.MULTILINE)
        text = p.sub(r'\1|', text)
        p = re.compile('\|', re.MULTILINE)
        text = p.sub(r'||', text)
        p = re.compile('\|\|<', re.MULTILINE)
        text = p.sub(r'||<(>', text)
        p = re.compile('\|\|>', re.MULTILINE)
        text = p.sub(r'||<)>', text)

        if markup == 2:
                # moinmoin tables are on one line
                p = re.compile('\|\|\s*\n', re.MULTILINE)
                text = p.sub(r'||', text)

        # mailto
        p = re.compile('mailto:', re.MULTILINE)
        text = p.sub(r'', text)

        # line breaks
        p = re.compile('(?<!~)%%%', re.MULTILINE)
        text = p.sub(r'[[BR]]', text)

        # unescape
        # This must stay the last filter or things will break real bad
        p = re.compile('~(~?)', re.MULTILINE)
        text = p.sub(r'\1', text)

        return text

# "secure" password prompting
def getpass():
        os.system("stty -echo")
        passwd = ''
        try:
                passwd = raw_input()
        except KeyboardInterrupt:
                os.system("stty echo")
                raise

        os.system("stty echo")
        return passwd

# main loop.

# connect to the database and fetch phpwiki pages
db = MySQLdb.connect(
                host=host,
                db=db,
                user=user,
                passwd=passwd,
        )
cursor = db.cursor()

stmt = "SELECT pagename,content,versiondata FROM page,recent,version WHERE " + pagename + \
       " page.id=version.id AND version.id=recent.id AND version=latestversion" + \
       " ORDER BY pagename"
cursor.execute(stmt)

# loop over the matching phpwiki pages
result = cursor.fetchall()
for pagename, content, versiondata in result:
        utf8pagename = unicode(pagename, 'latin-1')
        request = Request(utf8pagename)
        page = PageEditor(utf8pagename, request)
        print pagename,
        # overwriting pages if selecting only some
        if not editExistingPages and page.exists():
                print " already exists, skipping"
                continue

        # find out in the serialized field what markup type (old
        # style?) this page is in
        match = re.compile('s:6:"markup";s:[0-9]*:"([0-9]*)";').search(versiondata)
        if match is not None:
                # markup is 1 (old style) or 2 (new style)
                markup = match.group(1)
        else:
                # default to "new" markup style
                markup = 2

        # show some progress
        #
        # (ternary operator in python: http://c2.com/cgi/wiki?PythonIdioms)
        print (markup == 2 and [""] or ["(old style)"])[0],

        # do the actual parsing of this page and save it
        text = blockparser(content, markup)
        try:
                err = page.saveText(unicode(text, 'latin-1'), '0')
        # the exceptions thrown by saveText are errors or messages, so
        # just print both
        except Exception, msg:
                print msg,
        else:
                if err:
                        print err,

        # the EOL
        print

db.close

