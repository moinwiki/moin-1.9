"""
MoinMoin - Push files into the wiki.

This script pushes files from a directory into the wiki. It is usable in order
to mirror IRC logs for example.

    @copyright: 2005 by MoinMoin:AlexanderSchremmer
    @license: GNU GPL, see COPYING for details.
"""

### Configuration
# the request URL, important for farm configurations
url = "moinmoin.wikiwikiweb.de/"

# the author, visible in RecentChanges etc.
author = "WikiSyncronisationDaemon"

# the directory that should be pushed
local_dir = '/home/aschremmer/channel-logging/logs/ChannelLogger/freenode/#moin-dev'

# basepage of the pushed files
base_page = 'MoinMoinChat/Logs/'

# this function generates a pagename from the file name
def filename_function(filename):
    splitted = filename.split('.')
    return '/'.join(splitted[0] + [x.replace('-', '/') for x in splitted[0:-1]])
### end of configuration

import os, sys

from MoinMoin import wikiutil
from MoinMoin.request import RequestCLI
from MoinMoin.PageEditor import PageEditor

def decodeLinewise(text):
    resultList = []

    for line in text.splitlines():
        try:
            decoded_line = line.decode("utf-8")
        except UnicodeDecodeError:
            decoded_line = line.decode("iso-8859-1")
        resultList.append(decoded_line)

    return '\n'.join(resultList)

request = RequestCLI(url=url) #pagename necessary here?

for root, dirs, files in os.walk(local_dir):
    files.sort()
    for filename in files[:-1]: # do not push the last file as it is constantly written to
        pagename = base_page + filename_function(filename)
        print "Pushing %r as %r" % (filename, pagename)
        p = PageEditor(request, pagename,
                       do_editor_backup=0, uid_override=author)
        if p.exists():
            continue
                    
        fileObj = open(os.path.join(root, filename), 'rb')
        try:
            p.saveText("#format plain\n" + decodeLinewise(fileObj.read()), 0)
        except PageEditor.SaveError, e:
            print "Got %r" % (e, )
        fileObj.close()

print "Finished."
