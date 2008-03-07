# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - tests for the XMPP component

    @copyright: 2007 by Karol Nowak <grywacz@gmail.com>
    @license: GNU GPL, see COPYING for details.
"""

import py
from Queue import Queue

try:
    import pyxmpp
    from jabberbot.xmppbot import XMPPBot
except ImportError:
    py.test.skip("Skipping jabber bot tests - pyxmpp is not installed")

import jabberbot.commands as commands
from jabberbot.config import BotConfig

class TestXMPPBotCommands:
    """Various tests for the XMPP bot receiving commands from Wiki"""

    def setup_class(self):
        self.from_xmlrpc = Queue()
        self.to_xmlrpc = Queue()
        self.bot = XMPPBot(BotConfig, self.from_xmlrpc, self.to_xmlrpc)

    def setup_method(self, method):
        self.called = False
        self.bot.send_message = self.dummy_method
        self.bot.ask_for_subscription = self.dummy_method
        self.bot.remove_subscription = self.dummy_method

    def dummy_method(self, *args, **kwargs):
        self.called = True

    def testNotificationCommand(self):
        """Check if send_message is triggered for tested commands"""

        data = {'text': 'Some notification', 'subject': 'It is optional', 'url_list': []}
        cmds = []
        cmds.append(commands.NotificationCommand(["dude@example.com"], data, True))
        cmds.append(commands.NotificationCommandI18n(["dude@example.com"], data, True))
        cmds.append(commands.GetPage("dude@example.com", "TestPage"))
        cmds.append(commands.GetPageHTML("dude@example.com", "TestPage"))

        tmp_cmd = commands.GetPageList("dude@example.com")
        tmp_cmd.data = ""
        cmds.append(tmp_cmd)

        tmp_cmd = commands.GetPageInfo("dude@example.com", "TestPage")
        tmp_cmd.data = {'author': 'dude', 'lastModified': '200708060T34350', 'version': 42}
        cmds.append(tmp_cmd)

        for cmd in cmds:
            self.called = False
            self.bot.handle_command(cmd)
            if not self.called:
                print "The bot should send a notification when %s arrives!" % (cmd.__class__.__name__, )
                raise Exception()

    def testRosterCommands(self):
        """Test if appropriate functions are called for (Add|Remove)JIDFromRosterCommand"""

        command = commands.AddJIDToRosterCommand("dude@example.com")
        self.bot.handle_command(command)

        if not self.called:
            print "The bot should do something when AddJIDToRosterCommand arrives!"
            raise Exception()

        self.called = False
        command = commands.RemoveJIDFromRosterCommand("dude@example.com")
        self.bot.handle_command(command)

        if not self.called:
            print "The bot should do something when RemoveJIDFromRosterCommand arrives!"
            raise Exception()

    def testInternalHelp(self):
        """Check if there's help for every known command"""

        commands = self.bot.internal_commands + self.bot.xmlrpc_commands.values()
        for cmd in commands:
            print "There should be help on %s command!" % (cmd, )
            assert self.bot.help_on("dude@example.com", cmd)
