#! /usr/bin/env python

# needs darcs.idyll.org/~t/projects/twill-latest.tar.gz


import sys
from textwrap import wrap

from twill.commands import go, fv, submit, follow, notfind


def login(username, password):
    go('https://www.google.com/accounts/ManageAccount')
    fv('1', 'Email', username)
    fv('1', 'Passwd', password)
    submit()


def push_item(projectname, summary, comment, status, label):
    go('http://code.google.com/p/%s/issues/list' % (projectname, ))
    follow('New Issue')
    fv('3', 'summary', summary)
    fv('3', 'comment', wraptext(comment))
    fv('3', 'status', status)
    fv("3", "labelenter0", label)
    fv("3", "labelenter1", "")

    submit('submit')
    notfind("Letters did not match")


def wraptext(text):
    lines = text.splitlines()
    cur_p = []
    output = []
    for line in lines + [""]:
        if not line and cur_p:
            output.extend(wrap("\n".join(cur_p)) + [""])
            cur_p = []
            continue
        cur_p.append(line)
    return "\n".join(output)

