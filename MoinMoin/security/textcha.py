# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Text CAPTCHAs

    This is just asking some (admin configured) questions and
    checking if the answer is as expected. It is up to the wiki
    admin to setup questions that a bot can not easily answer, but
    humans can. It is recommended to setup SITE SPECIFIC questions
    and not to share the questions with other sites (if everyone
    asks the same questions / expects the same answers, spammers
    could adapt to that).

    TODO:
    * roundtrip the question in some other way:
     * use safe encoding / encryption for the q
     * make sure a q/a pair in the POST is for the q in the GET before
    * make some nice CSS
    * make similar changes to GUI editor

    @copyright: 2007 by MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import re
import random

from MoinMoin import log
logging = log.getLogger(__name__)

from MoinMoin import wikiutil

class TextCha(object):
    """ Text CAPTCHA support """

    def __init__(self, request, question=None):
        """ Initialize the TextCha.

            @param request: the request object
            @param question: see _init_qa()
        """
        self.request = request
        self.user_info = request.user.valid and request.user.name or request.remote_addr
        self.textchas = self._get_textchas()
        self._init_qa(question)

    def _get_textchas(self):
        """ get textchas from the wiki config for the user's language (or default_language or en) """
        request = self.request
        groups = request.groups
        cfg = request.cfg
        user = request.user
        disabled_group = cfg.textchas_disabled_group
        if disabled_group and user.name and user.name in groups.get(disabled_group, []):
            return None
        textchas = cfg.textchas
        if textchas:
            lang = user.language or request.lang
            logging.debug(u"TextCha: user.language == '%s'." % lang)
            if lang not in textchas:
                lang = cfg.language_default
                logging.debug(u"TextCha: fallback to language_default == '%s'." % lang)
                if lang not in textchas:
                    logging.error(u"TextCha: The textchas do not have content for language_default == '%s'! Falling back to English." % lang)
                    lang = 'en'
                    if lang not in textchas:
                        logging.error(u"TextCha: The textchas do not have content for 'en', auto-disabling textchas!")
                        cfg.textchas = None
                        lang = None
        else:
            lang = None
        if lang is None:
            return None
        else:
            logging.debug(u"TextCha: using lang = '%s'" % lang)
            return textchas[lang]

    def _init_qa(self, question=None):
        """ Initialize the question / answer.

         @param question: If given, the given question will be used.
                          If None, a new question will be generated.
        """
        if self.is_enabled():
            if question is None:
                self.question = random.choice(self.textchas.keys())
            else:
                self.question = question
            try:
                self.answer_regex = self.textchas[self.question]
                self.answer_re = re.compile(self.answer_regex, re.U|re.I)
            except KeyError:
                # this question does not exist, thus there is no answer
                self.answer_regex = ur"[Never match for cheaters]"
                self.answer_re = None
                logging.warning(u"TextCha: Non-existing question '%s'. User '%s' trying to cheat?" % (
                                self.question, self.user_info))
            except re.error:
                logging.error(u"TextCha: Invalid regex in answer for question '%s'" % self.question)
                self._init_qa()

    def is_enabled(self):
        """ check if textchas are enabled.

            They can be disabled for all languages if you use textchas = None or = {},
            also they can be disabled for some specific language, like:
            textchas = {
                'en': {
                    'some question': 'some answer',
                    # ...
                },
                'de': {}, # having no questions for 'de' means disabling textchas for 'de'
                # ...
            }
        """
        return not not self.textchas # we don't want to return the dict

    def check_answer(self, given_answer):
        """ check if the given answer to the question is correct """
        if self.is_enabled():
            if self.answer_re is not None:
                success = self.answer_re.match(given_answer.strip()) is not None
            else:
                # someone trying to cheat!?
                success = False
            success_status = success and u"success" or u"failure"
            logging.info(u"TextCha: %s (u='%s', a='%s', re='%s', q='%s')" % (
                             success_status,
                             self.user_info,
                             given_answer,
                             self.answer_regex,
                             self.question,
                             ))
            return success
        else:
            return True

    def _make_form_values(self, question, given_answer):
        question_form = wikiutil.escape(question, True)
        given_answer_form = wikiutil.escape(given_answer, True)
        return question_form, given_answer_form

    def _extract_form_values(self, form=None):
        if form is None:
            form = self.request.form
        question = form.get('textcha-question')
        given_answer = form.get('textcha-answer', u'')
        return question, given_answer

    def render(self, form=None):
        """ Checks if textchas are enabled and returns HTML for one,
            or an empty string if they are not enabled.

            @return: unicode result html
        """
        if self.is_enabled():
            question, given_answer = self._extract_form_values(form)
            if question is None:
                question = self.question
            question_form, given_answer_form = self._make_form_values(question, given_answer)
            result = u"""
<div id="textcha">
<span id="textcha-question">%s</span>
<input type="hidden" name="textcha-question" value="%s">
<input id="textcha-answer" type="text" name="textcha-answer" value="%s" size="20" maxlength="80">
</div>
""" % (wikiutil.escape(question), question_form, given_answer_form)
        else:
            result = u''
        return result

    def check_answer_from_form(self, form=None):
        if self.is_enabled():
            question, given_answer = self._extract_form_values(form)
            self._init_qa(question)
            return self.check_answer(given_answer)
        else:
            return True

