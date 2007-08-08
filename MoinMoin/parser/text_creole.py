# -*- coding: iso-8859-1 -*-

"""
Creole wiki markup parser plugin for MoinMoin 1.5

See http://wikicreole.org/ for latest specs.

Changes:
2007-08-08:
 * PEP8 cleanup

2007-03-23
 * Implemented table headings, as in Creole 0.5
 * No markup allowed in table headings

2007-02-10
 * Images inside link descriptions
 * Lists parsed and rendered properly

2007-02-05
 * Tables rendered properly
 * Links, images and nowiki in tables handled properly

2007-02-04
 * {{...}} can now be used both for attachments and images
 * No space required after bullets anymore
 * Implemented escaping with space in <pre>
 * Implemented greedy "}" parsing in nowiki
 * Added <h1> header available with =...=
 * Added <br> available with \\
 * Added tables (temporarily rendered as <pre>)
TODO: "smart" resolving of bold/list ambiguity, table rendering


2006-11-29
 * Fixed the bug causing newlines to be ignored inside //emphasis//
   and **strong**.

2006-09-11
 * Changed the bullet character for unordered lists to '*' according to spec.
 * Requiring a space or tab after the bullet in lists (to avoid collisions).
 * Moved the regula expression initialization to class initialization, for
   faster parser object creation.

"""

import re
import StringIO
from MoinMoin import config, macro, wikiutil

Dependencies = []


class Parser:
    """
    The class to glue the DocParser and DocEmitter with the
    MoinMoin current API.
    """
    # Enable caching
    caching = 1
    Dependencies = []

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


def _get_rule(rule, tab):
    return r'(?P<%s>%s)' % (rule, tab.get(rule, ''))


class DocParser:
    """
    Parse the raw text and create a document object
    that can be converted into output using Emitter.
    """

    # The parsing rules

    # whether the parser should convert \n into <br>
    bloglike_lines = False

    # For pre escaping:
    pre_escape_re = re.compile(r'^\s*\}\}\}\s*$', re.M)

    # For the inline elements:
    inline_tab = {
        'url': r'''(^|(?<=\s|[.,:;!?()/=]))(?P<url_target>(?P<url_proto>http|ftp|mailto|irc|https|ftps|news|gopher|file|telnet|nntp):\S+?)($|(?=\s|[,.:;!?()](\s|$)))''',
        'link': r'\[\[(?P<link_target>.+?)\s*(\|\s*(?P<link_text>.+?)\s*)?]]',
        'image': r'{{(?P<image_target>.+?)\s*(\|\s*(?P<image_text>.+?)\s*)?}}',
        'macro': r'<<(?P<macro_target>.+?)\s*(\|\s*(?P<macro_text>.+?)\s*)?>>',
        'code': r'{{{(?P<code_text>.*?)}}}',
        'emph': r'//',
        'strong': r'\*\*',
        'break': r'\\\\',
        'char': r'.',
    }

    # For the block elements:
    rule_rule = r'(?P<rule>^----+\s*$)'
    line_rule = r'(?P<line>^\s*$)'
    head_rule = r'(?P<head>^(?P<head_head>=+)\s*(?P<head_text>[^*].*?)\s*(?P<head_tail>=*)\s*$)'
    if bloglike_lines:
        text_rule = r'(?P<text>.+)(?P<break>(?<!\\)$\n(?!\s*$))?'
    else:
        text_rule = r'(?P<text>.+)'
    list_rule = r'(?P<list> ^[ \t]* ([*][^*]|[\#][^\#]) .*$  (\n[ \t]*[*\#]+.*$)*  )'
    pre_rule = r'(?P<pre>^{{{\s*$(\n)?(?P<pre_text>(^[\#]!(?P<pre_kind>.*?)(\s+.*)?$)?(.|\n)+?)(\n)?^}}}\s*$)'
    table_rule = r'(?P<table>^\s*\|.*?\s*\|?\s*$)'

    # For the link targets:
    extern_rule = r'(?P<extern_addr>(?P<extern_proto>http|https|ftp|nntp|news|mailto|telnet|file|irc):.*)'
    attach_rule = r'(?P<attach_scheme>attachment|inline|drawing|figure):(?P<attach_addr>.*)'
    inter_rule = r'(?P<inter_wiki>[A-Z][a-zA-Z]+):(?P<inter_page>.*)'
    #u'|'.join(wikimacro.getNames(config))
    macro_rule = r'(?P<macro_name>%s)\((-|(?P<macro_param>.*))\)' % '\w+'
    page_rule = r'(?P<page_name>.*)'

    # For splitting table cells:
    cell_rule = r'\|\s* ( (?P<head> [=][^|]+) | (?P<cell> ((%(link)s) |(%(macro)s) |(%(image)s) |(%(code)s) | [^|] )+)  )\s*' % inline_tab
    cell_re = re.compile(cell_rule, re.X|re.I|re.U)

    # For link descriptions:
    link_rules = r'|'.join([
            _get_rule('image', inline_tab),
            _get_rule('break', inline_tab),
            _get_rule('char', inline_tab),
    ])
    link_re = re.compile(link_rules, re.X|re.I|re.U)

    # For lists:
    item_rule = r'(?P<item> ^\s* (?P<item_head> [\#*]+ ) \s* (?P<item_text>.*?) $)'
    item_re = re.compile(item_rule, re.X|re.I|re.U|re.M)

    # For block elements:
    block_rules = '|'.join([
            line_rule,
            head_rule,
            rule_rule,
            pre_rule,
            list_rule,
            table_rule,
            text_rule,
    ])
    block_re = re.compile(block_rules, re.X|re.U|re.M)

    addr_rules = r'|'.join([
        macro_rule,
        extern_rule,
        attach_rule,
        inter_rule,
        page_rule,
    ])
    addr_re = re.compile(addr_rules, re.X|re.U)

    inline_rules = r'|'.join([
            _get_rule('link', inline_tab),
            _get_rule('url', inline_tab),
            _get_rule('macro', inline_tab),
            _get_rule('code', inline_tab),
            _get_rule('image', inline_tab),
            _get_rule('strong', inline_tab),
            _get_rule('emph', inline_tab),
            _get_rule('break', inline_tab),
            _get_rule('char', inline_tab),
    ])
    inline_re = re.compile(inline_rules, re.X|re.U)
    del inline_tab

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

    # The _*_repl methods called for matches in regexps:

    def _url_repl(self, groups):
        """Handle raw urls in text."""
        target = groups.get('url_target', '')
        node = DocNode('external_link', self.cur)
        node.content = target
        node.proto = groups.get('url_proto', 'http')
        DocNode('text', node, node.content)
        self.text = None
    _url_target_repl = _url_repl
    _url_proto_repl = _url_repl

    def _link_repl(self, groups):
        """Handle all other kinds of links."""
        target = groups.get('link_target', '')
        text = (groups.get('link_text', '') or '').strip()
        parent = self.cur
        m = self.addr_re.match(target)
        if m:
            if m.group('page_name'):
                node = DocNode('page_link', self.cur)
                node.content = m.group('page_name')
            elif m.group('extern_addr'):
                node = DocNode('external_link', self.cur)
                node.content = m.group('extern_addr')
                node.proto = m.group('extern_proto')
            elif m.group('inter_wiki'):
                node = DocNode('interwiki_link', self.cur)
                node.content = '%s:%s' % (m.group('inter_wiki'), m.group('inter_page'))
            elif m.group('attach_scheme'):
                scheme = m.group('attach_scheme')
                if scheme == 'inline':
                    scheme = 'inlined_attachment'
                node = DocNode(scheme, self.cur, m.group('attach_addr'))
            else:
                node = DocNode('bad_link', self.cur)
                node.content = target
            self.cur = node
            self.text = None
            re.sub(self.link_re, self._replace, text or node.content)
            self.cur = parent
        self.text = None
    _link_target_repl = _link_repl
    _link_text_repl = _link_repl

    def _macro_repl(self, groups):
        """Handles macros using the placeholder syntax."""
        target = groups.get('macro_target', '')
        text = (groups.get('macro_text', '') or '').strip()
        m = self.addr_re.match(target)
        if m and m.group('macro_name'):
            node = DocNode('macro', self.cur, m.group('macro_name'))
            node.args = m.group('macro_param')
        else:
            node = DocNode('bad_link', self.cur)
            node.content = target
            DocNode('text', node, text or target)
        self.text = None
    _macro_target_repl = _macro_repl
    _macro_text_repl = _macro_repl

    def _image_repl(self, groups):
        """Handles embedded images."""
        target = groups.get('image_target', '').strip()
        text = (groups.get('image_text', '') or '').strip()
        kind = 'attachment'
        if (target.endswith('.png') or
            target.endswith('.gif') or
            target.endswith('.jpg')):
                kind = 'image'
        node = DocNode(kind, self.cur, target)
        DocNode('text', node, text or node.content)
        self.text = None
    _image_target_repl = _image_repl
    _image_text_repl = _image_repl

    def _rule_repl(self, groups):
        self.cur = self._upto(self.cur, ('document', 'section', 'blockquote'))
        DocNode('rule', self.cur)

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
            self.cur = self._upto(self.cur, ('list_item', 'document', 'section', 'blockquote'))
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
        if self.cur.kind in ('table', 'table_row', 'bullet_list', 'number_list'):
            self.cur = self._upto(self.cur, ('document', 'section', 'blockquote'))
        if self.cur.kind in ('document', 'section', 'blockquote'):
            self.cur = DocNode('paragraph', self.cur)
        self.parse_inline(groups.get('text', '')+' ')
        if groups.get('break') and self.cur.kind in ('paragraph', 'emphasis', 'strong', 'code'):
            DocNode('break', self.cur, '')
        self.text = None
    _break_repl = _text_repl

    def _table_repl(self, groups):
        row = groups.get('table', '|').strip()
        self.cur = self._upto(self.cur, ('table', 'document', 'section', 'blockquote'))
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
        text = self.pre_escape_re.sub(lambda x: x.group(0)[1:], text)
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
        self.parse_block(self.raw)
        return self.root

#################### Helper classes

### The document model, and true parser and emitter follow

class DocNode:
    """A node in the Document."""

    def __init__(self, kind='', parent=None, content=None):
        self.children = []
        self.parent = parent
        self.kind = kind
        self.content = content
        if not self.parent is None:
            self.parent.children.append(self)


class DocEmitter:
    """
    Generate the output for the document tree consisting of DocNodes.
    """

    def __init__(self, root, formatter, request):
        self.root = root
        self.formatter = formatter
        self.request = request
        self.form = request.form
        self.macro = None

    def get_image(self, addr, text=''):
        """Return markup for image depending on the address."""
        if addr is None:
            addr = ''
        url = wikiutil.url_unquote(addr, want_unicode=True)
        if addr.startswith('http:'):
            return self.formatter.image(src=url, alt=text, html_class='external_image')
        else:
            return self.formatter.attachment_image(url, alt=text, html_class='image')

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

    def rule_emit(self, node):
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

    def definition_list_emit(self, node):
        return ''.join([
            self.formatter.definition_list(1),
            self.emit_children(node),
            self.formatter.definition_list(0),
        ])

    def term_emit(self, node):
        return ''.join([
            self.formatter.definition_term(1),
            self.emit_children(node),
            self.formatter.definition_term(0),
        ])

    def definition_emit(self, node):
        return ''.join([
            self.formatter.definition_desc(1),
            self.emit_children(node),
            self.formatter.definition_desc(0),
        ])

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

    def quote_emit(self, node):
        return ''.join([
            self.formatter.rawHTML('<q>'),
            self.emit_children(node),
            self.formatter.rawHTML('</q>'),
        ])

    def strong_emit(self, node):
        return ''.join([
            self.formatter.strong(1),
            self.emit_children(node),
            self.formatter.strong(0),
        ])

    def smiley_emit(self, node):
        return self.formatter.smiley(node.content)

    def header_emit(self, node):
        import sha
        pntt = self.formatter.page.page_name + self.get_text(node)+'%d' % node.level
        ident = "head-" + sha.new(pntt.encode(config.charset)).hexdigest()
        return ''.join([
            self.formatter.heading(1, node.level, id=ident),
            self.formatter.text(node.content or ''),
            self.formatter.heading(0, node.level),
        ])

    def code_emit(self, node):
        return ''.join([
            self.formatter.code(1),
            self.formatter.text(node.content or ''),
            self.formatter.code(0),
        ])

    def abbr_emit(self, node):
        return ''.join([
            self.formatter.rawHTML('<abbr title="%s">' % node.title),
            self.formatter.text(node.content or ''),
            self.formatter.rawHTML('</abbr>'),
        ])

    def page_link_emit(self, node):
        word = node.content
        # handle relative links
        if word.startswith(wikiutil.CHILD_PREFIX):
            word = self.formatter.page.page_name + '/' + word[wikiutil.CHILD_PREFIX_LEN:]
        # handle anchors
        parts = word.split("#", 1)
        anchor = ""
        if len(parts) == 2:
            word, anchor = parts
        return ''.join([
            self.formatter.pagelink(1, word, anchor=anchor),
            self.emit_children(node),
            self.formatter.pagelink(0, word),
        ])

    def external_link_emit(self, node):
        return ''.join([
            self.formatter.url(1, node.content, css='www %s' % node.proto),
            self.emit_children(node),
            self.formatter.url(0),
        ])

    def anchor_link_emit(self, node):
        return ''.join([
            self.formatter.url(1, node.content, css='anchor'),
            self.emit_children(node),
            self.formatter.url(0),
        ])

    def interwiki_link_emit(self, node):
        word = node.content
        wikitag, wikiurl, wikitail, wikitag_bad = \
            wikiutil.resolve_wiki(self.request, word)
        href = wikiutil.join_wiki(wikiurl, wikitail)
        return ''.join([
            self.formatter.interwikilink(1, wikitag, wikitail),
            self.emit_children(node),
            self.formatter.interwikilink(0),
        ])

    def attachment_emit(self, node):
        url = wikiutil.url_unquote(node.content, want_unicode=True)
        text = self.get_text(node)
        return self.formatter.attachment_link(url, text)

    def inlined_attachment_emit(self, node):
        url = wikiutil.url_unquote(node.content, want_unicode=True)
        text = self.get_text(node)
        return self.formatter.attachment_inlined(url, text)

    def image_emit(self, node):
        text = self.get_text(node)
        return self.get_image(node.content, text)

    def drawing_emit(self, node):
        url = wikiutil.url_unquote(node.content, want_unicode=True)
        text = self.get_text(node)
        return self.formatter.attachment_drawing(url, text)

    def figure_emit(self, node):
        text = self.get_text(node)
        url = wikiutil.url_unquote(node.content, want_unicode=True)
        return ''.join([
            self.formatter.rawHTML('<div class="figure">'),
            self.get_image(url, text), self.emit_children(node),
            self.formatter.rawHTML('</div>'),
        ])

    def bad_link_emit(self, node):
        return self.formatter.text(''.join([
            '[[',
            node.content or '',
            ']]',
        ]))

    def macro_emit(self, node):
        macro_name = node.content
        args = node.args
        if self.macro is None:
            self.macro = macro.Macro(self)
        try:
            return self.formatter.macro(self.macro, macro_name, args)
        except:
            return self.formatter.text(self.request.getText('macro error'))

    def section_emit(self, node):
        return ''.join([
            self.formatter.rawHTML(
                '<div class="%s" style="%s">' % (node.sect, node.style)),
            self.emit_children(node),
            self.formatter.rawHTML('</div>'),
        ])

    def break_emit(self, node):
        return ''.join([
            self.formatter.rawHTML('<br>'),
        ])

    def blockquote_emit(self, node):
        return ''.join([
            self.formatter.rawHTML('<blockquote>'),
            self.emit_children(node),
            self.formatter.rawHTML('</blockquote>'),
        ])

    def preformatted_emit(self, node):
        content = node.content
        self.processor_name = getattr(node, 'sect', '')
        self.processor = None
        if self.processor_name:
            self._setProcessor(self.processor_name)
        if self.processor is None:
            return ''.join([
                self.formatter.preformatted(1),
                self.formatter.text(content),
                self.formatter.preformatted(0),
            ])
        else:
            buff = StringIO.StringIO()
            self.request.redirect(buff)
            try:
                self.formatter.processor(
                    self.processor_name,
                    content.split('\n'),
                    self.processor_is_parser)
            finally:
                self.request.redirect()
            return buff.getvalue()

    def default_emit(self, node):
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
        try:
            emit = getattr(self, '%s_emit' % node.kind)
        except:
            emit = self.default_emit
        return emit(node)

    def emit(self):
        # Try to disable 'smart' formatting if possible
        magic_save = getattr(self.formatter, 'no_magic', False)
        self.formatter.no_magic = True
        output = '\n'.join([
            self.emit_node(self.root),
        ])
        self.formatter.no_magic = magic_save
        return output

    def _setProcessor(self, name): # From the wiki.py parser
        """ Set processer to either processor or parser named 'name' """
        cfg = self.request.cfg
        try:
            self.processor = wikiutil.importPlugin(
                cfg,
                "processor",
                name,
                "process")
            self.processor_is_parser = 0
        except wikiutil.PluginMissingError:
            try:
                self.processor = wikiutil.importPlugin(
                    cfg,
                    "parser",
                    name,
                    "Parser")
                self.processor_is_parser = 1
            except wikiutil.PluginMissingError:
                self.processor = None

