# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Creole wiki markup parser

    See http://wikicreole.org/ for latest specs.

    Notes:
    * No markup allowed in headings.
      Creole 1.0 does not require us to support this.
    * No markup allowed in table headings.
      Creole 1.0 does not require us to support this.
    * No (non-bracketed) generic url recognition: this is "mission impossible"
      except if you want to risk lots of false positives. Only known protocols
      are recognized.
    * We do not allow ":" before "//" italic markup to avoid urls with
      unrecognized schemes (like wtf://server/path) triggering italic rendering
      for the rest of the paragraph.

    @copyright: 2007 MoinMoin:RadomirDopieralski (creole 0.5 implementation),
                2007 MoinMoin:ThomasWaldmann (updates)
    @license: GNU GPL, see COPYING for details.
"""

import re
import StringIO
from MoinMoin import config, macro, wikiutil
from MoinMoin.support.python_compatibility import rsplit # Needed for python 2.3

Dependencies = []

# Whether the parser should convert \n into <br>.
bloglike_lines = False

class Parser:
    """
    Glue the DocParser and DocEmitter with the
    MoinMoin current API.
    """

    # Enable caching
    caching = 1
    Dependencies = Dependencies

    def __init__(self, raw, request, **kw):
        """Create a minimal Parser object with required attributes."""

        self.request = request
        self.form = request.form
        self.raw = raw

    def format(self, formatter):
        """Create and call the true parser and emitter."""

        document = DocParser(self.raw, self.request).parse()
        result = DocEmitter(document, formatter, self.request).emit()
        self.request.write(result)

class Rules:
    """Hold all the rules for generating regular expressions."""

    # For the inline elements:
    proto = r'http|https|ftp|nntp|news|mailto|telnet|file|irc'
    url =  r'''(?P<url>
            (^ | (?<=\s | [.,:;!?()/=]))
            (?P<escaped_url>~)?
            (?P<url_target> (?P<url_proto> %s ):\S+? )
            ($ | (?=\s | [,.:;!?()] (\s | $)))
        )''' % proto
    link = r'''(?P<link>
            \[\[
            (?P<link_target>.+?) \s*
            ([|] \s* (?P<link_text>.+?) \s*)?
            ]]
        )'''
    image = r'''(?P<image>
            {{
            (?P<image_target>.+?) \s*
            ([|] \s* (?P<image_text>.+?) \s*)?
            }}
        )'''
    macro = r'''(?P<macro>
            <<
            (?P<macro_name> \w+)
            (\( (?P<macro_args> .*?) \))? \s*
            ([|] \s* (?P<macro_text> .+?) \s* )?
            >>
        )'''
    code = r'(?P<code> {{{ (?P<code_text>.*?) }}} )'
    emph = r'(?P<emph> (?<!:)// )' # there must be no : in front of the //
                                   # avoids italic rendering in urls with
                                   # unknown protocols
    strong = r'(?P<strong> \*\* )'
    linebreak = r'(?P<break> \\\\ )'
    escape = r'(?P<escape> ~ (?P<escaped_char>\S) )'
    char =  r'(?P<char> . )'

    # For the block elements:
    separator = r'(?P<separator> ^ \s* ---- \s* $ )' # horizontal line
    line = r'(?P<line> ^ \s* $ )' # empty line that separates paragraphs
    head = r'''(?P<head>
            ^ \s*
            (?P<head_head>=+) \s*
            (?P<head_text> .*? ) \s*
            (?P<head_tail>=*) \s*
            $
        )'''
    if bloglike_lines:
        text = r'(?P<text> .+ ) (?P<break> (?<!\\)$\n(?!\s*$) )?'
    else:
        text = r'(?P<text> .+ )'
    list = r'''(?P<list>
            ^ [ \t]* ([*][^*\#]|[\#][^\#*]).* $
            ( \n[ \t]* [*\#]+.* $ )*
        )''' # Matches the whole list, separate items are parsed later. The
             # list *must* start with a single bullet.
    item = r'''(?P<item>
            ^ \s*
            (?P<item_head> [\#*]+) \s*
            (?P<item_text> .*?)
            $
        )''' # Matches single list items
    pre = r'''(?P<pre>
            ^{{{ \s* $
            (\n)?
            (?P<pre_text>
                ([\#]!(?P<pre_kind>\w*?)(\s+.*)?$)?
                (.|\n)+?
            )
            (\n)?
            ^}}} \s*$
        )'''
    pre_escape = r' ^(?P<indent>\s*) ~ (?P<rest> \}\}\} \s*) $'
    table = r'''(?P<table>
            ^ \s*
            [|].*? \s*
            [|]? \s*
            $
        )'''

    # For splitting table cells:
    cell = r'''
            \| \s*
            (
                (?P<head> [=][^|]+ ) |
                (?P<cell> (  %s | [^|])+ )
            ) \s*
        ''' % '|'.join([link, macro, image, code])
    # For the link targets:
    extern = r'(?P<extern_addr>(?P<extern_proto>%s):.*)' % proto
    attach = r'''
            (?P<attach_scheme> attachment | drawing | image ):
            (?P<attach_addr> .* )
        '''
    interwiki = r'''
            (?P<inter_wiki> [A-Z][a-zA-Z]+ ) :
            (?P<inter_page> .* )
        '''
    page = r'(?P<page_name> .* )'


class DocParser:
    """
    Parse the raw text and create a document object
    that can be converted into output using Emitter.
    """

    # For pre escaping, in creole 1.0 done with ~:
    pre_escape_re = re.compile(Rules.pre_escape, re.M | re.X)
    link_re = re.compile('|'.join([Rules.image, Rules.linebreak, Rules.char]), re.X | re.U) # for link descriptions
    item_re = re.compile(Rules.item, re.X | re.U | re.M) # for list items
    cell_re = re.compile(Rules.cell, re.X | re.U) # for table cells
    # For block elements:
    block_re = re.compile('|'.join([Rules.line, Rules.head, Rules.separator,
        Rules.pre, Rules.list, Rules.table, Rules.text]), re.X | re.U | re.M)
    # For inline elements:
    inline_re = re.compile('|'.join([Rules.link, Rules.url, Rules.macro,
        Rules.code, Rules.image, Rules.strong, Rules.emph, Rules.linebreak,
        Rules.escape, Rules.char]), re.X | re.U)

    def __init__(self, raw, request):
        self.request = request
        self.raw = raw
        self.root = DocNode('document', None)
        self.cur = self.root        # The most recent document node
        self.text = None            # The node to add inline characters to

    def _upto(self, node, kinds):
        """
        Look up the tree to the first occurence
        of one of the listed kinds of nodes or root.
        Start at the node node.
        """
        while node.parent is not None and not node.kind in kinds:
            node = node.parent
        return node

    # The _*_repl methods called for matches in regexps. Sometimes the
    # same method needs several names, because of group names in regexps.

    def _url_repl(self, groups):
        """Handle raw urls in text."""

        if not groups.get('escaped_url'):
            # this url is NOT escaped
            target = groups.get('url_target', '')
            node = DocNode('link', self.cur)
            node.content = target
            DocNode('text', node, node.content)
            self.text = None
        else:
            # this url is escaped, we render it as text
            if self.text is None:
                self.text = DocNode('text', self.cur, u'')
            self.text.content += groups.get('url_target')
    _url_target_repl = _url_repl
    _url_proto_repl = _url_repl
    _escaped_url = _url_repl

    def _link_repl(self, groups):
        """Handle all kinds of links."""

        target = groups.get('link_target', '')
        text = (groups.get('link_text', '') or '').strip()
        parent = self.cur
        self.cur = DocNode('link', self.cur)
        self.cur.content = target
        self.text = None
        re.sub(self.link_re, self._replace, text)
        self.cur = parent
        self.text = None
    _link_target_repl = _link_repl
    _link_text_repl = _link_repl

    def _macro_repl(self, groups):
        """Handles macros using the placeholder syntax."""

        name = groups.get('macro_name', '')
        text = (groups.get('macro_text', '') or '').strip()
        node = DocNode('macro', self.cur, name)
        node.args = groups.get('macro_args', '') or ''
        DocNode('text', node, text or name)
        self.text = None
    _macro_name_repl = _macro_repl
    _macro_args_repl = _macro_repl
    _macro_text_repl = _macro_repl

    def _image_repl(self, groups):
        """Handles images and attachemnts included in the page."""

        target = groups.get('image_target', '').strip()
        text = (groups.get('image_text', '') or '').strip()
        node = DocNode("image", self.cur, target)
        DocNode('text', node, text or node.content)
        self.text = None
    _image_target_repl = _image_repl
    _image_text_repl = _image_repl

    def _separator_repl(self, groups):
        self.cur = self._upto(self.cur, ('document', 'section', 'blockquote'))
        DocNode('separator', self.cur)

    def _item_repl(self, groups):
        bullet = groups.get('item_head', u'')
        text = groups.get('item_text', u'')
        if bullet[-1] == '#':
            kind = 'number_list'
        else:
            kind = 'bullet_list'
        level = len(bullet)
        lst = self.cur
        # Find a list of the same kind and level up the tree
        while (lst and
                   not (lst.kind in ('number_list', 'bullet_list') and
                        lst.level == level) and
                    not lst.kind in ('document', 'section', 'blockquote')):
            lst = lst.parent
        if lst and lst.kind == kind:
            self.cur = lst
        else:
            # Create a new level of list
            self.cur = self._upto(self.cur,
                ('list_item', 'document', 'section', 'blockquote'))
            self.cur = DocNode(kind, self.cur)
            self.cur.level = level
        self.cur = DocNode('list_item', self.cur)
        self.parse_inline(text)
        self.text = None
    _item_text_repl = _item_repl
    _item_head_repl = _item_repl

    def _list_repl(self, groups):
        text = groups.get('list', u'')
        self.item_re.sub(self._replace, text)

    def _head_repl(self, groups):
        self.cur = self._upto(self.cur, ('document', 'section', 'blockquote'))
        node = DocNode('header', self.cur, groups.get('head_text', '').strip())
        node.level = len(groups.get('head_head', ' '))
    _head_head_repl = _head_repl
    _head_text_repl = _head_repl

    def _text_repl(self, groups):
        if self.cur.kind in ('table', 'table_row', 'bullet_list',
            'number_list'):
            self.cur = self._upto(self.cur,
                ('document', 'section', 'blockquote'))
        if self.cur.kind in ('document', 'section', 'blockquote'):
            self.cur = DocNode('paragraph', self.cur)
        self.parse_inline(groups.get('text', '')+' ')
        if groups.get('break') and self.cur.kind in ('paragraph',
            'emphasis', 'strong', 'code'):
            DocNode('break', self.cur, '')
        self.text = None
    _break_repl = _text_repl

    def _table_repl(self, groups):
        row = groups.get('table', '|').strip()
        self.cur = self._upto(self.cur, (
            'table', 'document', 'section', 'blockquote'))
        if self.cur.kind != 'table':
            self.cur = DocNode('table', self.cur)
        tb = self.cur
        tr = DocNode('table_row', tb)

        text = ''
        for m in self.cell_re.finditer(row):
            cell = m.group('cell')
            if cell:
                self.cur = DocNode('table_cell', tr)
                self.text = None
                self.parse_inline(cell)
            else:
                cell = m.group('head')
                self.cur = DocNode('table_head', tr)
                self.text = DocNode('text', self.cur, u'')
                self.text.content = cell.strip('=')
        self.cur = tb
        self.text = None

    def _pre_repl(self, groups):
        self.cur = self._upto(self.cur, ('document', 'section', 'blockquote'))
        kind = groups.get('pre_kind', None)
        text = groups.get('pre_text', u'')
        def remove_tilde(m):
            return m.group('indent') + m.group('rest')
        text = self.pre_escape_re.sub(remove_tilde, text)
        node = DocNode('preformatted', self.cur, text)
        node.sect = kind or ''
        self.text = None
    _pre_text_repl = _pre_repl
    _pre_head_repl = _pre_repl
    _pre_kind_repl = _pre_repl

    def _line_repl(self, groups):
        self.cur = self._upto(self.cur, ('document', 'section', 'blockquote'))

    def _code_repl(self, groups):
        DocNode('code', self.cur, groups.get('code_text', u'').strip())
        self.text = None
    _code_text_repl = _code_repl
    _code_head_repl = _code_repl

    def _emph_repl(self, groups):
        if self.cur.kind != 'emphasis':
            self.cur = DocNode('emphasis', self.cur)
        else:
            self.cur = self._upto(self.cur, ('emphasis', )).parent
        self.text = None

    def _strong_repl(self, groups):
        if self.cur.kind != 'strong':
            self.cur = DocNode('strong', self.cur)
        else:
            self.cur = self._upto(self.cur, ('strong', )).parent
        self.text = None

    def _break_repl(self, groups):
        DocNode('break', self.cur, None)
        self.text = None

    def _escape_repl(self, groups):
        if self.text is None:
            self.text = DocNode('text', self.cur, u'')
        self.text.content += groups.get('escaped_char', u'')

    def _char_repl(self, groups):
        if self.text is None:
            self.text = DocNode('text', self.cur, u'')
        self.text.content += groups.get('char', u'')

    def _replace(self, match):
        """Invoke appropriate _*_repl method. Called for every matched group."""

        groups = match.groupdict()
        for name, text in groups.iteritems():
            if text is not None:
                replace = getattr(self, '_%s_repl' % name)
                replace(groups)
                return

    def parse_inline(self, raw):
        """Recognize inline elements inside blocks."""

        re.sub(self.inline_re, self._replace, raw)

    def parse_block(self, raw):
        """Recognize block elements."""

        re.sub(self.block_re, self._replace, raw)

    def parse(self):
        """Parse the text given as self.raw and return DOM tree."""

        self.parse_block(self.raw)
        return self.root

#################### Helper classes

### The document model and emitter follow

class DocNode:
    """
    A node in the document.
    """

    def __init__(self, kind='', parent=None, content=None):
        self.children = []
        self.parent = parent
        self.kind = kind
        self.content = content
        if self.parent is not None:
            self.parent.children.append(self)


class DocEmitter:
    """
    Generate the output for the document
    tree consisting of DocNodes.
    """

    addr_re = re.compile('|'.join([
            Rules.extern,
            Rules.attach,
            Rules.interwiki,
            Rules.page
        ]), re.X | re.U) # for addresses

    def __init__(self, root, formatter, request):
        self.root = root
        self.formatter = formatter
        self.request = request
        self.form = request.form
        self.macro = None

    def get_text(self, node):
        """Try to emit whatever text is in the node."""

        try:
            return node.children[0].content or ''
        except:
            return node.content or ''

    # *_emit methods for emitting nodes of the document:

    def document_emit(self, node):
        return self.emit_children(node)

    def text_emit(self, node):
        return self.formatter.text(node.content or '')

    def separator_emit(self, node):
        return self.formatter.rule()

    def paragraph_emit(self, node):
        return ''.join([
            self.formatter.paragraph(1),
            self.emit_children(node),
            self.formatter.paragraph(0),
        ])

    def bullet_list_emit(self, node):
        return ''.join([
            self.formatter.bullet_list(1),
            self.emit_children(node),
            self.formatter.bullet_list(0),
        ])

    def number_list_emit(self, node):
        return ''.join([
            self.formatter.number_list(1),
            self.emit_children(node),
            self.formatter.number_list(0),
        ])

    def list_item_emit(self, node):
        return ''.join([
            self.formatter.listitem(1),
            self.emit_children(node),
            self.formatter.listitem(0),
        ])

# Not used
#    def definition_list_emit(self, node):
#        return ''.join([
#            self.formatter.definition_list(1),
#            self.emit_children(node),
#            self.formatter.definition_list(0),
#        ])

# Not used
#    def term_emit(self, node):
#        return ''.join([
#            self.formatter.definition_term(1),
#            self.emit_children(node),
#            self.formatter.definition_term(0),
#        ])

# Not used
#    def definition_emit(self, node):
#        return ''.join([
#            self.formatter.definition_desc(1),
#            self.emit_children(node),
#            self.formatter.definition_desc(0),
#        ])

    def table_emit(self, node):
        return ''.join([
            self.formatter.table(1, attrs=getattr(node, 'attrs', '')),
            self.emit_children(node),
            self.formatter.table(0),
        ])

    def table_row_emit(self, node):
        return ''.join([
            self.formatter.table_row(1, attrs=getattr(node, 'attrs', '')),
            self.emit_children(node),
            self.formatter.table_row(0),
        ])

    def table_cell_emit(self, node):
        return ''.join([
            self.formatter.table_cell(1, attrs=getattr(node, 'attrs', '')),
            self.emit_children(node),
            self.formatter.table_cell(0),
        ])

    def table_head_emit(self, node):
        return ''.join([
            self.formatter.rawHTML('<th>'),
            self.emit_children(node),
            self.formatter.rawHTML('</th>'),
        ])

    def emphasis_emit(self, node):
        return ''.join([
            self.formatter.emphasis(1),
            self.emit_children(node),
            self.formatter.emphasis(0),
        ])

# Not used
#    def quote_emit(self, node):
#        return ''.join([
#            self.formatter.rawHTML('<q>'),
#            self.emit_children(node),
#            self.formatter.rawHTML('</q>'),
#        ])

    def strong_emit(self, node):
        return ''.join([
            self.formatter.strong(1),
            self.emit_children(node),
            self.formatter.strong(0),
        ])

# Not used
#    def smiley_emit(self, node):
#        return self.formatter.smiley(node.content)

    def header_emit(self, node):
        import sha
        pntt = '%s%s%d' % (self.formatter.page.page_name,
            self.get_text(node), node.level)
        ident = "head-%s" % sha.new(pntt.encode(config.charset)).hexdigest()
        return ''.join([
            self.formatter.heading(1, node.level, id=ident),
            self.formatter.text(node.content or ''),
            self.formatter.heading(0, node.level),
        ])

    def code_emit(self, node):
# XXX The current formatter will replace all spaces with &nbsp;, so we need
# to use rawHTML instead, until that is fixed.
#        return ''.join([
#            self.formatter.code(1),
#            self.formatter.text(node.content or ''),
#            self.formatter.code(0),
#        ])
        return ''.join([
            self.formatter.rawHTML('<tt>'),
            self.formatter.text(node.content or ''),
            self.formatter.rawHTML('</tt>'),
        ])

# Not used
#    def abbr_emit(self, node):
#        return ''.join([
#            self.formatter.rawHTML('<abbr title="%s">' % node.title),
#            self.formatter.text(node.content or ''),
#            self.formatter.rawHTML('</abbr>'),
#        ])

    def link_emit(self, node):
        target = node.content
        if node.children:
            inside = self.emit_children(node)
        else:
            inside = self.formatter.text(target)
        m = self.addr_re.match(target)
        if m:
            if m.group('page_name'):
                # link to a page
                word = m.group('page_name')
                if word.startswith(wikiutil.PARENT_PREFIX):
                    word = word[wikiutil.PARENT_PREFIX_LEN:]
                elif word.startswith(wikiutil.CHILD_PREFIX):
                    word = "%s/%s" % (self.formatter.page.page_name,
                        word[wikiutil.CHILD_PREFIX_LEN:])
                # handle anchors
                parts = rsplit(word, "#", 1)
                anchor = ""
                if len(parts) == 2:
                    word, anchor = parts
                return ''.join([
                    self.formatter.pagelink(1, word, anchor=anchor),
                    inside,
                    self.formatter.pagelink(0, word),
                ])
            elif m.group('extern_addr'):
                # external link
                address = m.group('extern_addr')
                proto = m.group('extern_proto')
                return ''.join([
                    self.formatter.url(1, address, css=proto),
                    inside,
                    self.formatter.url(0),
                ])
            elif m.group('inter_wiki'):
                # interwiki link
                wiki = m.group('inter_wiki')
                page = m.group('inter_page')
                if not node.children: # interwiki links don't show the moniker
                    inside = self.formatter.text(page)
                return ''.join([
                    self.formatter.interwikilink(1, wiki, page),
                    inside,
                    self.formatter.interwikilink(0),
                ])
            elif m.group('attach_scheme'):
                # link to an attachment
                scheme = m.group('attach_scheme')
                attachment = m.group('attach_addr')
                url = wikiutil.url_unquote(attachment, want_unicode=True)
                text = self.get_text(node)
                return ''.join([
                        self.formatter.attachment_link(1, url),
                        self.formatter.text(text),
                        self.formatter.attachment_link(0)
                    ])
        return "".join(["[[", self.formatter.text(target), "]]"])

# Not used
#    def anchor_link_emit(self, node):
#        return ''.join([
#            self.formatter.url(1, node.content, css='anchor'),
#            self.emit_children(node),
#            self.formatter.url(0),
#        ])

    def image_emit(self, node):
        target = node.content
        text = self.get_text(node)
        m = self.addr_re.match(target)
        if m:
            if m.group('page_name'):
                # inserted anchors
                url = wikiutil.url_unquote(target, want_unicode=True)
                if target.startswith('#'):
                    return self.formatter.rawHtml(u'<a name="%s"></a>' % url)
                # default to images
                return self.formatter.attachment_image(
                    url, alt=text, html_class='image')
            elif m.group('extern_addr'):
                # external link
                address = m.group('extern_addr')
                proto = m.group('extern_proto')
                url = wikiutil.url_unquote(address, want_unicode=True)
                return self.formatter.image(
                    src=url, alt=text, html_class='external_image')
            elif m.group('attach_scheme'):
                # link to an attachment
                scheme = m.group('attach_scheme')
                attachment = m.group('attach_addr')
                url = wikiutil.url_unquote(attachment, want_unicode=True)
                if scheme == 'image':
                    return self.formatter.attachment_image(
                        url, alt=text, html_class='image')
                elif scheme == 'drawing':
                    return self.formatter.attachment_drawing(url, text)
                else:
                    pass
            elif m.group('inter_wiki'):
                # interwiki link
                pass
#        return "".join(["{{", self.formatter.text(target), "}}"])
        url = wikiutil.url_unquote(node.content, want_unicode=True)
        return self.formatter.attachment_inlined(url, text)

# Not used
#    def drawing_emit(self, node):
#        url = wikiutil.url_unquote(node.content, want_unicode=True)
#        text = self.get_text(node)
#        return self.formatter.attachment_drawing(url, text)

# Not used
#    def figure_emit(self, node):
#        text = self.get_text(node)
#        url = wikiutil.url_unquote(node.content, want_unicode=True)
#        return ''.join([
#            self.formatter.rawHTML('<div class="figure">'),
#            self.get_image(url, text), self.emit_children(node),
#            self.formatter.rawHTML('</div>'),
#        ])

# Not used
#    def bad_link_emit(self, node):
#        return self.formatter.text(''.join([
#            '[[',
#            node.content or '',
#            ']]',
#        ]))

    def macro_emit(self, node):
        macro_name = node.content
        args = node.args
        if self.macro is None:
            self.macro = macro.Macro(self)
        try:
            return self.formatter.macro(self.macro, macro_name, args)
        except:
            return self.formatter.text(self.request.getText('macro error'))

# Not used
#    def section_emit(self, node):
#        return ''.join([
#            self.formatter.rawHTML(
#                '<div class="%s" style="%s">' % (node.sect, node.style)),
#            self.emit_children(node),
#            self.formatter.rawHTML('</div>'),
#        ])

    def break_emit(self, node):
        return self.formatter.linebreak(preformatted=0)

# Not used
#    def blockquote_emit(self, node):
#        return ''.join([
#            self.formatter.rawHTML('<blockquote>'),
#            self.emit_children(node),
#            self.formatter.rawHTML('</blockquote>'),
#        ])

    def preformatted_emit(self, node):
        parser_name = getattr(node, 'sect', '')
        if parser_name:
            try:
                return self.request.redirectedOutput(
                    self.formatter.parser, parser_name, node.content.split('\n'))
            except wikiutil.PluginMissingError:
                pass
        return ''.join([
            self.formatter.preformatted(1),
            self.formatter.text(node.content),
            self.formatter.preformatted(0),
        ])

    def default_emit(self, node):
        """Fallback function for emitting unknown nodes."""

        return ''.join([
            self.formatter.preformatted(1),
            self.formatter.text('<%s>\n' % node.kind),
            self.emit_children(node),
            self.formatter.preformatted(0),
        ])

    def emit_children(self, node):
        """Emit all the children of a node."""

        return ''.join([self.emit_node(child) for child in node.children])

    def emit_node(self, node):
        """Emit a single node."""

        emit = getattr(self, '%s_emit' % node.kind, self.default_emit)
        return emit(node)

    def emit(self):
        """Emit the document represented by self.root DOM tree."""

        # Try to disable 'smart' formatting if possible
        magic_save = getattr(self.formatter, 'no_magic', False)
        self.formatter.no_magic = True
        output = '\n'.join([
            self.emit_node(self.root),
        ])
        # restore 'smart' formatting if it was set
        self.formatter.no_magic = magic_save
        return output

del Rules # We have the regexps compiled, rules not needed anymore
