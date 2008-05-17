# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - text/xml file Filter

    @copyright: 2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import re

from MoinMoin import log
logging = log.getLogger(__name__)

from MoinMoin.filter.text import execute as textfilter

rx_stripxml = re.compile("<[^>]*?>", re.DOTALL|re.MULTILINE)

def execute(indexobj, filename):
    data = textfilter(indexobj, filename)
    try:
        data = " ".join(rx_stripxml.sub(" ", data).split())
    except RuntimeError, err:
        logging.error(str(err))
        data = ""
    return data

