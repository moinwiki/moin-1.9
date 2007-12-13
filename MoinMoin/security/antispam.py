# -*- coding: iso-8859-1 -*-
"""
    This implements a global (and a local) blacklist against wiki spammers.

    @copyright: 2005-2007 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details
"""

# give some log entries to stderr
debug = 0

import re, sys, time, datetime
import sets

from MoinMoin.security import Permissions
from MoinMoin import caching, wikiutil

# Errors ---------------------------------------------------------------

class Error(Exception):
    """Base class for antispam errors."""

    def __str__(self):
        return repr(self)

class WikirpcError(Error):
    """ Raised when we get xmlrpclib.Fault """

    def __init__(self, msg, fault):
        """ Init with msg and xmlrpclib.Fault dict """
        self.msg = msg
        self.fault = fault

    def __str__(self):
        """ Format the using description and data from the fault """
        return self.msg + ": [%(faultCode)s]  %(faultString)s" % self.fault


# Functions ------------------------------------------------------------

def dprint(s):
    if debug:
        if isinstance(s, unicode):
            s = s.encode('utf-8')
        sys.stderr.write('%s\n' % s)


def makelist(text):
    """ Split text into lines, strip them, skip # comments """
    lines = text.splitlines()
    result = []
    for line in lines:
        line = line.split(' # ', 1)[0] # rest of line comment
        line = line.strip()
        if line and not line.startswith('#'):
            result.append(line)
    return result


def getblacklist(request, pagename, do_update):
    """ Get blacklist, possibly downloading new copy

    @param request: current request (request instance)
    @param pagename: bad content page name (unicode)
    @rtype: list
    @return: list of blacklisted regular expressions
    """
    from MoinMoin.PageEditor import PageEditor
    p = PageEditor(request, pagename, uid_override="Antispam subsystem")
    mymtime = wikiutil.version2timestamp(p.mtime_usecs())
    if do_update:
        tooold = time.time() - 1800
        failure = caching.CacheEntry(request, "antispam", "failure", scope='wiki')
        fail_time = failure.mtime() # only update if no failure in last hour
        if (mymtime < tooold) and (fail_time < tooold):
            dprint("%d *BadContent too old, have to check for an update..." % tooold)
            import xmlrpclib
            import socket

            timeout = 15 # time out for reaching the master server via xmlrpc
            old_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(timeout)

            master = xmlrpclib.ServerProxy(request.cfg.antispam_master_url)

            try:
                # Get BadContent info
                master.putClientInfo('ANTISPAM-CHECK',
                                     request.http_host+request.script_name)
                response = master.getPageInfo(pagename)

                # It seems that response is always a dict
                if isinstance(response, dict) and 'faultCode' in response:
                    raise WikirpcError("failed to get BadContent information",
                                       response)

                # Compare date against local BadContent copy
                masterdate = response['lastModified']

                if isinstance(masterdate, datetime.datetime):
                    # for python 2.5
                    mydate = datetime.datetime(*tuple(time.gmtime(mymtime))[0:6])
                else:
                    # for python <= 2.4.x
                    mydate = xmlrpclib.DateTime(tuple(time.gmtime(mymtime)))

                dprint("master: %s mine: %s" % (masterdate, mydate))
                if mydate < masterdate:
                    # Get new copy and save
                    dprint("Fetching page from master...")
                    master.putClientInfo('ANTISPAM-FETCH', request.http_host + request.script_name)
                    response = master.getPage(pagename)
                    if isinstance(response, dict) and 'faultCode' in response:
                        raise WikirpcError("failed to get BadContent data", response)
                    p._write_file(response)
                    mymtime = wikiutil.version2timestamp(p.mtime_usecs())
                else:
                    failure.update("") # we didn't get a modified version, this avoids
                                       # permanent polling for every save when there
                                       # is no updated master page

            except (socket.error, xmlrpclib.ProtocolError), err:
                # Log the error
                dprint('Timeout / socket / protocol error when accessing'
                       ' moinmaster: %s' % str(err))
                # update cache to wait before the next try
                failure.update("")

            except (xmlrpclib.Fault, ), err:
                # Log the error
                dprint('Fault on moinmaster: %s' % str(err))
                # update cache to wait before the next try
                failure.update("")

            except Error, err:
                # In case of Error, we log the error and use the local BadContent copy.
                dprint(str(err))

            # set back socket timeout
            socket.setdefaulttimeout(old_timeout)

    blacklist = p.get_raw_body()
    return mymtime, makelist(blacklist)


class SecurityPolicy(Permissions):
    """ Extend the default security policy with antispam feature """

    def save(self, editor, newtext, rev, **kw):
        BLACKLISTPAGES = ["BadContent", "LocalBadContent"]
        if not editor.page_name in BLACKLISTPAGES:
            request = editor.request

            # Start timing of antispam operation
            request.clock.start('antispam')

            blacklist = []
            latest_mtime = 0
            for pn in BLACKLISTPAGES:
                do_update = (pn != "LocalBadContent")
                blacklist_mtime, blacklist_entries = getblacklist(request, pn, do_update)
                blacklist += blacklist_entries
                latest_mtime = max(latest_mtime, blacklist_mtime)

            if blacklist:
                invalid_cache = not getattr(request.cfg.cache, "antispam_blacklist", None)
                if invalid_cache or request.cfg.cache.antispam_blacklist[0] < latest_mtime:
                    mmblcache = []
                    for blacklist_re in blacklist:
                        try:
                            mmblcache.append(re.compile(blacklist_re, re.I))
                        except re.error, err:
                            dprint("Error in regex '%s': %s. Please check the pages %s." % (blacklist_re, str(err), ', '.join(BLACKLISTPAGES)))
                    request.cfg.cache.antispam_blacklist = (latest_mtime, mmblcache)

                from MoinMoin.Page import Page

                oldtext = ""
                if rev > 0: # rev is the revision of the old page
                    page = Page(request, editor.page_name, rev=rev)
                    oldtext = page.get_raw_body()

                newset = sets.ImmutableSet(newtext.splitlines(1))
                oldset = sets.ImmutableSet(oldtext.splitlines(1))
                difference = newset.difference(oldset)
                addedtext = ''.join(difference)

                for blacklist_re in request.cfg.cache.antispam_blacklist[1]:
                    match = blacklist_re.search(addedtext)
                    if match:
                        # Log error and raise SaveError, PageEditor
                        # should handle this.
                        _ = editor.request.getText
                        msg = _('Sorry, can not save page because "%(content)s"'
                                ' is not allowed in this wiki.') % {
                            'content': match.group()
                            }
                        dprint(msg)
                        raise editor.SaveError(msg)
            request.clock.stop('antispam')

        # No problem to save if my base class agree
        return Permissions.save(self, editor, newtext, rev, **kw)
