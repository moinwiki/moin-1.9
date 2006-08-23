# -*- coding: ascii -*-
"""
Thread monitor - Check the state of all threads.

Just call activate_hook() as early as possible in program execution.
Then you can trigger the output of tracebacks of all threads
by calling trigger_dump().

@copyright: 2006 Alexander Schremmer <alex AT alexanderweb DOT de>
@license: GNU GPL Version 2
"""

import sys
import threading
import traceback
from time import sleep
from StringIO import StringIO

try:
    set
except:
    from sets import Set as set

# global state
dumping = False
dump_file = None
dumped = set()
to_dump = set()
hook_enabled = False

def dump(label):
    df = dump_file or sys.stderr
    s = StringIO()
    print >>s, "\nDumping thread %s:" % (label, )
    try:
        raise ZeroDivisionError
    except ZeroDivisionError:
        f = sys.exc_info()[2].tb_frame.f_back.f_back
    traceback.print_list(traceback.extract_stack(f, None), s)
    df.write(s.getvalue())

def dump_hook(a, b, c): # arguments are ignored
    global dumping

    if dumping and sys.exc_info()[0] is None:
        thread = threading.currentThread()
        if thread in to_dump:
            dump(repr(thread))
            to_dump.discard(thread)
            dumped.add(thread)
            if not to_dump:
                dumping = False

def trigger_dump(dumpfile=None):
    """ Triggers the dump of the tracebacks of all threads.
        If dumpfile is specified, it is used as the output file. """
    global dumping, dump_file, to_dump

    to_dump = set(threading.enumerate())
    if dumpfile is not None:
        dump_file = dumpfile
    dumping = True

def activate_hook():
    """ Activates the thread monitor hook. Note that this interferes
    with any kind of profiler and some debugging extensions. """
    global hook_enabled

    sys.setprofile(dump_hook)
    threading.setprofile(dump_hook)
    hook_enabled = True

def dump_regularly(seconds):
    """ Dumps the tracebacks every 'seconds' seconds. """
    activate_hook()

    def background_dumper(seconds):
        while 1:
            sleep(seconds)
            trigger_dump()

    threading.Thread(target=background_dumper, args=(seconds, )).start()

