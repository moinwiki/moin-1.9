# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - jabber bot main file

    This is a bot for notification and simple editing
    operations. Developed as a Google Summer of Code 
    project.

@copyright: 2007 by Karol Nowak <grywacz@gmail.com>
@license: GNU GPL, see COPYING for details.
"""

import sys
from config import JabberConfig
from xmppbot import XMPPBot
from Queue import Queue

def main():
    commands = Queue()
    results = Queue()
    
    try:
        bot = XMPPBot(JabberConfig, commands, results)
        bot.start()
    
    except KeyboardInterrupt, i:
        print i
        sys.exit(0)

if __name__ == "__main__": main()