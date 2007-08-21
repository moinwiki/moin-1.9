# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - MoinMoin Wiki Markup Parser

    @copyright: 2000-2002 Juergen Hermann <jh@web.de>,
                2006-2007 MoinMoin:ThomasWaldmann,
                2007 by MoinMoin:ReimarBauer
    @license: GNU GPL, see COPYING for details.
"""

ur'''

    def anchor_link_emit(self, node):
        return ''.join([
            self.formatter.url(1, node.content, css='anchor'),
            self.emit_children(node),
            self.formatter.url(0),
        ])

TODO: use this for links to anchors
    res.append(self.formatter.anchorlink(1, words[0][1:]))
    res.append(self.formatter.text(words[1]))
    res.append(self.formatter.anchorlink(0))

'''

import re
from MoinMoin import config, wikiutil, macro


Dependencies = ['user'] # {{{#!wiki comment ... }}} has different output depending on the user's profile settings

class Parser:
    """
        Object that turns Wiki markup into HTML.

        All formatting commands can be parsed one line at a time, though
        some state is carried over between lines.

        Methods named like _*_repl() are responsible to handle the named regex
        patterns defined in print_html().
    """

    # allow caching
    caching = 1
    Dependencies = Dependencies

    # some common strings
    CHILD_PREFIX = wikiutil.CHILD_PREFIX
    CHILD_PREFIX_LEN = wikiutil.CHILD_PREFIX_LEN
    PARENT_PREFIX = wikiutil.PARENT_PREFIX
    PARENT_PREFIX_LEN = wikiutil.PARENT_PREFIX_LEN

    punct_pattern = re.escape(u'''"\'}]|:,.)?!''')
    url_scheme = (u'http|https|ftp|nntp|news|mailto|telnet|wiki|file|irc' +
                 (config.url_schemas and (u'|' + u'|'.join(config.url_schemas)) or ''))

    # some common rules
    url_rule = ur'''
        (^|(?<!\w))  # require either beginning of line or some whitespace to the left
        (?P<url_target>  # capture whole url there
         (?P<url_scheme>%(url_scheme)s)  # some scheme
         \:
         \S+?  # anything non-whitespace
        )
        ($|(?=\s|[%(punct)s](\s|$)))  # require either end of line or some whitespace or some punctuation+blank/eol afterwards
    ''' % {
        'url_scheme': url_scheme,
        'punct': punct_pattern,
    }

    word_rule = ur'''
        (?:
         (?<![%(u)s%(l)s/])  # require anything not upper/lower/slash before
         |
         ^  # ... or beginning of line
        )
        (?P<word_bang>\!)?  # configurable: avoid getting CamelCase rendered as link
        (?P<word_name>
         (?:
          (?P<word_parent_prefix>%(parent)s)*  # there might be either ../ parent prefix(es)
          |
          ((?<!%(child)s)%(child)s)?  # or maybe a single / child prefix (but not if we already had it before)
         )
         (
          ((?<!%(child)s)%(child)s)?  # there might be / child prefix (but not if we already had it before)
          (?:[%(u)s][%(l)s]+){2,}  # at least 2 upper>lower transitions make CamelCase
         )+  # we can have MainPage/SubPage/SubSubPage ...
        )
        (?![%(u)s%(l)s/])  # require anything not upper/lower/slash following
    ''' % {
        'u': config.chars_upper,
        'l': config.chars_lower,
        'child': re.escape(CHILD_PREFIX),
        'parent': re.escape(PARENT_PREFIX),
    }

    # link targets:
    extern_rule = r'(?P<extern_addr>(?P<extern_scheme>%s)\:.*)' % url_scheme
    attach_rule = r'(?P<attach_scheme>attachment|drawing)\:(?P<attach_addr>.*)'
    inter_rule = r'(?P<inter_wiki>[A-Z][a-zA-Z]+):(?P<inter_page>.*)'
    page_rule = r'(?P<page_name>.*)'

    link_target_rules = r'|'.join([
        extern_rule,
        attach_rule,
        inter_rule,
        page_rule,
    ])
    link_target_re = re.compile(link_target_rules, re.VERBOSE|re.UNICODE)

    transclude_rule = r"""
        (?P<transclude>
            \{\{
            (?P<transclude_target>.+?)\s*  # usually image target (eat trailing space)
            (\|\s*(?P<transclude_args>.+?)\s*)?  # usually image alt text (optional, strip space)
            \}\}
        )
    """
    text_rule = r"""
        (?P<simple_text>
            .+  # some text (not empty)
        )
    """
    # link descriptions:
    link_desc_rules = r'|'.join([
            transclude_rule,
            text_rule,
            # _get_rule('break', inline_tab),
            # _get_rule('char', inline_tab),
    ])
    link_desc_re = re.compile(link_desc_rules, re.VERBOSE|re.UNICODE)

    # transclude descriptions:
    transclude_desc_rules = r'|'.join([
            text_rule,
            # _get_rule('break', inline_tab),
            # _get_rule('char', inline_tab),
    ])
    transclude_desc_re = re.compile(transclude_desc_rules, re.VERBOSE|re.UNICODE)

    # lists:
    ol_rule = ur"""
        ^\s+  # indentation
        (?:[0-9]+|[aAiI])\. # arabic, alpha, roman counting
        (?:\#\d+)?  # optional start number
        \s  # require one blank afterwards
    """
    ol_re = re.compile(ol_rule, re.VERBOSE|re.UNICODE)

    dl_rule = ur"""
        ^\s+  # indentation
        .*?::  # definition term::
        \s  # require on blank afterwards
    """
    dl_re = re.compile(dl_rule, re.VERBOSE|re.UNICODE)

    # this is used inside <pre> / parser sections (we just want to know when it's over):
    pre_scan_rule = ur"""
(?P<pre>
    \}\}\}  # in pre, we only look for the end of the pre
)
"""
    pre_scan_re = re.compile(pre_scan_rule, re.VERBOSE|re.UNICODE)

    # the big, fat, less ugly one ;)
    # please be very careful: blanks and # must be escaped with \ !
    scan_rules = ur"""
(?P<emph_ibb>
    '''''(?=[^']+''')  # italic on, bold on, ..., bold off
)|(?P<emph_ibi>
    '''''(?=[^']+'')  # italic on, bold on, ..., italic off
)|(?P<emph_ib_or_bi>
    '{5}(?=[^'])  # italic and bold or bold and italic
)|(?P<emph>
    '{2,3}  # italic or bold
)|(?P<u>
    __ # underline
)|(?P<small>
    (
     (?P<small_on>\~-\ ?)  # small on (we eat a trailing blank if it is there)
    |
     (?P<small_off>-\~)  # small off
    )
)|(?P<big>
    (
     (?P<big_on>\~\+\ ?)  # big on (eat trailing blank)
    |
     (?P<big_off>\+\~)  # big off
    )
)|(?P<strike>
    (
     (?P<strike_on>--\()  # strike-through on
    |
     (?P<strike_off>\)--)  # strike-through off
    )
)|(?P<remark>
    (
     (?P<remark_on>/\*\ ?)  # inline remark on (eat trailing blank)
    |
     (?P<remark_off>\ ?\*/)  # off
    )
)|(?P<sup>
    \^  # superscript on
    (?P<sup_text>.*?)  # capture the text
    \^  # off
)|(?P<sub>
    ,,  # subscript on
    (?P<sub_text>[^,]{1,40})  # capture 1..40 chars of text
    ,,  # off
)|(?P<tt>
    \{\{\{  # teletype on
    (?P<tt_text>.*?)  # capture the text
    \}\}\}  # off
)|(?P<tt_bt>
    `  # teletype (using a backtick) on
    (?P<tt_bt_text>.*?)  # capture the text
    `  # off
)|(?P<interwiki>
    (?P<interwiki_wiki>[A-Z][a-zA-Z]+)  # interwiki wiki name
    \:
    (?P<interwiki_page>
     [^\s'\"\:\<\|]
     (
      [^\s%(punct)s]
     |
      (
       [%(punct)s]
       [^\s%(punct)s]
      )
     )+
    )  # interwiki page name
)|(?P<word>  # must come AFTER interwiki rule!
    %(word_rule)s  # CamelCase wiki words
)|(?P<link>
    \[\[
    (?P<link_target>.+?)\s*  # link target (eat trailing space)
    (\|\s*(?P<link_args>.+?)?\s*)? # link description (usually text, optional, strip space)
    \]\]
)|
%(transclude_rule)s
|(?P<url>
    %(url_rule)s
)|(?P<email>
    [-\w._+]+  # name
    \@  # at
    [\w-]+(\.[\w-]+)+  # server/domain
)|(?P<smiley>
    (^|(?<=\s))  # we require either beginning of line or some space before a smiley
    (%(smiley)s)  # one of the smileys
    (?=\s)  # we require some space after the smiley
)|(?P<macro>
    <<
    (?P<macro_name>(%%(macronames)s))  # name of the macro (only existing ones will match)
    (?:\((?P<macro_args>.*?)\))?  # optionally macro arguments
    >>
)|(?P<heading>
    ^(?P<hmarker>=+)\s+  # some === at beginning of line, eat trailing blanks
    (?P<heading_text>.*)  # capture heading text
    \s+(?P=hmarker)\s$  # some === at end of line (matching amount as we have seen), eat blanks
)|(?P<parser>
    \{\{\{
    (
     \#!.*  # we have a parser name directly following
    |
     \s*$  # no parser name, eat whitespace
    )
)|(?P<pre>
    (
     \{\{\{\ ?  # pre on
    |
     \}\}\}  # off
    )
)|(?P<comment>
    ^\#\#.*$  # src code comment, rest of line
)|(?P<ol>
    %(ol_rule)s  # ordered list
)|(?P<dl>
    %(dl_rule)s  # definition list
)|(?P<li>
    ^\s+\*\s*  # unordered list
)|(?P<li_none>
    ^\s+\.\s*  # unordered list, no bullets
)|(?P<indent>
    ^\s+  # indented by some spaces
)|(?P<tableZ>
    \|\|\ $  # the right end of a table row
)|(?P<table>
    (?:\|\|)+(?:<[^>]*?>)?(?!\|?\s$) # a table
)|(?P<rule>
    -{4,}  # hor. rule, min. 4 -
)|(?P<entity>
    &(
      ([a-zA-Z]+)  # symbolic entity, like &uuml;
      |
      (\#(\d{1,5}|x[0-9a-fA-F]+))  # numeric entities, like &#42; or &#x42;
     );
)|(?P<sgml_entity>  # must come AFTER entity rule!
    [<>&]  # needs special treatment for html/xml
)"""  % {

        'url_scheme': url_scheme,
        'url_rule': url_rule,
        'punct': punct_pattern,
        'ol_rule': ol_rule,
        'dl_rule': dl_rule,
        'word_rule': word_rule,
        'transclude_rule': transclude_rule,
        'smiley': u'|'.join([re.escape(s) for s in config.smileys])}

    # Don't start p before these
    no_new_p_before = ("heading rule table tableZ tr td "
                       "ul ol dl dt dd li li_none indent "
                       "macro parser pre")
    no_new_p_before = no_new_p_before.split()
    no_new_p_before = dict(zip(no_new_p_before, [1] * len(no_new_p_before)))

    def __init__(self, raw, request, **kw):
        self.raw = raw
        self.request = request
        self.form = request.form # Macro object uses this
        self._ = request.getText
        self.cfg = request.cfg
        self.line_anchors = kw.get('line_anchors', True)
        self.start_line = kw.get('start_line', 0)
        self.macro = None

        # currently, there is only a single, optional argument to this parser and
        # (when given), it is used as class(es) for a div wrapping the formatter output
        # either use a single class like "comment" or multiple like "comment/red/dotted"
        self.wrapping_div_class = kw.get('format_args', '').strip().replace('/', ' ')

        self.is_em = 0 # must be int
        self.is_b = 0 # must be int
        self.is_u = False
        self.is_strike = False
        self.is_big = False
        self.is_small = False
        self.is_remark = False

        self.lineno = 0
        self.in_list = 0 # between <ul/ol/dl> and </ul/ol/dl>
        self.in_li = 0 # between <li> and </li>
        self.in_dd = 0 # between <dd> and </dd>

        # states of the parser concerning being inside/outside of some "pre" section:
        # None == we are not in any kind of pre section (was: 0)
        # 'search_parser' == we didn't get a parser yet, still searching for it (was: 1)
        # 'found_parser' == we found a valid parser (was: 2)
        # 'no_parser' == we have no (valid) parser, use a normal <pre>...</pre> (was: 3)
        self.in_pre = None
        # needed for nested {{{
        self.in_nested_pre = 0

        self.no_862 = False
        self.in_table = 0
        self.inhibit_p = 0 # if set, do not auto-create a <p>aragraph

        # holds the nesting level (in chars) of open lists
        self.list_indents = []
        self.list_types = []

        # XXX TODO if we remove the runtime dependency, we can compile the scan_rules at module load time:
        self.scan_rules = self.scan_rules % {'macronames': u'|'.join(macro.getNames(self.cfg))}

    def _close_item(self, result):
        #result.append("<!-- close item begin -->\n")
        if self.in_table:
            result.append(self.formatter.table(0))
            self.in_table = 0
        if self.in_li:
            self.in_li = 0
            if self.formatter.in_p:
                result.append(self.formatter.paragraph(0))
            result.append(self.formatter.listitem(0))
        if self.in_dd:
            self.in_dd = 0
            if self.formatter.in_p:
                result.append(self.formatter.paragraph(0))
            result.append(self.formatter.definition_desc(0))
        #result.append("<!-- close item end -->\n")

    def _u_repl(self, word, groups):
        """Handle underline."""
        self.is_u = not self.is_u
        return self.formatter.underline(self.is_u)

    def _remark_repl(self, word, groups):
        """Handle remarks."""
        on = groups.get('remark_on')
        if on and self.is_remark:
            return self.formatter.text(word)
        off = groups.get('remark_off')
        if off and not self.is_remark:
            return self.formatter.text(word)
        self.is_remark = not self.is_remark
        return self.formatter.span(self.is_remark, css_class='comment')
    _remark_on_repl = _remark_repl
    _remark_off_repl = _remark_repl

    def _strike_repl(self, word, groups):
        """Handle strikethrough."""
        on = groups.get('strike_on')
        if on and self.is_strike:
            return self.formatter.text(word)
        off = groups.get('strike_off')
        if off and not self.is_strike:
            return self.formatter.text(word)
        self.is_strike = not self.is_strike
        return self.formatter.strike(self.is_strike)
    _strike_on_repl = _strike_repl
    _strike_off_repl = _strike_repl

    def _small_repl(self, word, groups):
        """Handle small."""
        on = groups.get('small_on')
        if on and self.is_small:
            return self.formatter.text(word)
        off = groups.get('small_off')
        if off and not self.is_small:
            return self.formatter.text(word)
        self.is_small = not self.is_small
        return self.formatter.small(self.is_small)
    _small_on_repl = _small_repl
    _small_off_repl = _small_repl

    def _big_repl(self, word, groups):
        """Handle big."""
        on = groups.get('big_on')
        if on and self.is_big:
            return self.formatter.text(word)
        off = groups.get('big_off')
        if off and not self.is_big:
            return self.formatter.text(word)
        self.is_big = not self.is_big
        return self.formatter.big(self.is_big)
    _big_on_repl = _big_repl
    _big_off_repl = _big_repl

    def _emph_repl(self, word, groups):
        """Handle emphasis, i.e. '' and '''."""
        if len(word) == 3:
            self.is_b = not self.is_b
            if self.is_em and self.is_b:
                self.is_b = 2
            return self.formatter.strong(self.is_b)
        else:
            self.is_em = not self.is_em
            if self.is_em and self.is_b:
                self.is_em = 2
            return self.formatter.emphasis(self.is_em)

    def _emph_ibb_repl(self, word, groups):
        """Handle mixed emphasis, i.e. ''''' followed by '''."""
        self.is_b = not self.is_b
        self.is_em = not self.is_em
        if self.is_em and self.is_b:
            self.is_b = 2
        return self.formatter.emphasis(self.is_em) + self.formatter.strong(self.is_b)

    def _emph_ibi_repl(self, word, groups):
        """Handle mixed emphasis, i.e. ''''' followed by ''."""
        self.is_b = not self.is_b
        self.is_em = not self.is_em
        if self.is_em and self.is_b:
            self.is_em = 2
        return self.formatter.strong(self.is_b) + self.formatter.emphasis(self.is_em)

    def _emph_ib_or_bi_repl(self, word, groups):
        """Handle mixed emphasis, exactly five '''''."""
        b_before_em = self.is_b > self.is_em > 0
        self.is_b = not self.is_b
        self.is_em = not self.is_em
        if b_before_em:
            return self.formatter.strong(self.is_b) + self.formatter.emphasis(self.is_em)
        else:
            return self.formatter.emphasis(self.is_em) + self.formatter.strong(self.is_b)

    def _sup_repl(self, word, groups):
        """Handle superscript."""
        text = groups.get('sup_text', '')
        return (self.formatter.sup(1) +
                self.formatter.text(text) +
                self.formatter.sup(0))
    _sup_text_repl = _sup_repl

    def _sub_repl(self, word, groups):
        """Handle subscript."""
        text = groups.get('sub_text', '')
        return (self.formatter.sub(1) +
               self.formatter.text(text) +
               self.formatter.sub(0))
    _sub_text_repl = _sub_repl

    def _tt_repl(self, word, groups):
        """Handle inline code."""
        tt_text = groups.get('tt_text', '')
        return (self.formatter.code(1) +
                self.formatter.text(tt_text) +
                self.formatter.code(0))
    _tt_text_repl = _tt_repl

    def _tt_bt_repl(self, word, groups):
        """Handle backticked inline code."""
        tt_bt_text = groups.get('tt_bt_text', '')
        return (self.formatter.code(1, css="backtick") +
                self.formatter.text(tt_bt_text) +
                self.formatter.code(0))
    _tt_bt_text_repl = _tt_bt_repl

    def _rule_repl(self, word, groups):
        """Handle sequences of dashes."""
        result = self._undent() + self._closeP()
        if len(word) <= 4:
            result += self.formatter.rule()
        else:
            # Create variable rule size 1 - 6. Actual size defined in css.
            size = min(len(word), 10) - 4
            result += self.formatter.rule(size)
        return result

    def _interwiki_repl(self, word, groups):
        """Handle InterWiki links."""
        wiki = groups.get('interwiki_wiki')
        page = groups.get('interwiki_page')

        wikitag_bad = wikiutil.resolve_interwiki(self.request, wiki, page)[3]
        if wikitag_bad:
            text = groups.get('interwiki')
            return self.formatter.text(text)
        else:
            return (self.formatter.interwikilink(1, wiki, page) +
                    self.formatter.text(page) +
                    self.formatter.interwikilink(0, wiki, page))
    _interwiki_wiki_repl = _interwiki_repl
    _interwiki_page_repl = _interwiki_repl

    def _word_repl(self, word, groups):
        """Handle WikiNames."""
        bang = groups.get('word_bang')
        if bang:
            # self.cfg.bang_meta:
            # handle !NotWikiNames
            return self.formatter.nowikiword(word)
        orig_word = word
        name = groups.get('word_name')
        parent_prefix = groups.get('word_parent_prefix')
        current_page = self.formatter.page.page_name
        name = wikiutil.AbsPageName(current_page, name)
        # if a simple, self-referencing link, emit it as plain text
        if name == current_page:
            return self.formatter.text(orig_word)
        else:
            # handle anchors
            parts = name.split("#", 1)
            anchor = ""
            if len(parts) == 2:
                name, anchor = parts
            return (self.formatter.pagelink(1, name, anchor=anchor) +
                    self.formatter.text(orig_word) +
                    self.formatter.pagelink(0, name))
    _word_bang_repl = _word_repl
    _word_parent_prefix_repl = _word_repl
    _word_name_repl = _word_repl

    def _url_repl(self, word, groups):
        """Handle literal URLs."""
        scheme = groups.get('url_scheme', 'http')
        target = groups.get('url_target', '')
        return (self.formatter.url(1, target, css=scheme) +
                self.formatter.text(target) +
                self.formatter.url(0))
    _url_target_repl = _url_repl
    _url_scheme_repl = _url_repl


    def _transclude_repl(self, word, groups):
        """Handles transcluding content, usually embedding images."""
        target = groups.get('transclude_target', '').strip()
        args = (groups.get('transclude_args', '') or '').strip()
        target = wikiutil.url_unquote(target, want_unicode=True)
        m = self.link_target_re.match(target)
        ma = self.transclude_desc_re.match(args)
        desc = None
        if ma:
            if ma.group('simple_text'):
                desc = ma.group('simple_text')
                desc = wikiutil.escape(desc)
        if m:
            if m.group('extern_addr'):
                scheme = m.group('extern_scheme')
                target = m.group('extern_addr')
                if not desc:
                    desc = wikiutil.escape(target)
                if scheme.startswith('http'): # can also be https
                    # currently only supports ext. image inclusion
                    return self.formatter.image(src=target, alt=desc, title=desc, css_class='external_image')

            elif m.group('attach_scheme'):
                scheme = m.group('attach_scheme')
                url = wikiutil.url_unquote(m.group('attach_addr'), want_unicode=True)
                if not desc:
                    desc = wikiutil.escape(url)
                if scheme == 'attachment':
                    mt = wikiutil.MimeType(filename=url)
                    if mt.major == 'text':
                        return self.formatter.attachment_inlined(url, desc)
                    elif mt.major == 'image':
                        return self.formatter.attachment_image(url, alt=desc, title=desc, css_class='image')
                    else:
                        # use EmbedObject for other mimetypes
                        from MoinMoin.macro.EmbedObject import EmbedObject
                        from MoinMoin.action import AttachFile
                        if mt is not None:
                            # reuse class tmp from Despam to define macro
                            from MoinMoin.action.Despam import tmp
                            macro = tmp()
                            macro.request = self.request
                            macro.formatter = self.request.html_formatter
                            pagename = self.formatter.page.page_name
                            href = AttachFile.getAttachUrl(pagename, url, self.request, escaped=1)
                            return self.formatter.rawHTML(EmbedObject.embed(EmbedObject(macro, wikiutil.escape(url)), mt, href))
                elif scheme == 'drawing':
                    return self.formatter.attachment_drawing(url, desc)

            elif m.group('page_name'): # TODO
                page_name = m.group('page_name')
                return u"Error: <<Include(%s,%s)>> emulation missing..." % (page_name, args)

            elif m.group('inter_wiki'): # TODO
                wiki_name = m.group('inter_wiki')
                page_name = m.group('inter_page')
                return u"Error: <<RemoteInclude(%s:%s,%s)>> still missing." % (wiki_name, page_name, args)

            else:
                if not desc:
                    desc = target
                return self.formatter.text('[[%s|%s]]' % (target, desc))
        return word +'???'
    _transclude_target_repl = _transclude_repl
    _transclude_args_repl = _transclude_repl

    def _link_description(self, desc, target='', default_text=''):
        """ parse a string <desc> valid as link description (text, transclusion, ...)
            and return formatted content.

            @param desc: the link description to parse
            @param default_text: use this text (formatted as text) if parsing
                                 desc returns nothing.
            @param target: target of the link (as readable markup) - used for
                           transcluded image's description
        """
        m = self.link_desc_re.match(desc)
        if m:
            if m.group('simple_text'):
                desc = m.group('simple_text')
                desc = wikiutil.escape(desc)
                desc = self.formatter.text(desc)
            elif m.group('transclude'):
                groupdict = m.groupdict()
                if groupdict.get('transclude_args') is None:
                    # if transcluded obj (image) has no description, use target for it
                    groupdict['transclude_args'] = target
                desc = m.group('transclude')
                desc = self._transclude_repl(desc, groupdict)
        else:
            desc = default_text
            if desc:
                desc = self.formatter.text(desc)
        return desc

    def _link_repl(self, word, groups):
        """Handle [[target|text]] links."""
        target = groups.get('link_target', '')
        desc = (groups.get('link_args', '') or '').strip()
        mt = self.link_target_re.match(target)
        if mt:
            if mt.group('page_name'):
                page_name = mt.group('page_name')
                # handle relative links
                if page_name.startswith(self.CHILD_PREFIX):
                    page_name = self.formatter.page.page_name + '/' + page_name[self.CHILD_PREFIX_LEN:] # XXX use func
                # handle anchors
                try:
                    page_name, anchor = page_name.split("#", 1)
                except ValueError:
                    anchor = ""
                if not page_name:
                    page_name = self.formatter.page.page_name
                return (self.formatter.pagelink(1, page_name, anchor=anchor) +
                        self._link_description(desc, target, page_name) +
                        self.formatter.pagelink(0, page_name))

            elif mt.group('extern_addr'):
                scheme = mt.group('extern_scheme')
                target = mt.group('extern_addr')
                return (self.formatter.url(1, target, css=scheme) +
                        self._link_description(desc, target, target) +
                        self.formatter.url(0))

            elif mt.group('inter_wiki'):
                wiki_name = mt.group('inter_wiki')
                page_name = mt.group('inter_page')
                wikitag_bad = wikiutil.resolve_interwiki(self.request, wiki_name, page_name)[3]
                return (self.formatter.interwikilink(1, wiki_name, page_name) +
                        self._link_description(desc, target, page_name) +
                        self.formatter.interwikilink(0, wiki_name, page_name))

            elif mt.group('attach_scheme'):
                scheme = mt.group('attach_scheme')
                url = wikiutil.url_unquote(mt.group('attach_addr'), want_unicode=True)
                if scheme == 'attachment':
                    return (self.formatter.attachment_link(1, url, title=desc) +
                            self._link_description(desc, target, url) +
                            self.formatter.attachment_link(0))
                elif scheme == 'drawing':
                    return self.formatter.attachment_drawing(url, desc, title=desc, alt=desc)
            else:
                if desc:
                    desc = '|' + desc
                return self.formatter.text('[[%s%s]]' % (target, desc))
    _link_target_repl = _link_repl
    _link_args_repl = _link_repl

    def _email_repl(self, word, groups):
        """Handle email addresses (without a leading mailto:)."""
        return (self.formatter.url(1, "mailto:%s" % word, css='mailto') +
                self.formatter.text(word) +
                self.formatter.url(0))

    def _sgml_entity_repl(self, word, groups):
        """Handle SGML entities."""
        return self.formatter.text(word)

    def _entity_repl(self, word, groups):
        """Handle numeric (decimal and hexadecimal) and symbolic SGML entities."""
        return self.formatter.rawHTML(word)

    def _indent_repl(self, match, groups):
        """Handle pure indentation (no - * 1. markup)."""
        result = []
        if not (self.in_li or self.in_dd):
            self._close_item(result)
            self.in_li = 1
            css_class = None
            if self.line_was_empty and not self.first_list_item:
                css_class = 'gap'
            result.append(self.formatter.listitem(1, css_class=css_class, style="list-style-type:none"))
        return ''.join(result)

    def _li_none_repl(self, match, groups):
        """Handle type=none (" .") lists."""
        result = []
        self._close_item(result)
        self.in_li = 1
        css_class = None
        if self.line_was_empty and not self.first_list_item:
            css_class = 'gap'
        result.append(self.formatter.listitem(1, css_class=css_class, style="list-style-type:none"))
        return ''.join(result)

    def _li_repl(self, match, groups):
        """Handle bullet (" *") lists."""
        result = []
        self._close_item(result)
        self.in_li = 1
        css_class = None
        if self.line_was_empty and not self.first_list_item:
            css_class = 'gap'
        result.append(self.formatter.listitem(1, css_class=css_class))
        return ''.join(result)

    def _ol_repl(self, match, groups):
        """Handle numbered lists."""
        return self._li_repl(match, groups)

    def _dl_repl(self, match, groups):
        """Handle definition lists."""
        result = []
        self._close_item(result)
        self.in_dd = 1
        result.extend([
            self.formatter.definition_term(1),
            self.formatter.text(match[1:-3].lstrip(' ')),
            self.formatter.definition_term(0),
            self.formatter.definition_desc(1),
        ])
        return ''.join(result)

    def _indent_level(self):
        """Return current char-wise indent level."""
        return len(self.list_indents) and self.list_indents[-1]

    def _indent_to(self, new_level, list_type, numtype, numstart):
        """Close and open lists."""
        openlist = []   # don't make one out of these two statements!
        closelist = []

        if self._indent_level() != new_level and self.in_table:
            closelist.append(self.formatter.table(0))
            self.in_table = 0

        while self._indent_level() > new_level:
            self._close_item(closelist)
            if self.list_types[-1] == 'ol':
                tag = self.formatter.number_list(0)
            elif self.list_types[-1] == 'dl':
                tag = self.formatter.definition_list(0)
            else:
                tag = self.formatter.bullet_list(0)
            closelist.append(tag)

            del self.list_indents[-1]
            del self.list_types[-1]

            if self.list_types: # we are still in a list
                if self.list_types[-1] == 'dl':
                    self.in_dd = 1
                else:
                    self.in_li = 1

        # Open new list, if necessary
        if self._indent_level() < new_level:
            self.list_indents.append(new_level)
            self.list_types.append(list_type)

            if self.formatter.in_p:
                closelist.append(self.formatter.paragraph(0))

            if list_type == 'ol':
                tag = self.formatter.number_list(1, numtype, numstart)
            elif list_type == 'dl':
                tag = self.formatter.definition_list(1)
            else:
                tag = self.formatter.bullet_list(1)
            openlist.append(tag)

            self.first_list_item = 1
            self.in_li = 0
            self.in_dd = 0

        # If list level changes, close an open table
        if self.in_table and (openlist or closelist):
            closelist[0:0] = [self.formatter.table(0)]
            self.in_table = 0

        self.in_list = self.list_types != []
        return ''.join(closelist) + ''.join(openlist)

    def _undent(self):
        """Close all open lists."""
        result = []
        #result.append("<!-- _undent start -->\n")
        self._close_item(result)
        for type in self.list_types[::-1]:
            if type == 'ol':
                result.append(self.formatter.number_list(0))
            elif type == 'dl':
                result.append(self.formatter.definition_list(0))
            else:
                result.append(self.formatter.bullet_list(0))
        #result.append("<!-- _undent end -->\n")
        self.list_indents = []
        self.list_types = []
        return ''.join(result)

    def _getTableAttrs(self, attrdef):
        # skip "|" and initial "<"
        while attrdef and attrdef[0] == "|":
            attrdef = attrdef[1:]
        if not attrdef or attrdef[0] != "<":
            return {}, ''
        attrdef = attrdef[1:]

        # extension for special table markup
        def table_extension(key, parser, attrs, wiki_parser=self):
            """ returns: tuple (found_flag, msg)
                found_flag: whether we found something and were able to process it here
                  true for special stuff like 100% or - or #AABBCC
                  false for style xxx="yyy" attributes
                msg: "" or an error msg
            """
            _ = wiki_parser._
            found = False
            msg = ''
            if key[0] in "0123456789":
                token = parser.get_token()
                if token != '%':
                    wanted = '%'
                    msg = _('Expected "%(wanted)s" after "%(key)s", got "%(token)s"') % {
                        'wanted': wanted, 'key': key, 'token': token}
                else:
                    try:
                        dummy = int(key)
                    except ValueError:
                        msg = _('Expected an integer "%(key)s" before "%(token)s"') % {
                            'key': key, 'token': token}
                    else:
                        found = True
                        attrs['width'] = '"%s%%"' % key
            elif key == '-':
                arg = parser.get_token()
                try:
                    dummy = int(arg)
                except ValueError:
                    msg = _('Expected an integer "%(arg)s" after "%(key)s"') % {
                        'arg': arg, 'key': key}
                else:
                    found = True
                    attrs['colspan'] = '"%s"' % arg
            elif key == '|':
                arg = parser.get_token()
                try:
                    dummy = int(arg)
                except ValueError:
                    msg = _('Expected an integer "%(arg)s" after "%(key)s"') % {
                        'arg': arg, 'key': key}
                else:
                    found = True
                    attrs['rowspan'] = '"%s"' % arg
            elif key == '(':
                found = True
                attrs['align'] = '"left"'
            elif key == ':':
                found = True
                attrs['align'] = '"center"'
            elif key == ')':
                found = True
                attrs['align'] = '"right"'
            elif key == '^':
                found = True
                attrs['valign'] = '"top"'
            elif key == 'v':
                found = True
                attrs['valign'] = '"bottom"'
            elif key == '#':
                arg = parser.get_token()
                try:
                    if len(arg) != 6: raise ValueError
                    dummy = int(arg, 16)
                except ValueError:
                    msg = _('Expected a color value "%(arg)s" after "%(key)s"') % {
                        'arg': arg, 'key': key}
                else:
                    found = True
                    attrs['bgcolor'] = '"#%s"' % arg
            return found, self.formatter.rawHTML(msg)

        # scan attributes
        attr, msg = wikiutil.parseAttributes(self.request, attrdef, '>', table_extension)
        if msg:
            msg = '<strong class="highlight">%s</strong>' % msg
        #self.request.log("parseAttributes returned %r" % attr)
        return attr, msg

    def _tableZ_repl(self, word, groups):
        """Handle table row end."""
        if self.in_table:
            result = ''
            # REMOVED: check for self.in_li, p should always close
            if self.formatter.in_p:
                result = self.formatter.paragraph(0)
            result += self.formatter.table_cell(0) + self.formatter.table_row(0)
            return result
        else:
            return self.formatter.text(word)

    def _table_repl(self, word, groups):
        """Handle table cell separator."""
        if self.in_table:
            result = []
            # check for attributes
            attrs, attrerr = self._getTableAttrs(word)

            # start the table row?
            if self.table_rowstart:
                self.table_rowstart = 0
                result.append(self.formatter.table_row(1, attrs))
            else:
                # Close table cell, first closing open p
                # REMOVED check for self.in_li, paragraph should close always!
                if self.formatter.in_p:
                    result.append(self.formatter.paragraph(0))
                result.append(self.formatter.table_cell(0))

            # check for adjacent cell markers
            if word.count("|") > 2:
                if 'align' not in attrs and \
                   not ('style' in attrs and 'text-align' in attrs['style'].lower()):
                    # add center alignment if we don't have some alignment already
                    attrs['align'] = '"center"'
                if 'colspan' not in attrs:
                    attrs['colspan'] = '"%d"' % (word.count("|")/2)

            # return the complete cell markup
            result.append(self.formatter.table_cell(1, attrs) + attrerr)
            result.append(self._line_anchordef())
            return ''.join(result)
        else:
            return self.formatter.text(word)

    def _heading_repl(self, word, groups):
        """Handle section headings."""
        heading_text = groups.get('heading_text', '').strip()
        depth = min(len(groups.get('hmarker')), 5)
        return ''.join([
            self._closeP(),
            self.formatter.heading(1, depth, id=heading_text),
            self.formatter.text(heading_text),
            self.formatter.heading(0, depth),
        ])
    _heading_text_repl = _heading_repl
    _hmarker_repl = _heading_repl

    def _parser_repl(self, word, groups):
        """Handle parsed code displays."""
        if word.startswith('{{{'):
            self.in_nested_pre = 1
            word = word[3:]

        self.parser = None
        self.parser_name = None
        s_word = word.strip()
        if s_word == '#!':
            # empty bang paths lead to a normal code display
            # can be used to escape real, non-empty bang paths
            word = ''
            self.in_pre = 'no_parser'
            return self._closeP() + self.formatter.preformatted(1)
        elif s_word.startswith('#!'):
            # First try to find a parser for this
            parser_name = s_word[2:].split()[0]
            self.setParser(parser_name)

        if self.parser:
            self.parser_name = parser_name
            self.in_pre = 'found_parser'
            self.parser_lines = [word]
            return ''
        elif s_word:
            self.in_pre = 'no_parser'
            return self._closeP() + self.formatter.preformatted(1) + \
                   self.formatter.text(s_word + ' (-)')
        else:
            self.in_pre = 'search_parser'
            return ''

    def _pre_repl(self, word, groups):
        """Handle code displays."""
        word = word.strip()
        if word == '{{{' and not self.in_pre:
            self.in_nested_pre = 1
            self.in_pre = 'no_parser'
            return self._closeP() + self.formatter.preformatted(1)
        elif word == '}}}' and self.in_pre and self.in_nested_pre == 1:
            self.in_pre = None
            self.inhibit_p = 0
            self.in_nested_pre = 0
            return self.formatter.preformatted(0)
        elif word == '}}}' and self.in_pre and self.in_nested_pre > 1:
            self.in_nested_pre -= 1
            if self.in_nested_pre < 0:
                self.in_nested_pre = 0
            return self.formatter.text(word)
        return self.formatter.text(word)

    def _smiley_repl(self, word, groups):
        """Handle smileys."""
        return self.formatter.smiley(word)

    def _comment_repl(self, word, groups):
        # if we are in a paragraph, we must close it so that normal text following
        # in the line below the comment will reopen a new paragraph.
        if self.formatter.in_p:
            self.formatter.paragraph(0)
        self.line_is_empty = 1 # markup following comment lines treats them as if they were empty
        return self.formatter.comment(word)

    def _closeP(self):
        if self.formatter.in_p:
            return self.formatter.paragraph(0)
        return ''

    def _macro_repl(self, word, groups):
        """Handle macros (<<macroname>>)."""
        macro_name = groups.get('macro_name')
        macro_args = groups.get('macro_args')
        self.inhibit_p = 0 # 1 fixes UserPreferences, 0 fixes paragraph formatting for macros

        # create macro instance
        if self.macro is None:
            self.macro = macro.Macro(self)
        return self.formatter.macro(self.macro, macro_name, macro_args)
    _macro_name_repl = _macro_repl
    _macro_args_repl = _macro_repl

    def scan(self, scan_re, line, inhibit_p=False):
        """ Scans one line
        Append text before match, invoke replace() with match, and add text after match.
        """
        result = []
        lastpos = 0

        ###result.append(u'<span class="info">[scan: <tt>"%s"</tt>]</span>' % line)
        for match in scan_re.finditer(line):
            # Add text before the match
            if lastpos < match.start():

                ###result.append(u'<span class="info">[add text before match: <tt>"%s"</tt>]</span>' % line[lastpos:match.start()])
                # self.no_862 is added to solve the issue of macros called inline
                if not (inhibit_p or self.inhibit_p or self.in_pre or self.formatter.in_p or self.no_862):
                    result.append(self.formatter.paragraph(1, css_class="line862"))
                result.append(self.formatter.text(line[lastpos:match.start()]))

            # Replace match with markup
            if not (inhibit_p or self.inhibit_p or self.in_pre or self.formatter.in_p or
                    self.in_table or self.in_list):
                result.append(self.formatter.paragraph(1, css_class="line867"))
            result.append(self.replace(match, inhibit_p))
            lastpos = match.end()

        ###result.append('<span class="info">[no match, add rest: <tt>"%s"<tt>]</span>' % line[lastpos:])

        # Add paragraph with the remainder of the line
        if not (inhibit_p or self.in_pre or self.in_li or self.in_dd or self.inhibit_p or
                self.formatter.in_p) and lastpos < len(line):
            result.append(self.formatter.paragraph(1, css_class="line874"))
        if '}}}' in line and len(line[lastpos:].strip()) > 0:
            result.append(wikiutil.renderText(self.request, Parser, line[lastpos:].strip()))
        else:
            result.append(self.formatter.text(line[lastpos:]))
        return u''.join(result)

    def _replace(self, match):
        """ Same as replace() but with no magic """
        for name, text in match.groupdict().iteritems():
            if text is not None:
                # Get replace method and replace text
                replace_func = getattr(self, '_%s_repl' % name)
                result = replace_func(text, match.groupdict())
                return result

    def replace(self, match, inhibit_p=False):
        """ Replace match using type name """
        result = []
        for type, hit in match.groupdict().items():
            if hit is not None and not type in ["hmarker", ]:

                ##result.append(u'<span class="info">[replace: %s: "%s"]</span>' % (type, hit))
                # Open p for certain types
                if not (inhibit_p or self.inhibit_p or self.formatter.in_p
                        or self.in_pre or (type in self.no_new_p_before)):
                    result.append(self.formatter.paragraph(1, css_class="line891"))

                # Get replace method and replace hit
                replace_func = getattr(self, '_%s_repl' % type)
                result.append(replace_func(hit, match.groupdict()))
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

    def _line_anchordef(self):
        if self.line_anchors and not self.line_anchor_printed:
            self.line_anchor_printed = 1
            return self.formatter.line_anchordef(self.lineno)
        else:
            return ''

    def format(self, formatter, inhibit_p=False):
        """ For each line, scan through looking for magic
            strings, outputting verbatim any intervening text.
        """
        self.formatter = formatter
        self.hilite_re = self.formatter.page.hilite_re

        # prepare regex patterns
        self.request.clock.start('compile_huge_and_pretty')
        scan_re = re.compile(self.scan_rules, re.UNICODE|re.VERBOSE)
        indent_re = re.compile(ur"^\s*", re.UNICODE)
        eol_re = re.compile(r'\r?\n', re.UNICODE)
        self.request.clock.stop('compile_huge_and_pretty')

        # get text and replace TABs
        rawtext = self.raw.expandtabs()

        # go through the lines
        self.lineno = self.start_line
        self.lines = eol_re.split(rawtext)
        self.line_is_empty = 0

        self.in_processing_instructions = 1

        if self.wrapping_div_class:
            self.request.write(self.formatter.div(1, css_class=self.wrapping_div_class))

        # Main loop
        for line in self.lines:
            if '>><<' in line.replace(' ', ''):
                self.no_862 = True

            self.line_anchor_printed = 0
            if not self.in_table:
                self.request.write(self._line_anchordef())
            self.table_rowstart = 1
            self.line_was_empty = self.line_is_empty
            self.line_is_empty = 0
            self.first_list_item = 0
            self.inhibit_p = 0

            # ignore processing instructions
            if self.in_processing_instructions:
                found = False
                for pi in ("##", "#format", "#refresh", "#redirect", "#deprecated",
                           "#pragma", "#form", "#acl", "#language"):
                    if line.lower().startswith(pi):
                        self.request.write(self.formatter.comment(line))
                        found = True
                        break
                if not found:
                    self.in_processing_instructions = 0
                else:
                    continue # do not parse this line
            if self.in_pre:
                # TODO: move this into function
                # still looking for processing instructions
                if self.in_pre == 'search_parser':
                    self.parser = None
                    parser_name = ''
                    if line.strip().startswith("#!"):
                        parser_name = line.strip()[2:].split()[0]
                        self.setParser(parser_name)

                    if self.parser:
                        self.in_pre = 'found_parser'
                        self.parser_lines = [line]
                        self.parser_name = parser_name
                        continue
                    else:
                        if not line.count('{{{') > 1:
                            self.request.write(self._closeP() +
                                self.formatter.preformatted(1))
                        self.in_pre = 'no_parser'

                if self.in_pre == 'found_parser':
                    self.in_nested_pre += line.count('{{{')
                    if self.in_nested_pre - line.count('}}}') == 0:
                        self.in_nested_pre = 1
                    # processing mode
                    try:
                        if line.endswith("}}}"):
                            if self.in_nested_pre == 1:
                                endpos = len(line) - 3
                            else:
                                self.parser_lines.append(line)
                                self.in_nested_pre -= 1
                                continue
                        else:
                            if self.in_nested_pre == 1:
                                endpos = line.index("}}}")
                            else:
                                self.parser_lines.append(line)
                                if "}}}" in line:
                                    self.in_nested_pre -= 1
                                continue

                    except ValueError:
                        self.parser_lines.append(line)
                        continue
                    if line[:endpos]:
                        self.parser_lines.append(line[:endpos])

                    # Close p before calling parser
                    # TODO: do we really need this?
                    self.request.write(self._closeP())
                    res = self.formatter.parser(self.parser_name, self.parser_lines)
                    self.request.write(res)
                    del self.parser_lines
                    self.in_pre = None
                    self.parser = None

                    # send rest of line through regex machinery
                    line = line[endpos+3:]
                    if not line.strip(): # just in the case "}}} " when we only have blanks left...
                        continue
            else:
                # we don't have \n as whitespace any more
                # This is the space between lines we join to one paragraph
                line += ' '

                # Paragraph break on empty lines
                if not line.strip():
                    if self.in_table:
                        self.request.write(self.formatter.table(0))
                        self.request.write(self._line_anchordef())
                        self.in_table = 0
                    # CHANGE: removed check for not self.list_types
                    # p should close on every empty line
                    if self.formatter.in_p:
                        self.request.write(self.formatter.paragraph(0))
                    self.line_is_empty = 1
                    continue

                # Check indent level
                indent = indent_re.match(line)
                indlen = len(indent.group(0))
                indtype = "ul"
                numtype = None
                numstart = None
                if indlen:
                    match = self.ol_re.match(line)
                    if match:
                        numtype, numstart = match.group(0).strip().split('.')
                        numtype = numtype[0]

                        if numstart and numstart[0] == "#":
                            numstart = int(numstart[1:])
                        else:
                            numstart = None

                        indtype = "ol"
                    else:
                        match = self.dl_re.match(line)
                        if match:
                            indtype = "dl"

                # output proper indentation tags
                self.request.write(self._indent_to(indlen, indtype, numtype, numstart))

                # Table mode
                # TODO: move into function?
                if (not self.in_table and line[indlen:indlen + 2] == "||"
                    and line.endswith("|| ") and len(line) >= 5 + indlen):
                    # Start table
                    if self.list_types and not self.in_li:
                        self.request.write(self.formatter.listitem(1, style="list-style-type:none"))
                        ## CHANGE: no automatic p on li
                        ##self.request.write(self.formatter.paragraph(1))
                        self.in_li = 1

                    # CHANGE: removed check for self.in_li
                    # paragraph should end before table, always!
                    if self.formatter.in_p:
                        self.request.write(self.formatter.paragraph(0))
                    attrs, attrerr = self._getTableAttrs(line[indlen+2:])
                    self.request.write(self.formatter.table(1, attrs) + attrerr)
                    self.in_table = True # self.lineno
                elif (self.in_table and not
                      # intra-table comments should not break a table
                      (line.startswith("##") or
                       line[indlen:indlen + 2] == "||" and
                       line.endswith("|| ") and
                       len(line) >= 5 + indlen)):

                    # Close table
                    self.request.write(self.formatter.table(0))
                    self.request.write(self._line_anchordef())
                    self.in_table = 0

            # Scan line, format and write
            scanning_re = self.in_pre and self.pre_scan_re or scan_re
            if '{{{' in line:
                self.in_nested_pre += 1
            formatted_line = self.scan(scanning_re, line, inhibit_p=inhibit_p)
            self.request.write(formatted_line)
            if self.in_pre == 'no_parser':
                self.request.write(self.formatter.linebreak())


        # Close code displays, paragraphs, tables and open lists
        self.request.write(self._undent())
        if self.in_pre: self.request.write(self.formatter.preformatted(0))
        if self.formatter.in_p: self.request.write(self.formatter.paragraph(0))
        if self.in_table: self.request.write(self.formatter.table(0))

        if self.wrapping_div_class:
            self.request.write(self.formatter.div(0))


    # Private helpers ------------------------------------------------------------

    def setParser(self, name):
        """ Set parser to parser named 'name' """
        # XXX this is done by the formatter as well
        try:
            self.parser = wikiutil.searchAndImportPlugin(self.request.cfg, "parser", name)
        except wikiutil.PluginMissingError:
            self.parser = None


