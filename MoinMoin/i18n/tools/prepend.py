#!/usr/bin/python
"""
    prepend some processing instructions to a .po file to be able to put it
    onto moinmaster wiki, letting it get processed by gettext parser

    for f in *.po; do ./prepend.py $f; done
"""
def run():
    import sys, codecs
    fname = sys.argv[1]

    lang = fname.replace('.po_', '').replace('.po', '')

    f = codecs.open(fname, 'r', 'utf-8')
    data = f.read()
    f.close()

    data = u"""\
## Please edit system and help pages ONLY in the moinmaster wiki! For more
## information, please see MoinMaster:MoinPagesEditorGroup.
##master-page:None
##master-date:None
#acl MoinPagesEditorGroup:read,write,delete,revert All:read
#format gettext
#language %s

%s""" % (lang, data)

    f = codecs.open(fname, 'w', 'utf-8')
    f.write(data)
    f.close()

if __name__ == "__main__":
    run()

