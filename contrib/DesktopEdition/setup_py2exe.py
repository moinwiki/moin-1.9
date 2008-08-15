# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - <short description>

    <what this stuff does ... - verbose enough>

    @copyright: 2006 by MoinMoin:YourNameHere 
    @license: GNU GPL, see COPYING for details.
"""

from distutils.core import setup
import py2exe

setup(
    version = "1.6.0.0",
    description = "MMDE is a wiki suitable for desktop use",
    name = "MoinMoin DesktopEdition",

    # targets to build
    console = [{
        "script": "moin.py",
        "icon_resources": [(1, r"..\moin--main--1.6\wiki\htdocs\favicon.ico")],
            }],
    zipfile = r"pylib",
    options = {
        "py2exe": {
            'bundle_files': 2,
            "excludes": ["Tkconstants","Tkinter","tcl", "popen2", "gzip", "gdchart", "mod_python", "_pybsddb",
                         "dbhash", # do not support hashed spellchecker dictionaries
                         "_ssl", # do not support SSL connections
                         "smtplib", 'email.MIMEText', # do not support mails
                         "select", "tty", # just used by pydoc
                         "os2emxpath", #used by os
                         "doctest", # called by test code
                         "MoinMoin.i18n.check_i18n",
                         "teud", "xapian",
                         'Ft.Lib', 'Ft.Xml', 'Ft.Xml.Xslt.Processor', "Ft",
                         #"xml",
                         'Image', 'xml.parsers','xml.sax', 'xml.xslt.Processor',
                         "cookielib", # added because of rst/urllib2
"wikiconfig", # we will supply it manually
"hotshot",
"stringprep", "encodings.idna",

                         ],
            "optimize": 2,
            "includes": ['encodings', 'encodings.iso8859_1', 'encodings.utf_8', 'encodings.ascii', 'encodings.utf_16_be', 'encodings.latin_1', 'encodings.iso8859_15', 'encodings.cp437',
                         'email.Utils',
                         'MoinMoin.action.*', 'MoinMoin.formatter.*', 'MoinMoin.macro.*', 'MoinMoin.parser.*', 'MoinMoin.theme.*',
                         'xml.dom', 'xml.dom.minidom',
                         'docutils.readers.standalone',
                         'docutils.languages.en',
                         'docutils.parsers.rst.directives.*',
                         'docutils.parsers.rst.directives.admonitions',
'docutils.parsers.rst.directives.body',
'docutils.parsers.rst.directives.html',
'docutils.parsers.rst.directives.images',
'docutils.parsers.rst.directives.parts',
'docutils.parsers.rst.directives.references',
"MoinMoin.i18n.zh_tw",
"MoinMoin.i18n.zh",
"MoinMoin.i18n.vi",
"MoinMoin.i18n.sr",
"MoinMoin.i18n.ru",
"MoinMoin.i18n.nl",
"MoinMoin.i18n.nb",
"MoinMoin.i18n.meta",
"MoinMoin.i18n.ko",
"MoinMoin.i18n.ja",
"MoinMoin.i18n.it",
"MoinMoin.i18n.hu",
"MoinMoin.i18n.he",
"MoinMoin.i18n.fr",
"MoinMoin.i18n.es",
"MoinMoin.i18n.en",
"MoinMoin.i18n.de",
"MoinMoin.i18n.da",
"MoinMoin.i18n.__init__",
],
            "dll_excludes": ["w9xpopen.exe", # we dont use popen
                             "bz2.pyd",
"unicodedata.pyd",

                             ],
        }
    }
    )

