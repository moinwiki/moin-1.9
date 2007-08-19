"""More comprehensive traceback formatting for Python scripts.

To enable this module, do:

    import cgitb; cgitb.enable()

at the top of your script.  The optional arguments to enable() are:

    display     - if true, tracebacks are displayed in the web browser
    logdir      - if set, tracebacks are written to files in this directory
    context     - number of lines of source code to show for each stack frame
    format      - 'text' or 'html' controls the output format
    viewClass   - sub class of View. Create this if you want to customize the
                  layout of the traceback.
    debug       - may be used by viewClass to decide on level of detail

By default, tracebacks are displayed but not saved, the context is 5 lines
and the output format is 'html' (for backwards compatibility with the
original use of this module).

Alternatively, if you have caught an exception and want cgitb to display it
for you, call cgitb.handler().  The optional argument to handler() is a
3-item tuple (etype, evalue, etb) just like the value of sys.exc_info().
The default handler displays output as HTML.


2005-04-22 Nir Soffer <nirs@freeshell.org>

Rewrite:
 - Refactor html and text functions to View class, HTMLFormatter and
   TextFormatter. No more duplicate formating code.
 - Layout is done with minimal html and css, in a way it can't be
   affected by surrounding code.
 - Built to be easy to subclass and modify without duplicating code.
 - Change layout, important details come first.
 - Factor frame analyzing and formatting into separate class.
 - Add debug argument, can be used to change error display e.g. user
   error view, developer error view.
 - Add viewClass argument, make it easy to customize the traceback view.
 - Easy to customize system details and application details.

The main goal of this rewrite was to have a traceback that can render
few tracebacks combined. It's needed when you wrap an expection and want
to print both the traceback up to the wrapper exception, and the
original traceback. There is no code to support this here, but it's easy
to add by using your own View sub class.
"""

__author__ = 'Ka-Ping Yee'
__version__ = '$Revision: 1.10 $'

import sys, os, pydoc, inspect, linecache, tokenize, keyword


def reset():
    """ Reset the CGI and the browser
    
    Return a string that resets the CGI and browser to a known state.
    TODO: probably some of this is not needed any more.
    """
    return """<!--: spam
Content-Type: text/html

<body><font style="color: white; font-size: 1px"> -->
<body><font style="color: white; font-size: 1px"> --> -->
</font> </font> </font> </script> </object> </blockquote> </pre>
</table> </table> </table> </table> </table> </font> </font> </font>
"""

__UNDEF__ = [] # a special sentinel object


class HiddenObject:
    def __repr__(self):
        return "<HIDDEN>"
HiddenObject = HiddenObject()

class HTMLFormatter:
    """ Minimal html formatter """

    def attributes(self, attributes=None):
        if attributes:
            result = [' %s="%s"' % (k, v) for k, v in attributes.items()]
            return ''.join(result)
        return ''

    def tag(self, name, text, attributes=None):
        return '<%s%s>%s</%s>\n' % (name, self.attributes(attributes), text, name)

    def section(self, text, attributes=None):
        return self.tag('div', text, attributes)

    def title(self, text, attributes=None):
        return self.tag('h1', text, attributes)

    def subTitle(self, text, attributes=None):
        return self.tag('h2', text, attributes)

    def subSubTitle(self, text, attributes=None):
        return self.tag('h3', text, attributes)

    def paragraph(self, text, attributes=None):
        return self.tag('p', text, attributes)

    def list(self, items, attributes=None):
        return self.formatList('ul', items, attributes)

    def orderedList(self, items, attributes=None):
        return self.formatList('ol', items, attributes)

    def formatList(self, name, items, attributes=None):
        """ Send list of raw texts or formatted items. """
        if isinstance(items, (list, tuple)):
            items = '\n' + ''.join([self.listItem(i) for i in items])
        return self.tag(name, items, attributes)

    def listItem(self, text, attributes=None):
        return self.tag('li', text, attributes)

    def link(self, href, text, attributes=None):
        if attributes is None:
            attributes = {}
        attributes['href'] = href
        return self.tag('a', text, attributes)

    def strong(self, text, attributes=None):
        return self.tag('strong', text, attributes)

    def em(self, text, attributes=None):
        return self.tag('em', text, attributes)

    def repr(self, object):
        return pydoc.html.repr(object)


class TextFormatter:
    """ Plain text formatter """

    def section(self, text, attributes=None):
        return text

    def title(self, text, attributes=None):
        lineBellow = '=' * len(text)
        return '%s\n%s\n\n' % (text, lineBellow)

    def subTitle(self, text, attributes=None):
        lineBellow = '-' * len(text)
        return '%s\n%s\n\n' % (text, lineBellow)

    def subSubTitle(self, text, attributes=None):
        lineBellow = '~' * len(text)
        return '%s\n%s\n\n' % (text, lineBellow)

    def paragraph(self, text, attributes=None):
        return text + '\n\n'

    def list(self, items, attributes=None):
        if isinstance(items, (list, tuple)):
            items = [' * %s\n' % i for i in items]
            return ''.join(items) + '\n'
        return items

    def orderedList(self, items, attributes=None):
        if isinstance(items, (list, tuple)):
            result = []
            for i in range(items):
                result.append(' %d. %s\n' % (i, items[i]))
            return ''.join(result) + '\n'
        return items

    def listItem(self, text, attributes=None):
        return ' * %s\n' % text

    def link(self, href, text, attributes=None):
        return '[[%s]]' % text

    def strong(self, text, attributes=None):
        return text

    def em(self, text, attributes=None):
        return text

    def repr(self, object):
        return repr(object)


class Frame:
    """ Analyze and format single frame in a traceback """

    def __init__(self, frame, file, lnum, func, lines, index):
        self.frame = frame
        self.file = file
        self.lnum = lnum
        self.func = func
        self.lines = lines
        self.index = index

    def format(self, formatter):
        """ Return formatted content """
        self.formatter = formatter
        vars, highlight = self.scan()
        items = [self.formatCall(),
                 self.formatContext(highlight),
                 self.formatVariables(vars)]
        return ''.join(items)

    # -----------------------------------------------------------------
    # Private - formatting

    def formatCall(self):
        call = '%s in %s%s' % (self.formatFile(),
                               self.formatter.strong(self.func),
                               self.formatArguments(),)
        return self.formatter.paragraph(call, {'class': 'call'})

    def formatFile(self):
        """ Return formatted file link """
        if not self.file:
            return '?'
        file = pydoc.html.escape(os.path.abspath(self.file))
        return self.formatter.link('file://' + file, file)

    def formatArguments(self):
        """ Return formated arguments list """
        if self.func == '?':
            return ''

        def formatValue(value):
            return '=' + self.formatter.repr(value)

        args, varargs, varkw, locals = inspect.getargvalues(self.frame)
        return inspect.formatargvalues(args, varargs, varkw, locals,
                                       formatvalue=formatValue)

    def formatContext(self, highlight):
        """ Return formatted context, next call highlighted """
        if self.index is None:
            return ''
        context = []
        i = self.lnum - self.index
        for line in self.lines:
            line = '%5d  %s' % (i, pydoc.html.escape(line))
            attributes = {}
            if i in highlight:
                attributes = {'class': 'highlight'}
            context.append(self.formatter.listItem(line, attributes))
            i += 1
        context = '\n' + ''.join(context) + '\n'
        return self.formatter.orderedList(context, {'class': 'context'})

    def formatVariables(self, vars):
        """ Return formatted variables """
        done = {}
        dump = []
        for name, where, value in vars:
            if name in done:
                continue
            done[name] = 1
            if value is __UNDEF__:
                dump.append('%s %s' % (name, self.formatter.em('undefined')))
            else:
                dump.append(self.formatNameValue(name, where, value))
        return self.formatter.list(dump, {'class': 'variables'})

    def formatNameValue(self, name, where, value):
        """ Format variable name and value according to scope """
        if where in ['global', 'builtin']:
            name = '%s %s' % (self.formatter.em(where),
                              self.formatter.strong(name))
        elif where == 'local':
            name = self.formatter.strong(name)
        else:
            name = where + self.formatter.strong(name.split('.')[-1])
        return '%s = %s' % (name, self.formatter.repr(value))

    # ---------------------------------------------------------------
    # Private - analyzing code

    def scan(self):
        """ Scan frame for vars while setting highlight line """
        highlight = {}

        def reader(lnum=[self.lnum]):
            highlight[lnum[0]] = 1
            try:
                return linecache.getline(self.file, lnum[0])
            finally:
                lnum[0] += 1

        vars = self.scanVariables(reader)
        return vars, highlight

    def scanVariables(self, reader):
        """ Lookup variables in one logical Python line """
        vars, lasttoken, parent, prefix, value = [], None, None, '', __UNDEF__
        for ttype, token, start, end, line in tokenize.generate_tokens(reader):
            if ttype == tokenize.NEWLINE:
                break
            if ttype == tokenize.NAME and token not in keyword.kwlist:
                if lasttoken == '.':
                    if parent is not __UNDEF__:
                        if self.unsafe_name(token):
                            value = HiddenObject
                        else:
                            value = getattr(parent, token, __UNDEF__)
                        vars.append((prefix + token, prefix, value))
                else:
                    where, value = self.lookup(token)
                    vars.append((token, where, value))
            elif token == '.':
                prefix += lasttoken + '.'
                parent = value
            else:
                parent, prefix = None, ''
            lasttoken = token
        return vars

    def lookup(self, name):
        """ Return the scope and the value of name """
        scope = None
        value = __UNDEF__
        locals = inspect.getargvalues(self.frame)[3]
        if name in locals:
            scope, value = 'local', locals[name]
        elif name in self.frame.f_globals:
            scope, value = 'global', self.frame.f_globals[name]
        elif '__builtins__' in self.frame.f_globals:
            scope = 'builtin'
            builtins = self.frame.f_globals['__builtins__']
            if isinstance(builtins, dict):
                value = builtins.get(name, __UNDEF__)
            else:
                value = getattr(builtins, name, __UNDEF__)
        if self.unsafe_name(name):
            value = HiddenObject
        return scope, value

    def unsafe_name(self, name):
        return name in self.frame.f_globals.get("unsafe_names", ())

class View:
    """ Traceback view """

    frameClass = Frame # analyze and format a frame

    def __init__(self, info=None, debug=0):
        """ Save starting info or current exception info """
        self.info = info or sys.exc_info()
        self.debug = debug

    def format(self, formatter, context=5):
        self.formatter = formatter
        self.context = context
        return formatter.section(self.formatContent(), {'class': 'cgitb'})

    def formatContent(self):
        """ General layout - override to change layout """
        content = (
            self.formatStylesheet(),
            self.formatTitle(),
            self.formatMessage(),
            self.formatTraceback(),
            self.formatSystemDetails(),
            self.formatTextTraceback(),
            )
        return ''.join(content)

    # -----------------------------------------------------------------
    # Stylesheet

    def formatStylesheet(self):
        """ Format inline html stylesheet """
        return '<style type="text/css">%s</style>' % self.stylesheet()

    def stylesheet(self):
        """ Return stylesheet rules. Override to change rules.

        The rules are sparated to make it easy to extend.

        The stylesheet must work even if sorounding code define the same
        css names, and it must not change the sorounding code look and
        behavior. This is done by having all content in a .traceback
        section.
        """
        return """
.cgitb {background: #E6EAF0; border: 1px solid #4D6180; direction: ltr;}
.cgitb p {margin: 0.5em 0; padding: 5px 10px; text-align: left;}
.cgitb ol {margin: 0}
.cgitb li {margin: 0.25em 0;}
.cgitb h1, .cgitb h2, .cgitb h3 {padding: 5px 10px; margin: 0; background: #4D6180; color: white;}
.cgitb h1 {font-size: 1.3em;}
.cgitb h2 {font-size: 1em; margin-top: 1em;}
.cgitb h3 {font-size: 1em;}
.cgitb .frames {margin: 0; padding: 0; color: #606060}
.cgitb .frames li {display: block;}
.cgitb .call {padding: 5px 10px; background: #A3B4CC; color: black}
.cgitb .context {padding: 0; font-family: monospace; }
.cgitb .context li {display: block; white-space: pre;}
.cgitb .context li.highlight {background: #C0D3F0; color: black}
.cgitb .variables {padding: 5px 10px; font-family: monospace;}
.cgitb .variables li {display: inline;}
.cgitb .variables li:after {content: ", ";}
.cgitb .variables li:last-child:after {content: "";}
.cgitb .exception {border: 1px solid #4D6180; margin: 10px}
.cgitb .exception h3 {background: #4D6180; color: white;}
.cgitb .exception p {color: black;}
.cgitb .exception ul {padding: 0 10px; font-family: monospace;}
.cgitb .exception li {display: block;}
"""

    # -----------------------------------------------------------------
    # Head

    def formatTitle(self):
        return self.formatter.title(self.exceptionTitle(self.info))

    def formatMessage(self):
        return self.formatter.paragraph(self.exceptionMessage(self.info))

    # -----------------------------------------------------------------
    # Traceback

    def formatTraceback(self):
        """ Return formatted traceback """
        return self.formatOneTraceback(self.info)

    def formatOneTraceback(self, info):
        """ Format one traceback
        
        Separate to enable formatting multiple tracebacks.
        """
        output = [self.formatter.subTitle('Traceback'),
                  self.formatter.paragraph(self.tracebackText(info)),
                  self.formatter.orderedList(self.tracebackFrames(info),
                                            {'class': 'frames'}),
                  self.formatter.section(self.formatException(info),
                                         {'class': 'exception'}), ]
        return self.formatter.section(''.join(output), {'class': 'traceback'})

    def tracebackFrames(self, info):
        frames = []
        traceback = info[2]
        for record in inspect.getinnerframes(traceback, self.context):
            frame = self.frameClass(*record)
            frames.append(frame.format(self.formatter))
        del traceback
        return frames

    def tracebackText(self, info):
        return '''A problem occurred in a Python script.  Here is the
        sequence of function calls leading up to the error, in the
        order they occurred.'''

    # --------------------------------------------------------------------
    # Exception

    def formatException(self, info):
        items = [self.formatExceptionTitle(info),
                 self.formatExceptionMessage(info),
                 self.formatExceptionAttributes(info), ]
        return ''.join(items)

    def formatExceptionTitle(self, info):
        return self.formatter.subSubTitle(self.exceptionTitle(info))

    def formatExceptionMessage(self, info):
        return self.formatter.paragraph(self.exceptionMessage(info))

    def formatExceptionAttributes(self, info):
        attribtues = []
        for name, value in self.exceptionAttributes(info):
            value = self.formatter.repr(value)
            attribtues.append('%s = %s' % (name, value))
        return self.formatter.list(attribtues)

    def exceptionAttributes(self, info):
        """ Return list of tuples [(name, value), ...] """
        instance = info[1]
        attribtues = []
        for name in dir(instance):
            if name.startswith('_'):
                continue
            value = getattr(instance, name)
            attribtues.append((name, value))
        return attribtues

    def exceptionTitle(self, info):
        type = info[0]
        return getattr(type, '__name__', str(type))

    def exceptionMessage(self, info):
        instance = info[1]
        return pydoc.html.escape(str(instance))


    # -----------------------------------------------------------------
    # System details

    def formatSystemDetails(self):
        details = ['Date: %s' % self.date(),
                   'Platform: %s' % self.platform(),
                   'Python: %s' % self.python(), ]
        details += self.applicationDetails()
        return (self.formatter.subTitle('System Details') +
                self.formatter.list(details, {'class': 'system'}))

    def date(self):
        import time
        rfc2822Date = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())
        return rfc2822Date

    def platform(self):
        try:
            return pydoc.html.escape(' '.join(os.uname()))
        except:
            return pydoc.html.escape('%s (%s)' % (sys.platform, os.name))

    def python(self):
        return 'Python %s (%s)' % (sys.version.split()[0], sys.executable)

    def applicationDetails(self):
        """ Override for your application """
        return []

    # -----------------------------------------------------------------
    # Text traceback

    def formatTextTraceback(self):
        template = self.textTracebackTemplate()
        return template % self.formatOneTextTraceback(self.info)

    def formatOneTextTraceback(self, info):
        """ Separate to enable formatting multiple tracebacks. """
        import traceback
        return pydoc.html.escape(''.join(traceback.format_exception(*info)))

    def textTracebackTemplate(self):
        return '''
    
<!-- The above is a description of an error in a Python program,
     formatted for a Web browser. In case you are not reading this 
     in a Web browser, here is the original traceback:

%s
-->
'''


class Hook:
    """A hook to replace sys.excepthook that shows tracebacks in HTML."""

    def __init__(self, display=1, logdir=None, context=5, file=None,
                 format="html", viewClass=View, debug=0):
        self.display = display          # send tracebacks to browser if true
        self.logdir = logdir            # log tracebacks to files if not None
        self.context = context          # number of source code lines per frame
        self.file = file or sys.stdout  # place to send the output
        self.format = format
        self.viewClass = viewClass
        self.debug = debug

    def __call__(self, etype, evalue, etb):
        self.handle((etype, evalue, etb))

    def handle(self, info=None):
        info = info or sys.exc_info()
        if self.format.lower() == "html":
            formatter = HTMLFormatter()
            self.file.write(reset())
            plain = False
        else:
            formatter = TextFormatter()
            plain = True
        try:
            view = self.viewClass(info, self.debug)
            doc = view.format(formatter, self.context)
        except:
            raise
            import traceback
            doc = ''.join(traceback.format_exception(*info))
            plain = True

        if self.display:
            if plain:
                doc = doc.replace('&', '&amp;').replace('<', '&lt;')
                self.file.write('<pre>' + doc + '</pre>\n')
            else:
                self.file.write(doc + '\n')
        else:
            self.file.write('<p>A problem occurred in a Python script.\n')

        if self.logdir is not None:
            import tempfile
            suffix = ['.txt', '.html'][self.format == "html"]
            (fd, path) = tempfile.mkstemp(suffix=suffix, dir=self.logdir)
            try:
                file = os.fdopen(fd, 'w')
                file.write(doc)
                file.close()
                msg = '<p> %s contains the description of this error.' % path
            except:
                msg = '<p> Tried to save traceback to %s, but failed.' % path
            self.file.write(msg + '\n')
        try:
            self.file.flush()
        except: pass


handler = Hook().handle

def enable(display=1, logdir=None, context=5, format="html", viewClass=View, debug=0):
    """Install an exception handler that formats tracebacks as HTML.

    The optional argument 'display' can be set to 0 to suppress sending the
    traceback to the browser, and 'logdir' can be set to a directory to cause
    tracebacks to be written to files there."""
    sys.excepthook = Hook(display=display, logdir=logdir, context=context,
                          format=format, viewClass=viewClass, debug=debug)

