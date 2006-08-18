# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Utility Functions
    General helper functions that are not directly wiki related.

    @copyright: 2004 Juergen Hermann, Thomas Waldmann
    @license: GNU GPL, see COPYING for details.
"""

import os, sys, re, random

#############################################################################
### XML helper functions
#############################################################################

g_xmlIllegalCharPattern = re.compile('[\x01-\x08\x0B-\x0D\x0E-\x1F\x80-\xFF]')
g_undoUtf8Pattern = re.compile('\xC2([^\xC2])')
g_cdataCharPattern = re.compile('[&<\'\"]')
g_textCharPattern = re.compile('[&<]')
g_charToEntity = {
    '&': '&amp;',
    '<': '&lt;',
    "'": '&apos;',
    '"': '&quot;'
}

def TranslateCDATA(text):
    """
        Convert a string to a CDATA-encoded one
        Copyright (c) 1999-2000 FourThought, http://4suite.com/4DOM
    """
    new_string, num_subst = re.subn(g_undoUtf8Pattern, lambda m: m.group(1), text)
    new_string, num_subst = re.subn(g_cdataCharPattern, lambda m, d=g_charToEntity: d[m.group()], new_string)
    new_string, num_subst = re.subn(g_xmlIllegalCharPattern, lambda m: '&#x%02X;' % ord(m.group()), new_string)
    return new_string

def TranslateText(text):
    """
        Convert a string to a PCDATA-encoded one (do minimal encoding)
        Copyright (c) 1999-2000 FourThought, http://4suite.com/4DOM
    """
    new_string, num_subst = re.subn(g_undoUtf8Pattern, lambda m: m.group(1), text)
    new_string, num_subst = re.subn(g_textCharPattern, lambda m, d=g_charToEntity: d[m.group()], new_string)
    new_string, num_subst = re.subn(g_xmlIllegalCharPattern, lambda m: '&#x%02X;' % ord(m.group()), new_string)
    return new_string


#############################################################################
### Misc
#############################################################################

def rangelist(numbers):
    """ Convert a list of integers to a range string in the form
        '1,2-5,7'.
    """
    numbers = numbers[:]
    numbers.sort()
    numbers.append(999999)
    pattern = ','
    for i in range(len(numbers)-1):
        if pattern[-1] == ',':
            pattern = pattern + str(numbers[i])
            if numbers[i] + 1 == numbers[i+1]:
                pattern = pattern + '-'
            else:
                pattern = pattern + ','
        elif numbers[i] + 1 != numbers[i+1]:
            pattern = pattern + str(numbers[i]) + ','

    if pattern[-1] in ',-':
        return pattern[1:-1]
    return pattern[1:]

def dumpFormData(form):
    """ Dump the form data for debugging purposes
    """
    from MoinMoin import wikiutil

    result = '<dt><strong>Form entries</strong></dt>'
    for k in form.keys():
        v = form.get(k, ["<empty>"])
        v = "|".join(v)
        result = result + '<dd><em>%s</em>=%s</dd>' % (k, wikiutil.escape(v))

    return result

def IsWin9x():
    """ Returns true if run on Windows 95, 98 or ME. """
    if hasattr(sys, 'getwindowsversion'):
        if sys.getwindowsversion()[3] == 1:
            return True
    elif 'command' in os.environ.get('comspec', ''):
        return True
    return False


class simpleIO:
    """ A simple StringIO replacement for code that calls us
        with ascii, Unicode and iso-8859-1 data. Wee, that is fun. """

    def __init__(self):
        self.buffer = []

    def write(self, foo):
        if not isinstance(foo, unicode):
            foo = foo.decode("iso-8859-1", "replace")
        self.buffer.append(foo)

    def getvalue(self):
        return u''.join(self.buffer)

    def close(self):
        self.buffer = None


def random_string(length):
    chars = ''.join([chr(random.randint(0, 255)) for x in xrange(length)])
    return chars

