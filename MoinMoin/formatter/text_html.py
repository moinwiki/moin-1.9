# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - "text/html+css" Formatter

    @copyright: 2000 - 2004 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""
import os.path, re
from MoinMoin.formatter.base import FormatterBase
from MoinMoin import wikiutil, i18n, config
from MoinMoin.Page import Page
from MoinMoin.action import AttachFile

class Formatter(FormatterBase):
    """
        Send HTML data.
    """

    hardspace = '&nbsp;'

    def __init__(self, request, **kw):
        apply(FormatterBase.__init__, (self, request), kw)

        # inline tags stack. When an inline tag is called, it goes into
        # the stack. When a block element starts, all inline tags in
        # the stack are closed.
        self._inlineStack = []

        self._in_li = 0
        self._in_code = 0
        self._in_code_area = 0
        self._in_code_line = 0
        self._code_area_num = 0
        self._code_area_js = 0
        self._code_area_state = ['', 0, -1, -1, 0]
        self._show_section_numbers = None
        self._content_ids = []
        self.pagelink_preclosed = False
        self._is_included = kw.get('is_included',False)
        self.request = request
        self.cfg = request.cfg

        if not hasattr(request, '_fmt_hd_counters'):
            request._fmt_hd_counters = []

    # Primitive formatter functions #####################################

    # all other methods should use these to format tags. This keeps the
    # code clean and handle pathological cases like unclosed p and
    # inline tags.

    def langAttr(self, lang=None):
        """ Return lang and dir attribute

        Must be used on all block elements - div, p, table, etc.
        @param lang: if defined, will return attributes for lang. if not
            defined, will return attributes only if the current lang is
            different from the content lang.
        @rtype: dict
        @retrun: language attributes
        """
        if not lang:
            lang = self.request.current_lang
            # Actions that generate content in user language should change
            # the content lang from the default defined in cfg.
            if lang == self.request.content_lang:
                # lang is inherited from content div
                return {}

        attr = {'lang': lang, 'dir': i18n.getDirection(lang),}
        return attr

    def formatAttributes(self, attr=None):
        """ Return formatted attributes string

        @param attr: dict containing keys and values
        @rtype: string ?
        @return: formated attributes or empty string
        """
        if attr:
            attr = [' %s="%s"' % (k, v) for k, v in attr.items()]           
            return ''.join(attr)
        return ''

    # TODO: use set when we require Python 2.3
    # TODO: The list is not complete, add missing from dtd
    _blocks = 'p div pre table tr td ol ul dl li dt dd h1 h2 h3 h4 h5 h6 hr form'
    _blocks = dict(zip(_blocks.split(), [1] * len(_blocks)))

    def open(self, tag, newline=False, attr=None):
        """ Open a tag with optional attributes
        
        @param tag: html tag, string
        @param newline: render tag on a separate line
        @parm attr: dict with tag attributes
        @rtype: string ?
        @return: open tag with attributes
        """
        if tag in self._blocks:
            # Block elements
            result = []
            
            # Add language attributes, but let caller overide the default
            attributes = self.langAttr()
            if attr:
                attributes.update(attr)
            
            # Format
            attributes = self.formatAttributes(attributes)
            result.append('<%s%s>' % (tag, attributes))
            if newline:
                result.append('\n')
            return ''.join(result)
        else:
            # Inline elements
            # Add to inlineStack
            self._inlineStack.append(tag)
            # Format
            return '<%s%s>' % (tag, self.formatAttributes(attr))
       
    def close(self, tag, newline=False):
        """ Close tag

        @param tag: html tag, string
        @rtype: string ?
        @return: closing tag
        """
        if tag in self._blocks:
            # Block elements
            # Close all tags in inline stack
            # Work on a copy, because close(inline) manipulate the stack
            result = []
            stack = self._inlineStack[:]
            stack.reverse()
            for inline in stack:
                result.append(self.close(inline))
            # Format with newline
            if newline:
                result.append('\n')
            result.append('</%s>\n' % (tag))
            return ''.join(result)            
        else:
            # Inline elements 
            # Pull from stack, ignore order, that is not our problem.
            # The code that calls us should keep correct calling order.
            if tag in self._inlineStack:
                self._inlineStack.remove(tag)
            return '</%s>' % tag


    # Public methods ###################################################

    def startContent(self, content_id='content', **kwargs):
        """ Start page content div """

        # Setup id
        if content_id!='content':
            aid = 'top_%s' % (content_id,)
        else:
            aid = 'top'
        self._content_ids.append(content_id)
        result = []
        # Use the content language
        attr = self.langAttr(self.request.content_lang)
        attr['id'] = content_id
        result.append(self.open('div', newline=1, attr=attr))
        result.append(self.anchordef(aid))
        return ''.join(result)
        
    def endContent(self):
        """ Close page content div """

        # Setup id
        try:
            cid = self._content_ids.pop()
        except:
            cid = 'content'
        if cid!='content':
            aid = 'bottom_%s' % (cid,)
        else:
            aid = 'bottom'

        result = []
        result.append(self.anchordef(aid))
        result.append(self.close('div', newline=1))
        return ''.join(result) 

    def lang(self, on, lang_name):
        """ Insert text with specific lang and direction.
        
            Enclose within span tag if lang_name is different from
            the current lang    
        """
        tag = 'span'
        if lang_name != self.request.current_lang:
            # Enclose text in span using lang attributes
            if on:
                attr = self.langAttr(lang=lang_name)
                return self.open(tag, attr=attr)
            return self.close(tag)

        # Direction did not change, no need for span
        return ''            
                
    def sysmsg(self, on, **kw):
        tag = 'div'
        if on:
            return self.open(tag, attr={'class': 'message'})
        return self.close(tag)
    
    # Links ##############################################################
    
    def pagelink(self, on, pagename='', page=None, **kw):
        """ Link to a page.

            formatter.text_python will use an optimized call with a page!=None
            parameter. DO NOT USE THIS YOURSELF OR IT WILL BREAK.

            See wikiutil.link_tag() for possible keyword parameters.
        """
        apply(FormatterBase.pagelink, (self, on, pagename, page), kw)
        self.pagelink_preclosed = False
        if page is None:
            page = Page(self.request, pagename, formatter=self);
        if self.request.user.show_nonexist_qm and on and not page.exists():
            self.pagelink_preclosed = True
            return (page.link_to(self.request, on=1, **kw) +
                    self.text("?") +
                    page.link_to(self.request, on=0, **kw))
        elif not on and self.pagelink_preclosed:
            return ""
        else:
            return page.link_to(self.request, on=on, **kw)

    def interwikilink(self, on, interwiki='', pagename='', **kw):
        """
        @keyword title: override using the interwiki wikiname as title
        """
        if not on:
            return '</a>'
        wikitag, wikiurl, wikitail, wikitag_bad = wikiutil.resolve_wiki(self.request, '%s:%s' % (interwiki, pagename))
        wikiurl = wikiutil.mapURL(self.request, wikiurl)
        if wikitag == 'Self': # for own wiki, do simple links
            if wikitail.find('#') > -1:
                wikitail, kw['anchor'] = wikitail.split('#', 1)
            wikitail = wikiutil.url_unquote(wikitail)
            try: # XXX this is the only place where we access self.page - do we need it? Crashes silently on actions!
                return apply(self.pagelink, (on, wikiutil.AbsPageName(self.request, self.page.page_name, wikitail)), kw)
            except:
                return apply(self.pagelink, (on, wikitail), kw)
        else: # return InterWiki hyperlink
            href = wikiutil.join_wiki(wikiurl, wikitail)
            if wikitag_bad:
                html_class = 'badinterwiki'
            else:
                html_class = 'interwiki'
            title = kw.get('title', wikitag)
            return self.url(1, href, title=title, unescaped=0, css=html_class)
            # unescaped=1 was changed to 0 to make interwiki links with pages with umlauts (or other non-ascii) work

    def url(self, on, url=None, css=None, **kw):
        """
            Keyword params:
                title - <a> title attribute
                attrs -  just include those <a> attrs "as is"
        """
        if url is not None:
            url = wikiutil.mapURL(self.request, url)
        title = kw.get('title', None)
        attrs = kw.get('attrs', None)
        if on:
            str = '<a'
            if css: 
                str = '%s class="%s"' % (str, css)
            if title:
                str = '%s title="%s"' % (str, title)
            if attrs:
                str = '%s %s' % (str, attrs)
            str = '%s href="%s">' % (str, wikiutil.escape(url, 1))
        else:
            str = '</a>'
        return str

    def anchordef(self, id):
        #return '<a id="%s"></a>' % (id, ) # this breaks PRE sections for IE
        # do not add a \n here, it breaks pre sections with line_anchordef
        return '<span id="%s" class="anchor"></span>' % (id, )

    def line_anchordef(self, lineno):
        return self.anchordef("line-%d" % lineno)

    def anchorlink(self, on, name='', id=None):
        extra = ''
        if id:
            extra = ' id="%s"' % id
        return ['<a href="#%s"%s>' % (name, extra), '</a>'][not on]

    def line_anchorlink(self, on, lineno=0):
        return self.anchorlink(on, name="line-%d" % lineno)

    # Attachments ######################################################

    def attachment_link(self, url, text, **kw):
        _ = self.request.getText
        pagename, filename = AttachFile.absoluteName(url, self.page.page_name)
        fname = wikiutil.taintfilename(filename)
        fpath = AttachFile.getFilename(self.request, pagename, fname)
        if not os.path.exists(fpath):
            linktext = _('Upload new attachment "%(filename)s"')
            return wikiutil.link_tag(
                self.request,
                ('%s?action=AttachFile&rename=%s' %
                 (wikiutil.quoteWikinameURL(pagename),
                  wikiutil.url_quote_plus(fname))),
                linktext % {'filename': self.text(fname)})
        target = AttachFile.getAttachUrl(pagename, filename, self.request)
        return (self.url(1, target, css='attachment', title="attachment:%s" % url) +
                self.text(text) +
                self.url(0))
    
    def attachment_image(self, url, **kw):
        _ = self.request.getText
        pagename, filename = AttachFile.absoluteName(url, self.page.page_name)
        fname = wikiutil.taintfilename(filename)
        fpath = AttachFile.getFilename(self.request, pagename, fname)
        if not os.path.exists(fpath):
            linktext = _('Upload new attachment "%(filename)s"')
            return wikiutil.link_tag(
                self.request,
                ('%s?action=AttachFile&rename=%s' %
                 (wikiutil.quoteWikinameURL(pagename),
                  wikiutil.url_quote_plus(fname))),
                linktext % {'filename': self.text(fname)})
        return self.image(
            title="attachment:%s" % url,
            src=AttachFile.getAttachUrl(pagename, filename, self.request, addts=1))
    
    def attachment_drawing(self, url, text, **kw):
        _ = self.request.getText
        pagename, filename = AttachFile.absoluteName(url, self.page.page_name)
        fname = wikiutil.taintfilename(filename)
        drawing = fname
        fname = fname + u".png"
        filename = filename + u".png"
        # fallback for old gif drawings (1.1 -> 1.2)
        fpath = AttachFile.getFilename(self.request, pagename, fname)
        if not os.path.exists(fpath):
            gfname = fname[:-4] + u".gif"
            gfilename = filename[:-4] + u".gif"
            gfpath = AttachFile.getFilename(self.request, pagename, gfname)
            if os.path.exists(gfpath):
                fname, filename, fpath = gfname, gfilename, gfpath

        # check whether attachment exists, possibly point to upload form
        if not os.path.exists(fpath):
            linktext = _('Create new drawing "%(filename)s"')
            return wikiutil.link_tag(
                self.request,
                ('%s?action=AttachFile&rename=%s%s' %
                 (wikiutil.quoteWikinameURL(pagename),
                  wikiutil.url_quote_plus(fname),
                  drawing and ('&drawing=%s' % wikiutil.url_quote(drawing)) or '')),
                linktext % {'filename': self.text(fname)})

        mappath = AttachFile.getFilename(self.request, pagename, drawing + u'.map')
        edit_link = ('%s?action=AttachFile&rename=%s&drawing=%s' % (
            wikiutil.quoteWikinameURL(pagename),
            wikiutil.url_quote_plus(fname),
            wikiutil.url_quote(drawing)))

        # check for map file
        if os.path.exists(mappath):
            # we have a image map. inline it and add a map ref
            # to the img tag
            try:
                map = open(mappath,'r').read()
            except IOError:
                pass
            except OSError:
                pass
            else:
                mapid = 'ImageMapOf'+drawing
                # replace MAPNAME
                map = map.replace('%MAPNAME%', mapid)
                # add alt and title tags to areas
                map = re.sub('href\s*=\s*"((?!%TWIKIDRAW%).+?)"',r'href="\1" alt="\1" title="\1"',map)
                # add in edit links plus alt and title attributes
                map = map.replace('%TWIKIDRAW%"', edit_link + '" alt="' + _('Edit drawing %(filename)s') % {'filename': self.text(fname)} + '" title="' + _('Edit drawing %(filename)s') % {'filename': self.text(fname)} + '"')
                # unxml, because 4.01 concrete will not validate />
                map = map.replace('/>','>')
                return (map + self.image(
                    alt=drawing,
                    src=AttachFile.getAttachUrl(
                    pagename, filename, self.request,
                    addts=1),
                    usemap='#'+mapid, html_class="drawing"))
        else:
            return wikiutil.link_tag(self.request,
                                     edit_link,
                                     self.image(alt=url,
                                                src=AttachFile.getAttachUrl(pagename, filename, self.request, addts=1), html_class="drawing"),
                                     attrs='title="%s"' % (_('Edit drawing %(filename)s') % {'filename': self.text(fname)}))
        
    
    # def attachment_inlined(self, url, text, **kw):
    # moved to MoinMoin/formatter/base.py


    # Text ##############################################################
    
    def _text(self, text):
        if self._in_code:
            return wikiutil.escape(text).replace(' ', self.hardspace)
        return wikiutil.escape(text)

    # Inline ###########################################################
        
    def strong(self, on):
        tag = 'strong'
        if on:
            return self.open(tag)
        return self.close(tag)

    def emphasis(self, on):
        tag = 'em'
        if on:
            return self.open(tag)
        return self.close(tag)

    def underline(self, on):
        tag = 'span'
        if on:
            return self.open(tag, attr={'class': 'u'})
        return self.close(tag)

    def highlight(self, on):
        tag = 'strong'
        if on:
            return self.open(tag, attr={'class': 'highlight'})
        return self.close(tag)

    def sup(self, on):
        tag = 'sup'
        if on:
            return self.open(tag)
        return self.close(tag)

    def sub(self, on):
        tag = 'sub'
        if on:
            return self.open(tag)
        return self.close(tag)

    def strike(self, on):
        tag = 'strike'
        if on:
            return self.open(tag)
        return self.close(tag)

    def code(self, on, **kw):
        tag = 'tt'
        # Maybe we don't need this, because we have tt will be in inlineStack.
        self._in_code = on        
        if on:
            return self.open(tag)
        return self.close(tag)
        
    def small(self, on):
        tag = 'small'
        if on:
            return self.open(tag)
        return self.close(tag)

    def big(self, on):
        tag = 'big'
        if on:
            return self.open(tag)
        return self.close(tag)


    # Block elements ####################################################

    def preformatted(self, on, attr=None):
        FormatterBase.preformatted(self, on)
        tag = 'pre'
        if on:
            return self.open(tag, newline=1, attr=attr)
        return self.close(tag)
                
    # Use by code area
    _toggleLineNumbersScript = """
<script type="text/JavaScript">
function isnumbered(obj) {
  return obj.childNodes.length && obj.firstChild.childNodes.length && obj.firstChild.firstChild.className == 'LineNumber';
}
function nformat(num,chrs,add) {
  var nlen = Math.max(0,chrs-(''+num).length), res = '';
  while (nlen>0) { res += ' '; nlen-- }
  return res+num+add;
}
function addnumber(did, nstart, nstep) {
  var c = document.getElementById(did), l = c.firstChild, n = 1;
  if (!isnumbered(c))
    if (typeof nstart == 'undefined') nstart = 1;
    if (typeof nstep  == 'undefined') nstep = 1;
    n = nstart;
    while (l != null) {
      if (l.tagName == 'SPAN') {
        var s = document.createElement('SPAN');
        s.className = 'LineNumber'
        s.appendChild(document.createTextNode(nformat(n,4,' ')));
        n += nstep;
        if (l.childNodes.length)
          l.insertBefore(s, l.firstChild)
        else
          l.appendChild(s)
      }
      l = l.nextSibling;
    }
  return false;
}
function remnumber(did) {
  var c = document.getElementById(did), l = c.firstChild;
  if (isnumbered(c))
    while (l != null) {
      if (l.tagName == 'SPAN' && l.firstChild.className == 'LineNumber') l.removeChild(l.firstChild);
      l = l.nextSibling;
    }
  return false;
}
function togglenumber(did, nstart, nstep) {
  var c = document.getElementById(did);
  if (isnumbered(c)) {
    remnumber(did);
  } else {
    addnumber(did,nstart,nstep);
  }
  return false;
}
</script>
"""
    
    def code_area(self, on, code_id, code_type='code', show=0, start=-1, step=-1):
        res = []
        ci = self.request.makeUniqueID('CA-%s_%03d' % (code_id, self._code_area_num))
        if on:
            # Open a code area
            self._in_code_area = 1
            self._in_code_line = 0
            self._code_area_state = [ci, show, start, step, start]

            # Open the code div - using left to right always!
            attr = {'class': 'codearea', 'lang': 'en', 'dir': 'ltr'}
            res.append(self.open('div', attr=attr))

            # Add the script only in the first code area on the page
            if self._code_area_js == 0 and self._code_area_state[1] >= 0:
                res.append(self._toggleLineNumbersScript)
                self._code_area_js = 1

            # Add line number link, but only for JavaScript enabled browsers.
            if self._code_area_state[1] >= 0:
                toggleLineNumbersLink = r'''
<script type="text/javascript">
document.write('<a href="#" onClick="return togglenumber(\'%s\', %d, %d);" \
                class="codenumbers">Toggle line numbers<\/a>');
</script>
''' % (self._code_area_state[0], self._code_area_state[2], self._code_area_state[3])
                res.append(toggleLineNumbersLink)

            # Open pre - using left to right always!
            attr = {'id': self._code_area_state[0], 'lang': 'en', 'dir': 'ltr'}
            res.append(self.open('pre', newline=True, attr=attr))
        else:
            # Close code area
            res = []
            if self._in_code_line:
                res.append(self.code_line(0))
            res.append(self.close('pre'))
            res.append(self.close('div'))

            # Update state
            self._in_code_area = 0
            self._code_area_num += 1

        return ''.join(res)

    def code_line(self, on):
        res = ''
        if not on or (on and self._in_code_line):
            res += '</span>\n'
        if on:
            res += '<span class="line">'
            if self._code_area_state[1] > 0:
                res += '<span class="LineNumber">%4d </span>' % (self._code_area_state[4], )
                self._code_area_state[4] += self._code_area_state[3]
        self._in_code_line = on != 0
        return res

    def code_token(self, on, tok_type):
        return ['<span class="%s">' % tok_type, '</span>'][not on]

    # Paragraphs, Lines, Rules ###########################################
    
    def linebreak(self, preformatted=1):
        if self._in_code_area:
            preformatted = 1
        return ['\n', '<br>\n'][not preformatted]
        
    def paragraph(self, on):
        if self._terse:
            return ''
        FormatterBase.paragraph(self, on)
        if self._in_li:
            self._in_li = self._in_li + 1
        tag = 'p'
        if on:
            return self.open(tag)
        return self.close(tag)
            
    def rule(self, size=None):
        if size:
            # Add hr class: hr1 - hr6
            return self.open('hr', newline=1, attr={'class': 'hr%d' % size})
        return self.open('hr', newline=1)
                
    def icon(self, type):
        return self.request.theme.make_icon(type)

    def smiley(self, text):
        w, h, b, img = config.smileys[text.strip()]
        href = img
        if not href.startswith('/'):
            href = self.request.theme.img_url(img)
        return self.image(src=href, alt=text, width=str(w), height=str(h))

    # Lists ##############################################################

    def number_list(self, on, type=None, start=None):
        tag = 'ol'
        if on:
            attr = {}
            if type is not None:
                attr['type'] = type
            if start is not None:
                attr['start'] = start
            return self.open(tag, newline=1, attr=attr)
        return self.close(tag)
    
    def bullet_list(self, on):
        tag = 'ul'
        if on:
            return self.open(tag, newline=1)
        return self.close(tag)
           
    def listitem(self, on, **kw):
        """ List item inherit its lang from the list. """
        tag = 'li'
        self._in_li = on != 0
        if on:
            attr = {}
            css_class = kw.get('css_class', None)
            if css_class:
                attr['class'] = css_class
            style = kw.get('style', None)
            if style:
                attr['style'] = style
            return self.open(tag, attr=attr)
        return self.close(tag)

    def definition_list(self, on):
        tag = 'dl'
        if on:
            return self.open(tag, newline=1)
        return self.close(tag)

    def definition_term(self, on):
        tag = 'dt'
        if on:
            return self.open(tag)
        return self.close(tag)
        
    def definition_desc(self, on):
        tag = 'dd'
        if on:
            return self.open(tag)
        return self.close(tag)

    def heading(self, on, depth, id = None, **kw):
        # remember depth of first heading, and adapt counting depth accordingly
        if not self._base_depth:
            self._base_depth = depth

        count_depth = max(depth - (self._base_depth - 1), 1)

        # check numbering, possibly changing the default
        if self._show_section_numbers is None:
            self._show_section_numbers = self.cfg.show_section_numbers
            numbering = self.request.getPragma('section-numbers', '').lower()
            if numbering in ['0', 'off']:
                self._show_section_numbers = 0
            elif numbering in ['1', 'on']:
                self._show_section_numbers = 1
            elif numbering in ['2', '3', '4', '5', '6']:
                # explicit base level for section number display
                self._show_section_numbers = int(numbering)

        heading_depth = depth # + 1

        # closing tag, with empty line after, to make source more readable
        if not on:
            return self.close('h%d' % heading_depth) + '\n'
            
        # create section number
        number = ''
        if self._show_section_numbers:
            # count headings on all levels
            self.request._fmt_hd_counters = self.request._fmt_hd_counters[:count_depth]
            while len(self.request._fmt_hd_counters) < count_depth:
                self.request._fmt_hd_counters.append(0)
            self.request._fmt_hd_counters[-1] = self.request._fmt_hd_counters[-1] + 1
            number = '.'.join(map(str, self.request._fmt_hd_counters[self._show_section_numbers-1:]))
            if number: number += ". "

        attr = {}
        if id:
            attr['id'] = id
        # Add space before heading, easier to check source code
        result = '\n' + self.open('h%d' % heading_depth, attr=attr)

        # TODO: convert this to readable code
        if self.request.user.show_topbottom:
            # TODO change top/bottom refs to content-specific top/bottom refs?
            result = ("%s%s%s%s%s%s%s%s" %
                      (result,
                       kw.get('icons',''),
                       self.url(1, "#bottom", unescaped=1),
                       self.icon('bottom'),
                       self.url(0),
                       self.url(1, "#top", unescaped=1),
                       self.icon('top'),
                       self.url(0)))
        return "%s%s%s" % (result, kw.get('icons',''), number)

    
    # Tables #############################################################

    _allowed_table_attrs = {
        'table': ['class', 'id', 'style'],
        'row': ['class', 'id', 'style'],
        '': ['colspan', 'rowspan', 'class', 'id', 'style'],
    }

    def _checkTableAttr(self, attrs, prefix):
        """ Check table attributes

        Convert from wikitable attributes to html 4 attributes.

        @param attrs: attribute dict
        @param prefix: used in wiki table attributes
        @rtyp: dict
        @return: valid table attributes
        """
        if not attrs:
            return {}

        result = {}
        s = "" # we collect synthesized style in s
        for key, val in attrs.items():
            # Ignore keys that don't start with prefix
            if prefix and key[:len(prefix)] != prefix:
                continue
            key = key[len(prefix):]
            val = val.strip('"')
            # remove invalid attrs from dict and synthesize style
            if key == 'width':
                s += "width: %s;" % val
            elif key == 'height':
                s += "height: %s;" % val
            elif key == 'bgcolor':
                s += "background-color: %s;" % val
            elif key == 'align':
                s += "text-align: %s;" % val
            elif key == 'valign':
                s += "vertical-align: %s;" % val
            # Ignore unknown keys
            if key not in self._allowed_table_attrs[prefix]:
                continue
            result[key] = val
        if s:
            if result.has_key('style'):
                result['style'] += s
            else:
                result['style'] = s
        return result


    def table(self, on, attrs=None):
        """ Create table

        @param on: start table
        @param attrs: table attributes
        @rtype: string
        @return start or end tag of a table
        """
        result = []
        if on:
            # Open div to get correct alignment with table width smaller
            # than 100%
            result.append(self.open('div', newline=1))

            # Open table
            if not attrs:
                attrs = {}
            else:
                attrs = self._checkTableAttr(attrs, 'table')
            result.append(self.open('table', newline=1, attr=attrs))
        else:
            # Close table then div
            result.append(self.close('table'))
            result.append(self.close('div'))

        return ''.join(result)    
    
    def table_row(self, on, attrs=None):
        tag = 'tr'
        if on:
            if not attrs:
                attrs = {}
            else:
                attrs = self._checkTableAttr(attrs, 'row')
            return self.open(tag, newline=1, attr=attrs)
        return self.close(tag)
    
    def table_cell(self, on, attrs=None):
        tag = 'td'
        if on:
            if not attrs:
                attrs = {}
            else:
                attrs = self._checkTableAttr(attrs, '')
            return self.open(tag, newline=1, attr=attrs)
        return self.close(tag)

    def escapedText(self, text):
        return wikiutil.escape(text)

    def rawHTML(self, markup):
        return markup

