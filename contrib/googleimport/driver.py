#!/usr/bin/env python
"""
MoinMoin wiki project -> Google Project Hosting converter

full of evil antipatterns, incl. Exception exceptions

@copyright: 2007 MoinMoin:AlexanderSchremmer
@license: GPL v2

"""
import sys
import re
import urllib2
from urllib import quote
import xmlrpclib

sys.path.append("/home/alexander/dev/python/ghopimport")
#sys.path.append("/srv/moin_tw/moin-1.6/contrib")

from googleimport import googlepush


class DataNotFoundException(Exception): pass


class Task(object):
    def __init__(self, summary, desc, label):
        self.summary = summary
        self.desc = desc
        self.label = label

    def __repr__(self):
        return (u"<Task summary=%r label=%r desc='''%s'''>" % (self.summary, self.label,  self.desc[:100] )).encode("utf-8")


def find_dict_entry(name, text):
    m = re.search(r"^ %s:: (.*)$" % (name, ), text, re.M | re.U)
    if not m:
        raise DataNotFoundException("%s not found" % (name, ))
    return m.groups()[0]

desc_pattern = r"""== Short Description ==
([\s\S]*?)
(= |$)"""

bugpage_pattern = r"""= Description =
([\s\S]*?)
="""

already_pushed_pages = set([x.strip() for x in """
EasyToDo/ExtendFormsOfAdvancedSearch
EasyToDo/ResearchMacOSXPluginSupport
EasyToDo/Research_Python_code_usable_for_filters
EasyToDo/Code_vCard_hCard_Support_For_Wikihomepages
EasyToDo/UserPreferredLanguageStatistics
EasyToDo/CloneWikiPagesByPackagePages
EasyToDo/ResearchLinuxPluginSupport
EasyToDo/ConvertMacrosToNewSyntax
EasyToDo/CaseStudy
EasyToDo/InstallMoinMoinForYourFriends
EasyToDo/JabberBotRefactoring
EasyToDo/ProofreadEnglishDocumentation
EasyToDo/ImplementXEPEntityCapabilities 1
EasyToDo/ImplementXEPEntityCapabilities 3
EasyToDo/ImplementXEPEntityCapabilities 2
EasyToDo/TestInstallDocs
EasyToDo/DesignAMoinMoinTheme
EasyToDo/ImproveStyleOfModernTheme
EasyToDo/ThinkingAloudUsabilityTest
EasyToDo/MakeAScreencast
EasyToDo/IntroduceMoinMoinToYourFriends
EasyToDo/RunJabberBotOnWindows
EasyToDo/ResearchWindowsPluginSupport
EasyToDo/DesignNewIconset
EasyToDo/CreateAPoster
EasyToDo/GermanWikiKurs
EasyToDo/Firefox3CompatibilityCheck
EasyToDo/SearchForMoinMoinIntegration
EasyToDo/AddUsageInfoToMoinCommand
EasyToDo/DumpPagesIntoZip
EasyToDo/ShowAclIndicator
""".split("\n")])

already_pushed_bugs = set([x.strip() for x in """
1.6devFAT32TroubleWithUnderlayFileNames
1.6devMissingRightsI18n
AclBlockMoinDump
ArbitraryInjectionOfErrorMessage
CannotUpdateCreateDrawings
GuiEditorExcelPasteExpatErrorUnboundPrefix
MailAccountDataGivesError
MakeIconLinkLosesAltTitle
ModPyConnectionErrors
MoinDumpTheme
NavigationMacroMultipleRepeat
RenamingUserAllowsOldUsernameToLogin
SubscribeAndUnsubscribeShareSameUrl
TWikiDrawOnDebian
TrivialChangeEasyAccess
WrongAlignedAttachment
XmlRpcPutPageAllowsEmptyPageName
""".split("\n")])

gatherers = []


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
                summary = find_dict_entry("Summary", page_contents)
                count = int(find_dict_entry("Count", page_contents))
                label = find_dict_entry("Label", page_contents)
            except DataNotFoundException, e:
                print "Could not import %r because of %r" % (page, e)
                continue
            desc_m = re.search(desc_pattern, page_contents)
            if not desc_m:
                raise Exception("Desc not found")
            desc = desc_m.groups()[0]
            for i in range(1, count + 1):
                print page
                text = desc
                new_summary = summary
                text += "\n\nA more detailed description of this issue is available at the MoinMoin wiki: %s" % (self.url + quote(page.encode("utf-8")), )
                if count > 1:
                    text += "\n\nThis issue is available multiple times. This one is %i of %i." % (i, count)
                    new_summary += " %i/%i" % (i, count)
                yield Task(new_summary, text, label)

    @is_gatherer
    def moin_bugs(self):
        pages = [pagename for pagename, contents in self.server.searchPages(r"t:MoinMoinBugs/ r:CategoryEasy\b")]
        for page in pages:
            bug_name = page.replace("MoinMoinBugs/", "")
            if bug_name in already_pushed_bugs:
                continue
            page_contents = self.server.getPage(page)
            m = re.search(bugpage_pattern, page_contents)
            if not m:
                raise Exception("bug desc not found")
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
            count = int(find_dict_entry("Count", page_contents))
            desc_m = re.search(desc_pattern, page_contents)
            if not desc_m:
                raise Exception("Desc not found")
            desc = desc_m.groups()[0]
            for i in range(1, count + 1):
                text = desc
                new_summary = summary
                text += "\n\nA more detailed description of this task is available at the MoinMoin wiki: %s" % (self.url + quote(page.encode("utf-8")), )
                if count > 1:
                    text += "\n\nThis task is available multiple times. This one is %i of %i." % (i, count)
                    new_summary += " %i/%i" % (i, count)
                yield Task(new_summary, text, "Translation")


def pull_and_push():
    #project_name = "google-highly-open-participation-moinmoin" # PRODUCTION IMPORT
    project_name = "moin-sandbox" # TEST RUN
    summary_prefix = "" # EMPTY FOR PRODUCTION IMPORT!
    if summary_prefix:
        tmin, tmax = 0, None
    else:
        tmin, tmax = 0, None
    print "Collecting tasks ..."
    tasks = Collector("http://moinmo.in/").collect_tasks()
    print "Importing %i tasks ..." % (len(tasks), )
    print "\n".join(repr(task) for task in tasks)
    argc = len(sys.argv)
    if not (2 <= argc <= 3):
        raise SystemExit("you must supply your username (and optionally your password) as argument(s) to this program")
    user = sys.argv[1]
    if argc == 2:
        password = raw_input("Password for %s:" % user)
    else:
        password = sys.argv[2]


    try:
        googlepush.login(user, password)
    except urllib2.URLError, e:
        print "Ignored exception %r" % (e, )

    i = 0
    for task in tasks[tmin:tmax]:
        i += 1
        print i, repr(task.summary)
        googlepush.push_item(project_name, summary_prefix + task.summary, task.desc, "Open", task.label)


if __name__ == "__main__":
    pull_and_push()

