# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - mailtranslators script
    
    read mail text from standard input and send an email to all translators -
    %(lang)s will be replaced by language.

    Usage: moin ... maint mailtranslators
    
    @copyright: 2004-2007 MoinMoin:ThomasWaldmann
    @license: GPL, see COPYING for details
"""

import sys, os

from MoinMoin import config, i18n
from MoinMoin.mail.sendmail import sendmail
from MoinMoin.script import MoinScript

class PluginScript(MoinScript):
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
        request.form = request.args = request.setup_args()

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
                    print lang, from_address, to_address, subject, text
                    rc = sendmail(request, [to_address], subject, text, mail_from=from_address)


