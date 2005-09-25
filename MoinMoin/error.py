# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - supply common error classes.
    
    TODO: translate strings?

    @copyright: 2004 by Nir Soffer
    @license: GNU GPL, see COPYING for details.
"""

import sys, os

from MoinMoin import config, version

class Error(Exception):
    """ Base class for moin moin errors
    
    Standard errors work safely only with strings using ascii or
    unicode. This class can be used safely with both strings using
    config.charset and unicode.

    You can init this class with either unicode or string using
    config.charset encoding. On output, the class will convert the string
    to unicode or the unicode to string, using config.charset.
            
    When you want to render an error, use unicode() or str() as needed.
    
    """

    def __init__(self, message):
        """ Initialize an error, decode if needed

        @param message: unicode, str or object that support __unicode__
            and __str__. __str__ should use config.charset.
        """
        self.message = message

    def __unicode__(self):
        """ Return unicode error message """
        if isinstance(self.message, str):
            return unicode(self.message, config.charset)
        else:
            return unicode(self.message)
    
    def __str__(self):
        """ Return encoded message """
        if isinstance(self.message, unicode):
            return self.message.encode(config.charset)
        else:
            return str(self.message)

    def __getitem__(self, item):
        """ Make it possible to access attributes like a dict """
        return getattr(self, item)
    
    
class FatalError(Error):
    """ Raise only when we must exit now 
    
    This error is handled at very high level and display a user friendly
    message with the error message you supply.
    
    Using this class will hide the python traceback which is very useful
    to developers. So use it only for known fatal errors, when we know
    what is the error, but still can't continue.

    Do not use this class but its more specific sub classes.
    """
    name = 'MoinMoin Fatal Error'

    # Links on project site that might help to resolve the problem
    baseurl = 'http://moinmoin.wikiwikiweb.de/'
    links = ['HelpOnInstalling', 'HelpOnConfiguration', 'MoinMoinBugs']
    
    def __init__(self, message):
        """ Extend Error with environment details """
        Error.__init__(self, message)
        # Get environment details
        self.system = '%s (%s)' % (sys.platform, os.name)
        self.python = 'Python %s (%s)' % (sys.version.split()[0], sys.executable)
        self.moin = 'MoinMoin release %s (revision %s)' % (
            version.release, version.revision)
        
    def asHTML(self):
        """ Render error as html

        We may not have any style sheets at this stage, using our own
        styles.

        @rtype: unicode
        @return: error formatted as html
        """
        # Make html paragraphs from text paragraphs separated by empty lines
        message = [u'<p>%s</p>' % p for p in unicode(self).split(u'\n\n')]
        message = '\n'.join(message)

        # Make links list in the project site
        links = [u'<li><a href="%s%s">%s</a></li>' % (self.baseurl, link, link)
                 for link in self.links]
        links = u'<ul class="links">\n%s\n</ul>\n' % '\n'.join(links)

        html = [
            u'''
<html>
    <head>
        <title>%(name)s</title>
        <style type="text/css">
            h1 {font-size: 1.3em; margin: 0}
            .message {border: 1px solid gray; background: #f7f7f7; margin:20px;}
            .content {padding: 15px;}
            .info {font-size: 0.85em; color: gray;}
            ul.info {margin: 0; padding: 0;}
            ul.links {margin: 5px 15px; padding: 0;}
            ul.info li, ul.links li {display: inline; margin: 0 5px;}
            hr {background: none; height: 0; border: none; border-top: 1px dotted gray;
                margin: 0; padding: 0;}
        </style>
    </head>
    <body>
        <div class="message">
            <div class="content">
                <h1>%(name)s</h1>''' % self,
            message,
            u'''
                <ul class="info">
                    <li>%(system)s</li>
                    <li>%(python)s</li>
                    <li>%(moin)s</li>
                </ul>
            </div>
            <hr>''' % self,
            links,
            u'''
        </div>
    </body>
</html>
''',]
        html = '\n'.join(html)
        return html

    def asLog(self):
        """ Render error for logs

        For log we don't need all the 'nice' stuff we show for a
        user. Just the plain error.

        @rtype: string
        @return: error formatted for log
        """
        return '%s: %s' % (self.name, str(self))


class ConfigurationError(FatalError):
    """ Raise when fatal misconfiguration is found
    """
    name = 'MoinMoin Configuration Error'
        

class InternalError(FatalError):
    """ Raise when internal fatal error is found
    """
    name = 'MoinMoin Internal Error'


class ConvertError(FatalError):
    """ Raise when html to wiki conversion fails
    """
    name = 'MoinMoin Converter Error'


