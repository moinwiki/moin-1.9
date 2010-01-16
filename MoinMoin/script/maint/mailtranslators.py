# -*- coding: iso-8859-1 -*-
"""
MoinMoin - mailtranslators script

@copyright: 2004-2007 MoinMoin:ThomasWaldmann
@license: GPL, see COPYING for details
"""

import sys

from MoinMoin import i18n
from MoinMoin.mail.sendmail import sendmail
from MoinMoin.script import MoinScript

class PluginScript(MoinScript):
    """\
Purpose:
========
This tool allows you to have a message read in from standard input, and
then sent to all translators via email. If you use %(lang)s in the message
it will be replaced with the appropriate language code for the translator.

Detailed Instructions:
======================
General syntax: moin [options] maint mailtranslators [mailtranslators-options]

[options] usually should be:
    --config-dir=/path/to/my/cfg/ --wiki-url=http://wiki.example.org/

[mailtranslators-options] see below:
    0. To send an email to all translaters, from john@smith.com, and with a subject
       of 'Please update your translations!' and a body of 'Please update your language,
       %(lang)s'
       moin ... maint mailtranslators --from-address john@smith.com --subject 'Please update your translations!'
       Please update your language, %(lang)s
       ^D
"""

    def __init__(self, argv, def_values):
        MoinScript.__init__(self, argv, def_values)
        self.parser.add_option(
            "-f", "--from-address", dest="from_address",
            help="use as from: for email."
        )
        self.parser.add_option(
            "-s", "--subject", dest="subject",
            help="use as subject: for email."
        )

    def mainloop(self):
        self.init_request()
        request = self.request

        from_address = unicode(self.options.from_address or "tw-public@gmx.de")
        subject = unicode(self.options.subject or "MoinMoin i18n notification")
        text_template = unicode(sys.stdin.read())

        languages = i18n.wikiLanguages()
        langs = languages.keys()
        langs.remove('en') # nothing to do for english, so remove it
        #langs = ['de', ] # for testing

        if len(text_template) > 10: # do not send mails w/o real content
            for lang in langs:
                to_address = languages[lang]['last-translator']
                rc = None
                if to_address and '***vacant***' not in to_address:
                    text = text_template % locals()
                    rc = sendmail(request, [to_address], subject, text, mail_from=from_address)
                    print lang, repr(from_address), repr(to_address), subject, repr(rc)

