#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - "moin" is the main script command and calls other stuff as
    a sub-command.

    Usage: moin cmdmodule cmdname [options]
               
    @copyright: 2006 by Thomas Waldmann
    @license: GNU GPL, see COPYING for details.
"""

def run():
    from MoinMoin.script import MoinScript
    MoinScript().run(showtime=0)
    
if __name__ == "__main__":
    # Insert the path to MoinMoin in the start of the path
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(sys.argv[0]), os.pardir, os.pardir))

    run()

