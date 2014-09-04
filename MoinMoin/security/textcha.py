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
     * make sure a q/a pair in the POST is for the q in the GET before
    * make some nice CSS
    * make similar changes to GUI editor

    @copyright: 2007 by MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import re
import random

from time import time

from MoinMoin import log
logging = log.getLogger(__name__)

from MoinMoin import wikiutil
from werkzeug.security import safe_str_cmp as safe_str_equal
from MoinMoin.support.python_compatibility import hmac_new

SHA1_LEN = 40 # length of hexdigest
TIMESTAMP_LEN = 10 # length of timestamp

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
        if self.textchas:
            self.secret = request.cfg.secrets["security/textcha"]
            self.expiry_time = request.cfg.textchas_expiry_time
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

    def _compute_signature(self, question, timestamp):
        signature = u"%s%d" % (question, timestamp)
        return hmac_new(self.secret, signature.encode('utf-8')).hexdigest()

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

    def check_answer(self, given_answer, timestamp, signature):
        """ check if the given answer to the question is correct and within the correct timeframe"""
        if self.is_enabled():
            reason = 'ok'
            if self.answer_re is not None:
                success = self.answer_re.match(given_answer.strip()) is not None
                if not success:
                    reason = 'answer_re did not match'
            else:
                # someone trying to cheat!?
                success = False
                reason = 'answer_re is None'
            if not timestamp or timestamp + self.expiry_time < time():
                success = False
                reason = 'textcha expired'
            try:
                if not safe_str_equal(self._compute_signature(self.question, timestamp), signature):
                    success = False
                    reason = 'signature mismatch'
            except TypeError:
                success = False
                reason = 'TypeError during signature check'

            success_status = success and u"success" or u"failure"
            logging.info(u"TextCha: %s (u='%s', a='%s', re='%s', q='%s', rsn='%s')" % (
                             success_status,
                             self.user_info,
                             given_answer,
                             self.answer_regex,
                             self.question,
                             reason,
                             ))
            return success
        else:
            return True

    def _make_form_values(self, question, given_answer):
        timestamp = time()
        question_form = "%s %d%s" % (
            wikiutil.escape(question, True),
            timestamp,
            self._compute_signature(question, timestamp)
        )
        given_answer_form = wikiutil.escape(given_answer, True)
        return question_form, given_answer_form

    def _extract_form_values(self, form=None):
        if form is None:
            form = self.request.form
        question = form.get('textcha-question')
        signature = None
        timestamp = None
        if question:
            # the signature is the last SHA1_LEN bytes of the question
            signature = question[-SHA1_LEN:]

            # operate on the remainder
            question = question[:-SHA1_LEN]
            try:
                # the timestamp is the next TIMESTAMP_LEN bytes
                timestamp = int(question[-TIMESTAMP_LEN:])
            except ValueError:
                pass
            # there is a space between the timestamp and the question, so take away 1
            question = question[:-TIMESTAMP_LEN - 1]
        given_answer = form.get('textcha-answer', u'')
        return question, given_answer, timestamp, signature

    def render(self, form=None):
        """ Checks if textchas are enabled and returns HTML for one,
            or an empty string if they are not enabled.

            @return: unicode result html
        """
        if self.is_enabled():
            question, given_answer, timestamp, signature = self._extract_form_values(form)
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
            question, given_answer, timestamp, signature = self._extract_form_values(form)
            self._init_qa(question)
            return self.check_answer(given_answer, timestamp, signature)
        else:
            return True

