3rd party python code requirements
==================================

This file has some notes about the software we bundle and ship with MoinMoin
in the MoinMoin/support/ directory. If you are a Linux distributor and you
want to rip out this stuff and replace it with packages, this is for you!

We list the shipped version and also the minimum required version.
The shipped version will work best with moin as usually has some more bug
fixes than the minimum required version.
We do not test with the minimum required version, but we try to keep this
file updated and correct to our best knowledge.

In case you find bugs in this requirements specification, please let us know!

Thanks to all 3rd party software authors!

flup (cgi/fastcgi/scgi/ajp to WSGI adapter)
===========================================
shipped: 1.0.2+, from repo: hg clone -r 3b07cc2b0c76 http://hg.saddi.com/flup-server
minimum: 1.0.2


pygments (highlighting for all sorts of source code and other text files)
=========================================================================
shipped: 1.1.1
minimum: 1.1.1(?)


parsedatetime (parse date/time strings)
=======================================
shipped: 0.8.7
minimum: 0.8.7(?)


werkzeug (WSGI toolkit)
=======================
shipped: 0.5.1
minimum: 0.5.1(?)


xappy (High-Level Python library for Xapian)
============================================
shipped: 0.5
minimum: 0.5


htmlmarkup.py (safe html rendering)
===================================
shipped: copied from TRAC's trac.util.html, revision 3609, merged on 2006-08-20
minimum: same(?)


Replacements for Python stdlib modules
======================================
difflib.py (fixes broken Python 2.4.3 difflib, see comment in file)
HeaderFixed.py ("copied from email.Header because the original is broken")
tarfile.py (misc. brokenness up to Python 2.6, see comment in file)


Other stuff
===========
BasicAuthTransport.py (taken from Amos' XML-RPC HowTo)
python_compatibility.py (to be compatible with older Pythons)

