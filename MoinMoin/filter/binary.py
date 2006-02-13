# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - binary file Filter
    
    Processes any binary file and extracts ASCII content from it.

    @copyright: 2006 by ThomasWaldmann MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import os, string

# we don't want or are not able to process those:
blacklist = ('.exe', '.com', '.cab',
             '.iso',
             '.zip', '.gz', '.tgz', '.bz2', '.tb2', )

# builds a list of all characters:
norm = string.maketrans('', '')
# builds a list of all non-alphanumeric characters:
non_alnum = string.translate(norm, norm, string.letters+string.digits) 
# translate table that replaces all non-alphanumeric by blanks:
trans_nontext = string.maketrans(non_alnum, ' '*len(non_alnum))

def execute(indexobj, filename):
    fileext = os.path.splitext(filename)[1]
    if fileext in blacklist:
        return u''
    f = file(filename, "rb")
    data = f.read()
    f.close()
    data = data.translate(trans_nontext)
    data = ' '.join(data.split()) # remove lots of blanks
    return data.decode('ascii')

