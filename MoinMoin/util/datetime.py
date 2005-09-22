# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Date & Time Utilities

    @copyright: 2003 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

# we guarantee that time is always imported!
import time


def tmtuple(tmsecs=None):
    """ Return a time tuple.

        This is currently an alias for gmtime(), but allows later tweaking.
    """
    # avoid problems due to timezones etc. - especially a underflow
    if -86400 <= tmsecs <= 86400: # if we are around 0, we maybe had
        tmsecs = 0                # 0 initially, so reset it to 0.
    return time.gmtime(tmsecs or time.time())

