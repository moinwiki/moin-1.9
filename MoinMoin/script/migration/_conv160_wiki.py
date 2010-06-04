# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - convert content in 1.5.8 wiki markup to 1.6.0 style
               by using a modified 1.5.8 parser as translator.

    Assuming we have this "renames" map:
    -------------------------------------------------------
    'PAGE', 'some_page'        -> 'some page'
    'FILE', 'with%20blank.txt' -> 'with blank.txt'

    Markup transformations needed:
    -------------------------------------------------------
    ["some_page"]           -> [[some page]] # renamed
    [:some_page:some text]  -> [[some page|some text]]
    [:page:text]            -> [[page|text]]
                               (with a page not being renamed)

    attachment:with%20blank.txt -> [[attachment:with blank.txt]]
    attachment:some_page/with%20blank.txt -> [[attachment:some page/with blank.txt]]
    The attachment processing should also urllib.unquote the filename (or at
    least replace %20 by space) and put it into "quotes" if it contains spaces.

    @copyright: 2007 MoinMoin:JohannesBerg,
                2007 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import re

from MoinMoin import i18n
i18n.wikiLanguages = lambda: {}

from MoinMoin import config, wikiutil, macro
from MoinMoin.action import AttachFile
from MoinMoin.Page import Page
from MoinMoin.support.python_compatibility import rsplit

from text_moin158_wiki import Parser

def convert_wiki(request, pagename, intext, renames):
    """ Convert content written in wiki markup """
    noeol = False
    if not intext.endswith('\r\n'):
        intext += '\r\n'
        noeol = True
    c = Converter(request, pagename, intext, renames)
    result = request.redirectedOutput(c.convert, request)
    if noeol and result.endswith('\r\n'):
        result = result[:-2]
    return result


STONEAGE_IMAGELINK = False # True for ImageLink(target,image), False for ImageLink(image,target)

# copied from moin 1.6.0 macro/ImageLink.py (to be safe in case we remove ImageLink some day)
# ... and slightly modified/refactored for our needs here.
# hint: using parse_quoted_separated from wikiutil does NOT work here, because we do not have
#       quoted urls when they contain a '=' char in the 1.5 data input.
def explore_args(args):
    """ explore args for positional and keyword parameters """
    if args:
        args = args.split(',')
        args = [arg.strip() for arg in args]
    else:
        args = []

    kw_count = 0
    kw = {} # keyword args
    pp = [] # positional parameters

    kwAllowed = ('width', 'height', 'alt')

    for arg in args:
        if '=' in arg:
            key, value = arg.split('=', 1)
            key_lowerstr = str(key.lower())
            # avoid that urls with "=" are interpreted as keyword
            if key_lowerstr in kwAllowed:
                kw_count += 1
                kw[key_lowerstr] = value
            elif not kw_count and '://' in arg:
                # assuming that this is the image
                pp.append(arg)
        else:
            pp.append(arg)

    if STONEAGE_IMAGELINK and len(pp) >= 2:
        pp[0], pp[1] = pp[1], pp[0]

    return pp, kw


class Converter(Parser):
    def __init__(self, request, pagename, raw, renames):
        self.pagename = pagename
        self.raw = raw
        self.renames = renames
        self.request = request
        self._ = None
        self.in_pre = 0

        self.formatting_rules = self.formatting_rules % {'macronames': u'|'.join(['ImageLink', ] + macro.getNames(self.request.cfg))}

    # no change
    def return_word(self, word):
        return word
    _emph_repl = return_word
    _emph_ibb_repl = return_word
    _emph_ibi_repl = return_word
    _emph_ib_or_bi_repl = return_word
    _u_repl = return_word
    _strike_repl = return_word
    _sup_repl = return_word
    _sub_repl = return_word
    _small_repl = return_word
    _big_repl = return_word
    _tt_repl = return_word
    _tt_bt_repl = return_word
    _remark_repl = return_word
    _table_repl = return_word
    _tableZ_repl = return_word
    _rule_repl = return_word
    _smiley_repl = return_word
    _smileyA_repl = return_word
    _ent_repl = return_word
    _ent_numeric_repl = return_word
    _ent_symbolic_repl = return_word
    _heading_repl = return_word
    _email_repl = return_word
    _notword_repl = return_word
    _indent_repl = return_word
    _li_none_repl = return_word
    _li_repl = return_word
    _ol_repl = return_word
    _dl_repl = return_word
    _comment_repl = return_word

    # translate pagenames using pagename translation map

    def _replace(self, key):
        """ replace a item_name if it is in the renames dict
            key is either a 2-tuple ('PAGE', pagename)
            or a 3-tuple ('FILE', pagename, filename)
        """
        current_page = self.pagename
        item_type, page_name, file_name = (key + (None, ))[:3]
        abs_page_name = wikiutil.AbsPageName(current_page, page_name)
        if item_type == 'PAGE':
            key = (item_type, abs_page_name)
            new_name = self.renames.get(key)
            if new_name is None:
                # we don't have an entry in rename map - apply the same magic
                # to the page name as 1.5 did (" " -> "_") and try again:
                abs_magic_name = abs_page_name.replace(u' ', u'_')
                key = (item_type, abs_magic_name)
                new_name = self.renames.get(key)
                if new_name is None:
                    # we didn't find it under the magic name either -
                    # that means we do not rename it!
                    new_name = page_name
            if new_name != page_name and abs_page_name != page_name:
                # we have to fix the (absolute) new_name to be a relative name (as it was before)
                new_name = wikiutil.RelPageName(current_page, new_name)
        elif item_type == 'FILE':
            key = (item_type, abs_page_name, file_name)
            new_name = self.renames.get(key)
            if new_name is None:
                # we don't have an entry in rename map - apply the same magic
                # to the page name as 1.5 did (" " -> "_") and try again:
                abs_magic_name = abs_page_name.replace(u' ', u'_')
                key = (item_type, abs_magic_name, file_name)
                new_name = self.renames.get(key)
                if new_name is None:
                    # we didn't find it under the magic name either -
                    # that means we do not rename it!
                    new_name = file_name
        return new_name

    def _replace_target(self, target):
        target_and_anchor = rsplit(target, '#', 1)
        if len(target_and_anchor) > 1:
            target, anchor = target_and_anchor
            target = self._replace(('PAGE', target))
            return '%s#%s' % (target, anchor)
        else:
            target = self._replace(('PAGE', target))
            return target

    # markup conversion

    def _macro_repl(self, word):
        # we use [[...]] for links now, macros will be <<...>>
        macro_rule = ur"""
            \[\[
            (?P<macro_name>\w+)
            (\((?P<macro_args>.*?)\))?
            \]\]
        """
        word = unicode(word) # XXX why is word not unicode before???
        m = re.match(macro_rule, word, re.X|re.U)
        macro_name = m.group('macro_name')
        macro_args = m.group('macro_args')
        if macro_name == 'ImageLink':
            fixed, kw = explore_args(macro_args)
            #print "macro_args=%r" % macro_args
            #print "fixed=%r, kw=%r" % (fixed, kw)
            image, target = (fixed + ['', ''])[:2]
            if image is None:
                image = ''
            if target is None:
                target = ''
            if '://' not in image:
                # if it is not a URL, it is meant as attachment
                image = u'attachment:%s' % image
            if not target:
                target = image
            elif target.startswith('inline:'):
                target = 'attachment:' + target[7:] # we don't support inline:
            elif target.startswith('wiki:'):
                target = target[5:] # drop wiki:
            image_attrs = []
            alt = kw.get('alt') or ''
            width = kw.get('width')
            if width is not None:
                image_attrs.append(u"width=%s" % width)
            height = kw.get('height')
            if height is not None:
                image_attrs.append(u"height=%s" % height)
            image_attrs = u", ".join(image_attrs)
            if image_attrs:
                image_attrs = u'|' + image_attrs
            if alt or image_attrs:
                alt = u'|' + alt
            result = u'[[%s|{{%s%s%s}}]]' % (target, image, alt, image_attrs)
        else:
            if macro_args:
                macro_args = u"(%s)" % macro_args
            else:
                macro_args = u''
            result = u"<<%s%s>>" % (macro_name, macro_args)
        # XXX later check whether some to be renamed pagename is used as macro param
        return result

    def _word_repl(self, word, text=None):
        """Handle WikiNames."""
        if not text:
            return word
        else: # internal use:
            return '[[%s|%s]]' % (word, text)

    def _wikiname_bracket_repl(self, word):
        """Handle special-char wikinames."""
        pagename = word[2:-2]
        if pagename:
            pagename = self._replace(('PAGE', pagename))
            return '[[%s]]' % pagename
        else:
            return word

    def _interwiki_repl(self, word):
        """Handle InterWiki links."""
        wikitag, wikiurl, wikitail, wikitag_bad = wikiutil.resolve_wiki(self.request, word)
        if wikitag_bad:
            return word
        else:
            wikiname, pagename = word.split(':', 1)
            pagename = wikiutil.url_unquote(pagename) # maybe someone has used %20 for blanks in pagename
            camelcase = wikiutil.isStrictWikiname(pagename)
            if wikiname in ('Self', self.request.cfg.interwikiname):
                pagename = self._replace(('PAGE', pagename))
                if camelcase:
                    return '%s' % pagename # optimize special case
                else:
                    return '[[%s]]' % pagename # optimize special case
            else:
                if ' ' in pagename: # we could get a ' '  by urlunquoting
                    return '[[%s:%s]]' % (wikiname, pagename)
                else:
                    return '%s:%s' % (wikiname, pagename)

    def interwiki(self, url_and_text):
        if len(url_and_text) == 1:
            url = url_and_text[0]
            text = ''
        else:
            url, text = url_and_text
            text = '|' + text

        # keep track of whether this is a self-reference, so links
        # are always shown even the page doesn't exist.
        scheme, url = url.split(':', 1)
        wikiname, pagename = wikiutil.split_wiki(url)
        if (url.startswith(wikiutil.CHILD_PREFIX) or # fancy link to subpage [wiki:/SubPage text]
            Page(self.request, url).exists()): # fancy link to local page [wiki:LocalPage text]
            pagename = wikiutil.url_unquote(url)
            pagename = self._replace_target(pagename)
            return '[[%s%s]]' % (pagename, text)
        if wikiname in ('Self', self.request.cfg.interwikiname, ''): # [wiki:Self:LocalPage text] or [:LocalPage:text]
            pagename = wikiutil.url_unquote(pagename)
            pagename = self._replace_target(pagename)
            return '[[%s%s]]' % (pagename, text)

        wikitag, wikiurl, wikitail, wikitag_bad = wikiutil.resolve_wiki(self.request, url)
        if wikitag_bad: # likely we got some /InterWiki as wikitail, we don't want that!
            pagename = wikiutil.url_unquote(pagename)
            pagename = self._replace_target(pagename)
            wikitail = pagename
        else: # good
            wikitail = wikiutil.url_unquote(wikitail)

        # link to self?
        if wikiutil.isPicture(wikitail):
            return '{{%s:%s%s}}' % (wikitag, wikitail, text)
        else:
            if ' ' not in wikitail and not text:
                return '%s:%s' % (wikitag, wikitail)
            else:
                return '[[%s:%s%s]]' % (wikitag, wikitail, text)

    def attachment(self, url_and_text):
        """ This gets called on attachment URLs. """
        if len(url_and_text) == 1:
            url = url_and_text[0]
            text = ''
        else:
            url, text = url_and_text
            text = '|' + text

        scheme, fname = url.split(":", 1)
        #scheme, fname, text = wikiutil.split_wiki(target_and_text)

        pagename, fname = AttachFile.absoluteName(fname, self.pagename)
        from_this_page = pagename == self.pagename
        fname = self._replace(('FILE', pagename, fname))
        fname = wikiutil.url_unquote(fname, want_unicode=True)
        fname = self._replace(('FILE', pagename, fname))
        pagename = self._replace(('PAGE', pagename))
        if from_this_page:
            name = fname
        else:
            name = "%s/%s" % (pagename, fname)

        if scheme == 'drawing':
            return "{{drawing:%s%s}}" % (name, text)

        # check for image URL, and possibly return IMG tag
        # (images are always inlined, just like for other URLs)
        if wikiutil.isPicture(name):
            return "{{attachment:%s%s}}" % (name, text)

        # inline the attachment
        if scheme == 'inline':
            return '{{attachment:%s%s}}' % (name, text)
        else: # 'attachment'
            return '[[attachment:%s%s]]' % (name, text)

    def _url_repl(self, word):
        """Handle literal URLs including inline images."""
        scheme = word.split(":", 1)[0]

        if scheme == 'wiki':
            return self.interwiki([word])
        if scheme in self.attachment_schemas:
            return '%s' % self.attachment([word])

        if wikiutil.isPicture(word): # magic will go away in 1.6!
            return '{{%s}}' % word # new markup for inline images
        else:
            return word

    def _url_bracket_repl(self, word):
        """Handle bracketed URLs."""
        word = word[1:-1] # strip brackets

        # Local extended link?
        if word[0] == ':':
            words = word[1:].split(':', 1)
            link, text = (words + ['', ''])[:2]
            if link.strip() == text.strip():
                text = ''
            link = self._replace_target(link)
            if text:
                text = '|' + text
            return '[[%s%s]]' % (link, text)

        # Traditional split on space
        words = word.split(None, 1)
        if words[0][0] == '#':
            # anchor link
            link, text = (words + ['', ''])[:2]
            if link.strip() == text.strip():
                text = ''
            #link = self._replace_target(link)
            if text:
                text = '|' + text
            return '[[%s%s]]' % (link, text)

        scheme = words[0].split(":", 1)[0]
        if scheme == "wiki":
            return self.interwiki(words)
            #scheme, wikiname, pagename, text = self.interwiki(word)
            #print "%r %r %r %r" % (scheme, wikiname, pagename, text)
            #if wikiname in ('Self', self.request.cfg.interwikiname, ''):
            #    if text:
            #        text = '|' + text
            #    return '[[%s%s]]' % (pagename, text)
            #else:
            #    if text:
            #        text = '|' + text
            #    return "[[%s:%s%s]]" % (wikiname, pagename, text)
        if scheme in self.attachment_schemas:
            m = self.attachment(words)
            if m.startswith('{{') and m.endswith('}}'):
                # with url_bracket markup, 1.5.8 parser does not embed, but link!
                m = '[[%s]]' % m[2:-2]
            return m

        target, desc = (words + ['', ''])[:2]
        if wikiutil.isPicture(desc) and re.match(self.url_rule, desc):
            #return '[[%s|{{%s|%s}}]]' % (words[0], words[1], words[0])
            return '[[%s|{{%s}}]]' % (target, desc)
        else:
            if desc:
                desc = '|' + desc
            return '[[%s%s]]' % (target, desc)

    def _pre_repl(self, word):
        w = word.strip()
        if w == '{{{' and not self.in_pre:
            self.in_pre = True
        elif w == '}}}' and self.in_pre:
            self.in_pre = False
        return word

    def _processor_repl(self, word):
        self.in_pre = True
        return word

    def scan(self, scan_re, line):
        """ Scans one line - append text before match, invoke replace() with match, and add text after match.  """
        result = []
        lastpos = 0

        for match in scan_re.finditer(line):
            # Add text before the match
            if lastpos < match.start():
                result.append(line[lastpos:match.start()])
            # Replace match with markup
            result.append(self.replace(match))
            lastpos = match.end()

        # Add remainder of the line
        result.append(line[lastpos:])
        return u''.join(result)


    def replace(self, match):
        """ Replace match using type name """
        result = []
        for _type, hit in match.groupdict().items():
            if hit is not None and not _type in ["hmarker", ]:
                # Get replace method and replace hit
                replace = getattr(self, '_' + _type + '_repl')
                # print _type, hit
                result.append(replace(hit))
                return ''.join(result)
        else:
            # We should never get here
            import pprint
            raise Exception("Can't handle match %r\n%s\n%s" % (
                match,
                pprint.pformat(match.groupdict()),
                pprint.pformat(match.groups()),
            ))

        return ""

    def convert(self, request):
        """ For each line, scan through looking for magic
            strings, outputting verbatim any intervening text.
        """
        self.request = request
        # prepare regex patterns
        rules = self.formatting_rules.replace('\n', '|')
        if self.request.cfg.bang_meta:
            rules = ur'(?P<notword>!%(word_rule)s)|%(rules)s' % {
                'word_rule': self.word_rule,
                'rules': rules,
            }
        pre_rules = r'''(?P<pre>\}\}\})'''
        pre_scan_re = re.compile(pre_rules, re.UNICODE)
        scan_re = re.compile(rules, re.UNICODE)
        eol_re = re.compile(r'\r?\n', re.UNICODE)

        rawtext = self.raw

        # remove last item because it's guaranteed to be empty
        self.lines = eol_re.split(rawtext)[:-1]
        self.in_processing_instructions = True

        # Main loop
        for line in self.lines:
            # ignore processing instructions
            if self.in_processing_instructions:
                found = False
                for pi in ("##", "#format", "#refresh", "#redirect", "#deprecated",
                           "#pragma", "#form", "#acl", "#language"):
                    if line.lower().startswith(pi):
                        self.request.write(line + '\r\n')
                        found = True
                        break
                if not found:
                    self.in_processing_instructions = False
                else:
                    continue # do not parse this line
            if not line.strip():
                self.request.write(line + '\r\n')
            else:
                # Scan line, format and write
                scanning_re = self.in_pre and pre_scan_re or scan_re
                formatted_line = self.scan(scanning_re, line)
                self.request.write(formatted_line + '\r\n')

