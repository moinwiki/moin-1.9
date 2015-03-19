#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
MoinMoin wiki project -> Google Project Hosting converter

Full of evil antipatterns, incl. Exception exceptions.

@copyright: 2007,2010 MoinMoin:AlexanderSchremmer
@license: GNU GPL, see COPYING for details.
"""

import sys
import re
import urllib2
from urllib import quote
import xmlrpclib
import csv

from MoinMoin.web.contexts import ScriptContext
from MoinMoin.Page import Page

# monkeypatch the formatter to avoid line_anchors:
from MoinMoin.formatter import text_html
text_html.line_anchors = False

request = ScriptContext(None, None)


class DataNotFoundException(Exception): pass


class Task(object):
    def __init__(self, summary, desc, label, hours, mentors, difficulty, types):
        self.summary = summary
        self.label = label
        self.hours = hours
        self.mentors = mentors
        self.difficulty = difficulty
        self.types = types

        page = Page(request, "")
        page.set_raw_body(desc)
        desc = request.redirectedOutput(page.send_page, content_only=1)
        for s, r in [
                ('\n', ' '),
                (' class="line862"', ''),
                (' class="line867"', ''),
                (' class="line874"', ''),
                (' class="line891"', ''),
            ]:
            desc = desc.replace(s, r)
        self.desc = desc

    def __repr__(self):
        return (u"<Task summary=%r label=%r hours=%i mentors=%r difficulty=%r types=%r desc='''%s'''>" % (
            self.summary, self.label, self.hours, self.mentors, self.difficulty,
            self.types, self.desc[:100])).encode("utf-8")


def find_dict_entry(name, text):
    m = re.search(r"^ %s:: (.*)$" % (name, ), text, re.M | re.U)
    if not m:
        raise DataNotFoundException("%s not found" % (name, ))
    return m.groups()[0]


desc_pattern = r"""= Description =
([\s\S]*?)
= Discussion ="""

bugpage_pattern = r"""= Description =
([\s\S]*?)
="""

already_pushed_pages = set([x.strip() for x in """
""".split("\n")])

already_pushed_bugs = set([x.strip() for x in """
""".split("\n")])

gatherers = []

def first(s):
    """ return first word or '' """
    splitted = s.strip().split()
    if splitted:
        return splitted[0]
    else:
        return ''

class Collector(object):
    def is_gatherer(function):
        gatherers.append(function)
        return function

    def __init__(self, url):
        self.url = url
        self.server = xmlrpclib.ServerProxy(url + "?action=xmlrpc2")

    def collect_tasks(self):
        tasks = []
        for gatherer in gatherers:
            new = list(gatherer(self))
            tasks.extend(new)

        return tasks

    @is_gatherer
    def easytodo_pages(self):
        pages = self.server.getAllPagesEx(dict(prefix="EasyToDo/"))
        for page in pages:
            if page in already_pushed_pages:
                continue
            page_contents = self.server.getPage(page)
            try:
                summary = find_dict_entry("Title", page_contents)
                count = int(first(find_dict_entry("Count", page_contents)))
                label = find_dict_entry("Tags", page_contents)
                hours = int(first(find_dict_entry("Duration", page_contents)))
                mentors = find_dict_entry("Mentors", page_contents)
                difficulty = find_dict_entry("Difficulty", page_contents)
                try:
                    types = find_dict_entry("Types", page_contents)
                except DataNotFoundException:
                    # old tasks use "Type"
                    types = find_dict_entry("Type", page_contents)
            except (DataNotFoundException, ValueError), e:
                print >>sys.stderr, "Could not import %r because of %r" % (page, e)
                continue
            desc_m = re.search(desc_pattern, page_contents)
            if not desc_m:
                raise Exception("Could not import %r because Desc not found" % page)
            desc = desc_m.groups()[0]

            for i in range(1, count + 1):
                text = desc
                new_summary = summary
                text += "\n\nYou can discuss this issue in the !MoinMoin wiki: %s" % (self.url + quote(page.encode("utf-8")), )
                if count > 1:
                    text += "\n\nThis issue is available multiple times. This one is %i of %i." % (i, count)
                    new_summary += " %i/%i" % (i, count)
                yield Task(new_summary, text, label, hours, mentors, difficulty, types)

    #@is_gatherer
    def moin_bugs(self):
        pages = [pagename for pagename, contents in self.server.searchPages(r"t:MoinMoinBugs/ r:CategoryEasy\b")]
        for page in pages:
            bug_name = page.replace("MoinMoinBugs/", "")
            if bug_name in already_pushed_bugs:
                continue
            page_contents = self.server.getPage(page)
            m = re.search(bugpage_pattern, page_contents)
            if not m:
                raise Exception("Could not import %r because of bug desc not found" % page)
            desc = m.groups()[0]
            desc = "A user filed a bug report at the MoinMoin site. Here is a short description about the issue. A more detailed description is available at the MoinMoin wiki: %s\n\n" % (self.url + quote(page.encode("utf-8")), ) + desc
            yield Task(bug_name, desc, "Code")

    #@is_gatherer
    def translation_items(self):
        #languages = self.server.getPage(u"EasyToDoTranslation/Languages").strip().splitlines()
        #languages = ["Lithuanian (lt)"]
        languages = []
        for language in languages:
            page = u"EasyToDoTranslation"
            page_contents = self.server.getPage(page)
            page_contents = page_contents.replace("LANG", language)
            summary = find_dict_entry("Summary", page_contents)
            count = int(first(find_dict_entry("Count", page_contents)))
            desc_m = re.search(desc_pattern, page_contents)
            if not desc_m:
                raise Exception("Could not import %r because Desc not found" % page)
            desc = desc_m.groups()[0]
            for i in range(1, count + 1):
                text = desc
                new_summary = summary
                text += "\n\nA more detailed description of this task is available at the MoinMoin wiki: %s" % (self.url + quote(page.encode("utf-8")), )
                if count > 1:
                    text += "\n\nThis task is available multiple times. This one is %i of %i." % (i, count)
                    new_summary += " %i/%i" % (i, count)
                yield Task(new_summary, text, "Translation")


def pull_and_gencsv():
    print >> sys.stderr, "Collecting tasks ..."
    tasks = Collector("http://moinmo.in/").collect_tasks()
    print >> sys.stderr, "Importing %i tasks ..." % (len(tasks), )
    print >> sys.stderr, "\n".join(repr(task) for task in tasks)

    summary_prefix = '' # "[TEST] " # EMPTY FOR PRODUCTION IMPORT!
    tmin, tmax = 0, None
    csvwriter = csv.writer(sys.stdout, delimiter=",", doublequote=True)
    for task in tasks[tmin:tmax]:
        csvwriter.writerow([summary_prefix + task.summary, task.desc, task.hours, task.mentors, task.difficulty, task.types, task.label])


if __name__ == "__main__":
    pull_and_gencsv()

