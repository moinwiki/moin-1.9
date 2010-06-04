# -*- coding: iso-8859-1 -*-
""" MoinMoin failure

    Handle fatal errors by showing a message and debugging information.

    @copyright: 2004-2005 Nir Soffer <nirs@freeshell.org>
    @license: GNU GPL, see COPYING for details.
"""
import sys, os
import traceback

from MoinMoin import log
logging = log.getLogger(__name__)

from MoinMoin.support import cgitb
from MoinMoin.error import ConfigurationError


class View(cgitb.View):
    """ Display an error message and debugging information

    Additions to cgitb.View:
     - Multiple tracebacks support
     - Debugging information is shown only in debug mode
     - Moin application information
     - General help text and links
     - Handle multiple paragraphs in exception message

    cgitb is heavily modified cgitb, but fully backward compatible with
    the standard cgitb. It should not contain any moin specific code.

    cgitb was refactored to be easy to customize by applications
    developers. This moin specific subclass is an example.
    """
    debugInfoID = 'debug-info'

    def formatContent(self):
        content = (
            self.script(),
            self.formatStylesheet(),
            self.formatTitle(),
            self.formatMessage(),
            self.formatButtons(),
            self.formatDebugInfo(),
            self.formatTextTraceback()
            )
        return ''.join(content)

    def script(self):
        return '''
<script type="text/javascript">
function toggleDebugInfo() {
    var tb = document.getElementById('%s');
    if (tb == null) return;
    tb.style.display = tb.style.display ? '' : 'none';
}
</script>
''' % self.debugInfoID

    def stylesheet(self):
        return cgitb.View.stylesheet(self) + """
.cgitb .buttons {margin: 0.5em 0; padding: 5px 10px;}
.cgitb .buttons li {display: inline; margin: 0; padding: 0 0.25em;}
"""

    def formatMessage(self):
        """ handle multiple paragraphs messages and add general help """
        f = self.formatter
        text = [self.formatExceptionMessage(self.info)]

        if self.info[0] == ConfigurationError:
            tbt = traceback.extract_tb(self.info[1].exceptions()[-1][2])[-1]
            text.append(
                f.paragraph('Error in your configuration file "%s"'
                            ' around line %d.' % tbt[:2]))
        else:
            text.append(
                f.paragraph("If you want to report a bug, please save "
                            "this page and  attach it to your bug report."))
        return ''.join(text)

    def formatButtons(self):
        """ Add 'buttons' to the error dialog """
        f = self.formatter
        buttons = [f.link('javascript:toggleDebugInfo()',
                          'Show debugging information')]
        if self.info[0] != ConfigurationError:
            buttons.append(
                   f.link('http://moinmo.in/MoinMoinBugs',
                          'Report bug'))
            buttons.append(
                   f.link('http://moinmo.in/FrontPage',
                          'Visit MoinMoin wiki'))
        return f.list(buttons, {'class': 'buttons'})

    def formatDebugInfo(self):
        """ Put debugging information in a hidden div """
        attributes = {'id': self.debugInfoID}
        info = [self.debugInfoHideScript(),
                self.formatTraceback(),
                self.formatSystemDetails(), ]
        return self.formatter.section(''.join(info), attributes)

    def debugInfoHideScript(self):
        """ Hide debug info for javascript enabled browsers """
        if self.debug:
            return ''
        return '''
<script type="text/javascript">toggleDebugInfo()</script>
'''

    def formatTraceback(self):
        return self.formatAllTracebacks(self.formatOneTraceback)

    def formatTextTraceback(self):
        template = self.textTracebackTemplate()
        return template % self.formatAllTracebacks(self.formatOneTextTraceback)

    def formatAllTracebacks(self, formatFuction):
        """ Format multiple tracebacks using formatFunction """
        tracebacks = []
        for ttype, tvalue, tb in self.exceptions():
            if ttype is None:
                break
            tracebacks.append(formatFuction((ttype, tvalue, tb)))
            del tb
        return ''.join(tracebacks)

    def exceptions(self):
        """ Return a list of exceptions info, starting at self.info """
        try:
            return [self.info] + self.info[1].exceptions()
        except AttributeError:
            return [self.info]

    def applicationDetails(self):
        """ Add MoinMoin details to system details """
        from MoinMoin import version
        return ['MoinMoin: Release %s (%s)' % (version.release,
                                              version.revision)]

    def formatExceptionMessage(self, info):
        """ Handle multiple paragraphs in exception message """
        text = cgitb.View.exceptionMessage(self, info)
        text = text.split('\n\n')
        text = ''.join([self.formatter.paragraph(item) for item in text])
        return text


def handle(request, err):
    """ Handle failures

    Display fancy error view, or fallback to simple text traceback
    """
    if 'MOIN_DEBUG' in os.environ:
        raise err

    savedError = sys.exc_info()
    logging.exception('An exception occurred, URI was "%s".' % request.request_uri)

    try:
        display = request.cfg.traceback_show # might fail if we have no cfg yet
    except:
        # default to True here to allow an admin setting up the wiki
        # to see the errors made in the configuration file
        display = True

    try:
        debug = 'debug' in request.form
    except:
        debug = False

    try:
        # try to output a nice html error page
        handler = cgitb.Hook(file=request, display=display, viewClass=View, debug=debug)
        handler.handle(savedError)
    except:
        # if that fails, log the cgitb problem ...
        logging.exception('cgitb raised this exception')
        # ... and try again with a simpler output method:
        request.write('<pre>\n')
        printTextException(request, savedError, display)
        request.write('\nAdditionally cgitb raised this exception:\n')
        printTextException(request, display=display)
        request.write('</pre>\n')



def printTextException(request, info=None, display=True):
    """ Simple text exception that should never fail

    Print all exceptions in a composite error.
    """
    if not display:
        request.write("(Traceback display forbidden by configuration)\n")
        return
    from MoinMoin import wikiutil
    if info is None:
        info = sys.exc_info()
    try:
        exceptions = [info] + info[1].exceptions()
    except AttributeError:
        exceptions = [info]
    for info in exceptions:
        text = ''.join(traceback.format_exception(*info))
        text = wikiutil.escape(text)
        request.write(text)

