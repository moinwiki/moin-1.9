# -*- coding: utf-8 -*-
"""
MoinMoin - do global changes to all pages in a wiki.

@copyright: 2004-2006 MoinMoin:ThomasWaldmann
@license: GNU GPL, see COPYING for details.
"""

debug = False

from MoinMoin import PageEditor
from MoinMoin.script import MoinScript

class PluginScript(MoinScript):
    """\
Purpose:
========
This tool allows you to edit all the pages in a wiki.

Detailed Instructions:
======================
General syntax: moin [options] maint globaledit [globaledit-options]

[options] usually should be:
    --config-dir=/path/to/my/cfg/ --wiki-url=http://wiki.example.org/

[globaledit-options] see below:
    0. The changes that will be performed are hardcoded in the function
       do_edit.

    1. This script takes no command line arguments.
"""

    def __init__(self, argv, def_values):
        MoinScript.__init__(self, argv, def_values)

    def do_edit(self, pagename, origtext):
        if pagename in ['LocalSpellingWords', 'LocalBadContent', ]:
            return origtext
        language_line = format_line = masterpage = None
        acl_lines = []
        master_lines = []
        pragma_lines = []
        comment_lines = []
        content_lines = []
        lines = origtext.splitlines()
        header = True
        for l in lines:
            if not l.startswith('#'):
                header = False
            if header:
                if l.startswith('#acl '):
                    acl_lines.append(l)
                elif l.startswith('#language '):
                    language_line = l
                elif l.startswith('#format '):
                    format_line = l
                elif l.startswith('##master-page:'):
                    masterpage = l.split(':', 1)[1].strip()
                    master_lines.append(l)
                elif l.startswith('##master-revision:'):
                    master_lines.append(l)
                elif l.startswith('##master-date:'):
                    master_lines.append(l)
                elif l.startswith('##'):
                    comment_lines.append(l)
                elif l.startswith('#'):
                    pragma_lines.append(l)
            else:
                content_lines.append(l)

        if not language_line:
            language_line = '#language en'
        if not format_line:
            format_line = '#format wiki'
        aclold = '#acl MoinPagesEditorGroup:read,write,delete,revert All:read'
        if aclold in acl_lines:
            acl_lines.remove(aclold)
        if not acl_lines and (
            masterpage is None and not pagename.endswith('Template') or
            masterpage not in ['FrontPage', 'WikiSandBox', ] and not (pagename.endswith('Template') or masterpage.endswith('Template'))):
            acl_lines = ['#acl -All:write Default']
        if not master_lines:
            master_lines = ['##master-page:Unknown-Page', '##master-date:Unknown-Date', ]

        cold = [u"## Please edit system and help pages ONLY in the moinmaster wiki! For more",
                u"## information, please see MoinMaster:MoinPagesEditorGroup.",
        ]
        cnew = [u"## Please edit system and help pages ONLY in the master wiki!",
                u"## For more information, please see MoinMoin:MoinDev/Translation.",
        ]
        for c in cold + cnew:
            if c in comment_lines:
                comment_lines.remove(c)

        comment_lines = cnew + comment_lines

        if content_lines and content_lines[-1].strip(): # not an empty line at EOF
            content_lines.append('')

        if masterpage and masterpage.endswith('Template'):
            if masterpage.startswith('Homepage'):
                # keep the comments on the Homepage...Template, but after the master lines:
                changedtext = master_lines + comment_lines + [format_line, language_line, ] + pragma_lines + content_lines
            else:
                changedtext = master_lines + [format_line, language_line, ] + pragma_lines + content_lines
        else:
            changedtext = comment_lines + master_lines + acl_lines + [format_line, language_line, ] + pragma_lines + content_lines
        changedtext = '\n'.join(changedtext)
        return changedtext

    def mainloop(self):
        if debug:
            import codecs
            origtext = codecs.open('origtext', 'r', 'utf-8').read()
            origtext = origtext.replace('\r\n', '\n')
            changedtext = self.do_edit("", origtext)
            changedtext = changedtext.replace('\n', '\r\n')
            f = codecs.open('changedtext', 'w', 'utf-8')
            f.write(changedtext)
            f.close()
        else:
            self.init_request()
            request = self.request

            # Get all existing pages in the wiki
            pagelist = request.rootpage.getPageList(user='')

            for pagename in pagelist:
                #request = CLI.Request(url=url, pagename=pagename.encode('utf-8'))
                p = PageEditor.PageEditor(request, pagename, do_editor_backup=0)
                origtext = p.get_raw_body()
                changedtext = self.do_edit(pagename, origtext)
                if changedtext and changedtext != origtext:
                    print "Writing %s ..." % repr(pagename)
                    p._write_file(changedtext)

