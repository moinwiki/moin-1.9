# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Wiki XMLRPC v1 and v2 Interface + plugin extensions

    Parts of this code are based on Juergen Hermann's wikirpc.py,
    Les Orchard's "xmlrpc.cgi" and further work by Gustavo Niemeyer.

    See http://www.ecyrd.com/JSPWiki/Wiki.jsp?page=WikiRPCInterface
    and http://www.decafbad.com/twiki/bin/view/Main/XmlRpcToWiki
    for specs on many of the functions here.

    See also http://www.jspwiki.org/Wiki.jsp?page=WikiRPCInterface2
    for the new stuff.

    The main difference between v1 and v2 is that v2 relies on utf-8
    as transport encoding. No url-encoding and no base64 anymore, except
    when really necessary (like for transferring binary files like
    attachments maybe).

    @copyright: 2003-2008 MoinMoin:ThomasWaldmann,
                2004-2006 MoinMoin:AlexanderSchremmer
                2007-2009 MoinMoin:ReimarBauer
    @license: GNU GPL, see COPYING for details
"""
from MoinMoin.util import pysupport

modules = pysupport.getPackageModules(__file__)

import os, sys, time, xmlrpclib

from MoinMoin import log
logging = log.getLogger(__name__)

from MoinMoin import config, user, wikiutil
from MoinMoin.Page import Page
from MoinMoin.PageEditor import PageEditor
from MoinMoin.logfile import editlog
from MoinMoin.action import AttachFile
from MoinMoin import caching
from MoinMoin import session


class XmlRpcAuthTokenIDHandler(session.SessionIDHandler):
    def __init__(self, token=None):
        session.SessionIDHandler.__init__(self)
        self.token = token

    def get(self, request):
        return self.token

    def set(self, request, session_id, expires):
        self.token = session_id


logging_tearline = '- XMLRPC %s ' + '-' * 40

class XmlRpcBase:
    """ XMLRPC base class with common functionality of wiki xmlrpc v1 and v2 """
    def __init__(self, request):
        """
        Initialize an XmlRpcBase object.
        @param request: the request object
        """
        self.request = request
        self.version = None # this has to be defined in derived class
        self.cfg = request.cfg

    #############################################################################
    ### Helper functions
    #############################################################################

    def _instr(self, text):
        """ Convert inbound string.

        @param text: the text to convert (encoded str or unicode)
        @rtype: unicode
        @return: text as unicode
        """
        raise NotImplementedError("please implement _instr in derived class")

    def _outstr(self, text):
        """ Convert outbound string.

        @param text: the text to convert (encoded str or unicode)
        @rtype: str
        @return: text as encoded str
        """
        raise NotImplementedError("please implement _outstr in derived class")

    def _inlob(self, text):
        """ Convert inbound base64-encoded utf-8 to Large OBject.

        @param text: the text to convert
        @rtype: unicode
        @return: text
        """
        text = text.data #this is a already base64-decoded 8bit string
        text = unicode(text, 'utf-8')
        return text

    def _outlob(self, text):
        """ Convert outbound Large OBject to base64-encoded utf-8.

        @param text: the text, either unicode or utf-8 string
        @rtype: str
        @return: xmlrpc Binary object
        """
        if isinstance(text, unicode):
            text = text.encode('utf-8')
        else:
            if config.charset != 'utf-8':
                text = unicode(text, config.charset).encode('utf-8')
        return xmlrpclib.Binary(text)

    def _dump_exc(self):
        """ Convert an exception to a string.

        @rtype: str
        @return: traceback as string
        """
        import traceback

        return "%s: %s\n%s" % (
            sys.exc_info()[0],
            sys.exc_info()[1],
            '\n'.join(traceback.format_tb(sys.exc_info()[2])),
        )

    def process(self):
        """ xmlrpc v1 and v2 dispatcher """
        try:
            if 'xmlrpc' in self.request.cfg.actions_excluded:
                # we do not handle xmlrpc v1 and v2 differently
                response = xmlrpclib.Fault(1, "This moin wiki does not allow xmlrpc method calls.")
            else:
                # overwrite any user there might be, if you need a valid user for
                # xmlrpc, you have to use multicall and getAuthToken / applyAuthToken
                self.request.user = user.User(self.request, auth_method='xmlrpc:invalid')

                data = self.request.read(self.request.content_length)

                try:
                    params, method = xmlrpclib.loads(data)
                except:
                    # if anything goes wrong here, we want to see the raw data:
                    logging.debug("Length of raw data: %d bytes" % len(data))
                    logging.debug(logging_tearline % 'request raw data begin')
                    logging.debug('%r' % data)
                    logging.debug(logging_tearline % 'request raw data end')
                    raise

                logging.debug(logging_tearline % 'request parsed data begin')
                logging.debug('%s(%r)' % (method, params))
                logging.debug(logging_tearline % 'request parsed data end')

                response = self.dispatch(method, params)
        except:
            logging.exception("An exception occurred (this is also sent as fault response to the client):")
            # report exception back to client
            response = xmlrpclib.dumps(xmlrpclib.Fault(1, self._dump_exc()))
        else:
            logging.debug(logging_tearline % 'response begin')
            logging.debug(response)
            logging.debug(logging_tearline % 'response end')

            if isinstance(response, xmlrpclib.Fault):
                response = xmlrpclib.dumps(response)
            else:
                # wrap response in a singleton tuple
                response = (response, )
                # serialize it
                response = xmlrpclib.dumps(response, methodresponse=1, allow_none=True)

        self.request.emit_http_headers([
            "Content-Type: text/xml; charset=utf-8",
            "Content-Length: %d" % len(response),
        ])
        self.request.write(response)

    def dispatch(self, method, params):
        """ call dispatcher - for method==xxx it either locates a method called
            xmlrpc_xxx or loads a plugin from plugin/xmlrpc/xxx.py
        """
        method = method.replace(".", "_")

        try:
            fn = getattr(self, 'xmlrpc_' + method)
        except AttributeError:
            try:
                fn = wikiutil.importPlugin(self.request.cfg, 'xmlrpc',
                                           method, 'execute')
            except wikiutil.PluginMissingError:
                response = xmlrpclib.Fault(1, "No such method: %s." %
                                           method)
            else:
                response = fn(self, *params)
        else:
            response = fn(*params)

        return response

    # Common faults -----------------------------------------------------

    def notAllowedFault(self):
        return xmlrpclib.Fault(1, "You are not allowed to read this page.")

    def noSuchPageFault(self):
        return xmlrpclib.Fault(1, "No such page was found.")

    def noLogEntryFault(self):
        return xmlrpclib.Fault(1, "No log entry was found.")

    #############################################################################
    ### System methods
    #############################################################################

    def xmlrpc_system_multicall(self, call_list):
        """system.multicall([{'methodName': 'add', 'params': [2, 2]}, ...]) => [[4], ...]

        Allows the caller to package multiple XML-RPC calls into a single
        request.

        See http://www.xmlrpc.com/discuss/msgReader$1208

        Copied from SimpleXMLRPCServer.py
        """

        results = []
        for call in call_list:
            method_name = call['methodName']
            params = call['params']

            try:
                # XXX A marshalling error in any response will fail the entire
                # multicall. If someone cares they should fix this.
                result = self.dispatch(method_name, params)

                if not isinstance(result, xmlrpclib.Fault):
                    results.append([result])
                else:
                    results.append(
                        {'faultCode': result.faultCode,
                         'faultString': result.faultString}
                        )
            except:
                results.append(
                    {'faultCode': 1,
                     'faultString': "%s:%s" % (sys.exc_type, sys.exc_value)}
                    )

        return results

    #############################################################################
    ### Interface implementation
    #############################################################################

    def xmlrpc_getRPCVersionSupported(self):
        """ Returns version of the Wiki API.

        @rtype: int
        @return: 1 or 2 (wikirpc version)
        """
        return self.version

    def xmlrpc_getAllPages(self):
        """ Get all pages readable by current user

        @rtype: list
        @return: a list of all pages.
        """

        # the official WikiRPC interface is implemented by the extended method
        # as well
        return self.xmlrpc_getAllPagesEx()


    def xmlrpc_getAllPagesEx(self, opts=None):
        """ Get all pages readable by current user. Not an WikiRPC method.

        @param opts: dictionary that can contain the following arguments:
                include_system:: set it to false if you do not want to see system pages
                include_revno:: set it to True if you want to have lists with [pagename, revno]
                include_deleted:: set it to True if you want to include deleted pages
                exclude_non_writable:: do not include pages that the current user may not write to
                include_underlay:: return underlay pagenames as well
                prefix:: the page name must begin with this prefix to be included
                mark_deleted:: returns the revision number -rev_no if the page was deleted.
                    Makes only sense if you enable include_revno and include_deleted.
        @rtype: list
        @return: a list of all pages.
        """
        from MoinMoin.wikisync import normalise_pagename
        options = {"include_system": True, "include_revno": False, "include_deleted": False,
                   "exclude_non_writable": False, "include_underlay": True, "prefix": "",
                   "pagelist": None, "mark_deleted": False}
        if opts is not None:
            options.update(opts)

        if not options["include_system"]:
            p_filter = lambda name: not wikiutil.isSystemPage(self.request, name)
        else:
            p_filter = lambda name: True

        if options["exclude_non_writable"]:
            p_filter = lambda name, p_filter=p_filter: p_filter(name) and self.request.user.may.write(name)

        if options["prefix"] or options["pagelist"]:
            def p_filter(name, p_filter=p_filter, prefix=(options["prefix"] or ""), pagelist=options["pagelist"]):
                if not p_filter(name):
                    return False
                n_name = normalise_pagename(name, prefix)
                if not n_name:
                    return False
                if not pagelist:
                    return True
                return n_name in pagelist

        pagelist = self.request.rootpage.getPageList(filter=p_filter, exists=not options["include_deleted"],
                                                     include_underlay=options["include_underlay"],
                                                     return_objects=options["include_revno"])

        if options['include_revno']:
            pages = []
            for page in pagelist:
                revno = page.get_real_rev()
                if options["mark_deleted"] and not page.exists():
                    revno = -revno
                pages.append([self._outstr(page.page_name), revno])
            return pages
        else:
            return [self._outstr(page) for page in pagelist]

    def xmlrpc_getRecentChanges(self, date):
        """ Get RecentChanges since date

        @param date: date since when rc will be listed
        @rtype: list
        @return: a list of changed pages since date, which should be in
            UTC. The result is a list, where each element is a struct:
            * name (string) :
                Name of the page. The name is in UTF-8.
            * lastModified (date) :
                Date of last modification, in UTC.
            * author (string) :
                Name of the author (if available). UTF-8.
            * version (int) :
                Current version.
        """

        return_items = []

        edit_log = editlog.EditLog(self.request)
        for log in edit_log.reverse():
            # get last-modified UTC (DateTime) from log
            gmtuple = tuple(time.gmtime(wikiutil.version2timestamp(log.ed_time_usecs)))
            lastModified_date = xmlrpclib.DateTime(gmtuple)

            # skip if older than "date"
            if lastModified_date < date:
                break

            # skip if knowledge not permitted
            if not self.request.user.may.read(log.pagename):
                continue

            # get page name (str) from log
            pagename_str = self._outstr(log.pagename)

            # get user name (str) from log
            author_str = log.hostname
            if log.userid:
                userdata = user.User(self.request, log.userid)
                if userdata.name:
                    author_str = userdata.name
            author_str = self._outstr(author_str)

            return_item = {'name': pagename_str,
                           'lastModified': lastModified_date,
                           'author': author_str,
                           'version': int(log.rev) }
            return_items.append(return_item)

        return return_items

    def xmlrpc_getPageInfo(self, pagename):
        """ Invoke xmlrpc_getPageInfoVersion with rev=None """
        return self.xmlrpc_getPageInfoVersion(pagename, rev=None)

    def xmlrpc_getPageInfoVersion(self, pagename, rev):
        """ Return page information for specific revision

        @param pagename: the name of the page (utf-8)
        @param rev: revision to get info about (int)
        @rtype: dict
        @return: page information
            * name (string): the canonical page name, UTF-8.
            * lastModified (date): Last modification date, UTC.
            * author (string): author name, UTF-8.
            * version (int): current version

        """
        pn = self._instr(pagename)

        # User may read this page?
        if not self.request.user.may.read(pn):
            return self.notAllowedFault()

        if rev is not None:
            page = Page(self.request, pn, rev=rev)
        else:
            page = Page(self.request, pn)
            rev = page.current_rev()

        # Non existing page?
        if not page.exists():
            return self.noSuchPageFault()

        # Get page info
        edit_info = page.edit_info()
        if not edit_info:
            return self.noLogEntryFault()

        mtime = wikiutil.version2timestamp(long(edit_info['timestamp'])) # must be long for py 2.2.x
        gmtuple = tuple(time.gmtime(mtime))

        version = rev # our new rev numbers: 1,2,3,4,....

        #######################################################################
        # BACKWARDS COMPATIBILITY CODE - remove when 1.2.x is regarded stone age
        # as we run a feed for BadContent on MoinMaster, we want to stay
        # compatible here for a while with 1.2.x moins asking us for BadContent
        # 1.3 uses the lastModified field for checking for updates, so it
        # should be no problem putting the old UNIX timestamp style of version
        # number in the version field
        if self.request.cfg.sitename == 'MoinMaster' and pagename == 'BadContent':
            version = int(mtime)
        #######################################################################

        return {
            'name': self._outstr(page.page_name),
            'lastModified': xmlrpclib.DateTime(gmtuple),
            'author': self._outstr(edit_info['editor']),
            'version': version,
            }

    def xmlrpc_getPage(self, pagename):
        """ Invoke xmlrpc_getPageVersion with rev=None """
        return self.xmlrpc_getPageVersion(pagename, rev=None)

    def xmlrpc_getPageVersion(self, pagename, rev):
        """ Get raw text from specific revision of pagename

        @param pagename: pagename (utf-8)
        @param rev: revision number (int)
        @rtype: str
        @return: utf-8 encoded page data
        """
        pagename = self._instr(pagename)

        # User may read page?
        if not self.request.user.may.read(pagename):
            return self.notAllowedFault()

        if rev is not None:
            page = Page(self.request, pagename, rev=rev)
        else:
            page = Page(self.request, pagename)

        # Non existing page?
        if not page.exists():
            return self.noSuchPageFault()

        # Return page raw text
        if self.version == 2:
            return self._outstr(page.get_raw_body())
        elif self.version == 1:
            return self._outlob(page.get_raw_body())

    def xmlrpc_getPageHTML(self, pagename):
        """ Invoke xmlrpc_getPageHTMLVersion with rev=None """
        return self.xmlrpc_getPageHTMLVersion(pagename, rev=None)

    def xmlrpc_getPageHTMLVersion(self, pagename, rev):
        """ Get HTML of from specific revision of pagename

        @param pagename: the page name (utf-8)
        @param rev: revision number (int)
        @rtype: str
        @return: page in rendered HTML (utf-8)
        """
        pagename = self._instr(pagename)

        # User may read page?
        if not self.request.user.may.read(pagename):
            return self.notAllowedFault()

        if rev is not None:
            page = Page(self.request, pagename, rev=rev)
        else:
            page = Page(self.request, pagename)

        # Non existing page?
        if not page.exists():
            return self.noSuchPageFault()

        # Render page into a buffer
        result = self.request.redirectedOutput(page.send_page, content_only=1)

        # Return rendered page
        if self.version == 2:
            return self._outstr(result)
        elif self.version == 1:
            return xmlrpclib.Binary(result)

    def xmlrpc_listLinks(self, pagename):
        """
        list links for a given page
        @param pagename: the page name
        @rtype: list
        @return: links of the page, structs, with the following elements
            * name (string) : The page name or URL the link is to, UTF-8 encoding.
            * type (int) : The link type. Zero (0) for internal Wiki
              link, one (1) for external link (URL - image link, whatever).
        """
        pagename = self._instr(pagename)

        # User may read page?
        if not self.request.user.may.read(pagename):
            return self.notAllowedFault()

        page = Page(self.request, pagename)

        # Non existing page?
        if not page.exists():
            return self.noSuchPageFault()

        links_out = []
        for link in page.getPageLinks(self.request):
            links_out.append({'name': self._outstr(link), 'type': 0 })
        return links_out

    def xmlrpc_putPage(self, pagename, pagetext):
        """
        save a page / change a page to a new text
        @param pagename: the page name (unicode or utf-8)
        @param pagetext: the new page text (content, unicode or utf-8)
        @rtype: bool
        @return: true on success
        """

        pagename = self._instr(pagename)

        if not pagename:
            return xmlrpclib.Fault("INVALID", "pagename can't be empty")

        # check ACLs
        if not self.request.user.may.write(pagename):
            return xmlrpclib.Fault(1, "You are not allowed to edit this page")

        page = PageEditor(self.request, pagename)
        try:
            if self.version == 2:
                newtext = self._instr(pagetext)
            elif self.version == 1:
                newtext = self._inlob(pagetext)
            msg = page.saveText(newtext, 0)
        except page.SaveError, msg:
            logging.error("SaveError: %s" % msg)
            return xmlrpclib.Fault(1, "%s" % msg)

        # Update pagelinks cache
        page.getPageLinks(self.request)

        return xmlrpclib.Boolean(1)

    def xmlrpc_revertPage(self, pagename, revision):
        """Revert a page to previous revision

        This is mainly intended to be used by the jabber bot.

        @param pagename: the page name (unicode or utf-8)
        @param revision: revision to revert to
        @rtype bool
        @return true on success

        """

        pagename = self._instr(pagename)

        if not self.request.user.may.write(pagename):
            return xmlrpclib.Fault(1, "You are not allowed to edit this page")

        rev = int(self._instr(revision))
        editor = PageEditor(self.request, pagename)

        try:
            editor.revertPage(rev)
        except PageEditor.SaveError, error:
            return xmlrpclib.Fault(1, "Revert failed: %s" % (str(error), ))

        return xmlrpclib.Boolean(1)

    def xmlrpc_searchPages(self, query_string):
        """ Searches pages for query_string.
            Returns a list of tuples (foundpagename, context)
        """
        from MoinMoin import search
        results = search.searchPages(self.request, query_string)
        results.formatter = self.request.html_formatter
        results.request = self.request
        return [(self._outstr(hit.page_name),
                 self._outstr(results.formatContext(hit, 180, 1)))
                for hit in results.hits]

    def xmlrpc_searchPagesEx(self, query_string, search_type, length, case, mtime, regexp):
        """ Searches pages for query_string - extended version for compatibility

        This function, in contrary to searchPages(), doesn't return HTML-formatted data.

        @param query_string: term to search for
        @param search_type: "text" or "title" search
        @param length: length of context preview (in characters)
        @param case: should the search be case sensitive?
        @param mtime: only output pages modified after mtime
        @param regexp: should the query_string be treates as a regular expression?
        @return: (page name, context preview, page url)

        """
        from MoinMoin import search
        from MoinMoin.formatter.text_plain import Formatter

        kwargs = {"sort": "page_name", "case": case, "regex": regexp}
        if search_type == "title":
            kwargs["titlesearch"] = True

        results = search.searchPages(self.request, query_string, **kwargs)
        results.formatter = Formatter(self.request)
        results.request = self.request

        return [(self._outstr(hit.page_name),
                 self._outstr(results.formatContext(hit, length, 1)),
                 self.request.getQualifiedURL(hit.page.url(self.request, {})))
                for hit in results.hits]

    def xmlrpc_getMoinVersion(self):
        """ Returns a tuple of the MoinMoin version:
            (project, release, revision)
        """
        from MoinMoin import version
        return (version.project, version.release, version.revision)


    # user profile data transfer

    def xmlrpc_getUserProfile(self):
        """ Return the user profile data for the current user.
            Use this in a single multicall after applyAuthToken.
            If we have a valid user, returns a dict of items from user profile.
            Otherwise, return an empty dict.
        """
        u = self.request.user
        if not u.valid:
            userdata = {}
        else:
            userdata = dict(u.persistent_items())
        return userdata

    def xmlrpc_getUserLanguageByJID(self, jid):
        """ Returns user's language given his/her Jabber ID

        It makes no sense to consider this a secret, right? Therefore
        an authentication token is not required. We return a default
        of "en" if user is not found.

        TODO: surge protection? Do we fear account enumeration?
        """
        retval = "en"
        u = user.get_by_jabber_id(self.request, jid)
        if u:
            retval = u.language

        return retval

    # authorization methods

    def xmlrpc_getAuthToken(self, username, password, *args):
        """ Returns a token which can be used for authentication
            in other XMLRPC calls. If the token is empty, the username
            or the password were wrong.
        """
        id_handler = XmlRpcAuthTokenIDHandler()

        u = self.request.cfg.session_handler.start(self.request, id_handler)
        u = self.request.handle_auth(u, username=username,
                                     password=password, login=True)

        self.request.cfg.session_handler.after_auth(self.request, id_handler, u)

        if u and u.valid:
            return id_handler.token
        else:
            return ""

    def xmlrpc_getJabberAuthToken(self, jid, secret):
        """Returns a token which can be used for authentication.

        This token can be used in other XMLRPC calls. Generation of
        token depends on user's JID and a secret shared between wiki
        and Jabber bot.

        @param jid: a bare Jabber ID
        """
        if self.cfg.secrets['jabberbot'] != secret:
            return ""

        u = self.request.handle_jid_auth(jid)

        if u and u.valid:
            return self._generate_auth_token(u)
        else:
            return ""

    def xmlrpc_applyAuthToken(self, auth_token):
        """ Applies the auth token and thereby authenticates the user. """
        if not auth_token:
            return xmlrpclib.Fault("INVALID", "Empty token.")

        id_handler = XmlRpcAuthTokenIDHandler(auth_token)

        u = self.request.cfg.session_handler.start(self.request, id_handler)
        u = self.request.handle_auth(u)
        self.request.cfg.session_handler.after_auth(self.request, id_handler, u)
        if u and u.valid:
            self.request.user = u
            return "SUCCESS"
        else:
            return xmlrpclib.Fault("INVALID", "Invalid token.")


    def xmlrpc_deleteAuthToken(self, auth_token):
        """ Delete the given auth token. """
        id_handler = XmlRpcAuthTokenIDHandler(auth_token)

        u = self.request.cfg.session_handler.start(self.request, id_handler)
        u = self.request.handle_auth(u)
        self.request.cfg.session_handler.after_auth(self.request, id_handler, u)

        self.request.session.delete()

        return "SUCCESS"


    # methods for wiki synchronization

    def xmlrpc_getDiff(self, pagename, from_rev, to_rev, n_name=None):
        """ Gets the binary difference between two page revisions.

            @param pagename: unicode string qualifying the page name

            @param fromRev: integer specifying the source revision. May be None to
            refer to a virtual empty revision which leads to a diff
            containing the whole page.

            @param toRev: integer specifying the target revision. May be None to
            refer to the current revision. If the current revision is the same
            as fromRev, there will be a special error condition "ALREADY_CURRENT"

            @param n_name: do a tag check verifying that n_name was the normalised
            name of the last tag

            If both fromRev and toRev are None, this function acts similar to getPage, i.e. it will diff("",currentRev).

            @return Returns a dict:
            * status (not a field, implicit, returned as Fault if not SUCCESS):
             * "SUCCESS" - if the diff could be retrieved successfully
             * "NOT_EXIST" - item does not exist
             * "FROMREV_INVALID" - the source revision is invalid
             * "TOREV_INVALID" - the target revision is invalid
             * "INTERNAL_ERROR" - there was an internal error
             * "INVALID_TAG" - the last tag does not match the supplied normalised name
             * "ALREADY_CURRENT" - this not merely an error condition. It rather means that
             there is no new revision to diff against which is a good thing while
             synchronisation.
            * current: the revision number of the current revision (not the one which was diff'ed against)
            * diff: Binary object that transports a zlib-compressed binary diff (see bdiff.py, taken from Mercurial)
            * conflict: if there is a conflict on the page currently

        """
        from MoinMoin.util.bdiff import textdiff, compress
        from MoinMoin.wikisync import TagStore

        pagename = self._instr(pagename)
        if n_name is not None:
            n_name = self._instr(n_name)

        # User may read page?
        if not self.request.user.may.read(pagename):
            return self.notAllowedFault()

        def allowed_rev_type(data):
            if data is None:
                return True
            return isinstance(data, int) and data > 0

        if not allowed_rev_type(from_rev):
            return xmlrpclib.Fault("FROMREV_INVALID", "Incorrect type for from_rev.")

        if not allowed_rev_type(to_rev):
            return xmlrpclib.Fault("TOREV_INVALID", "Incorrect type for to_rev.")

        currentpage = Page(self.request, pagename)
        if not currentpage.exists():
            return xmlrpclib.Fault("NOT_EXIST", "Page does not exist.")

        revisions = currentpage.getRevList()

        if from_rev is not None and from_rev not in revisions:
            return xmlrpclib.Fault("FROMREV_INVALID", "Unknown from_rev.")
        if to_rev is not None and to_rev not in revisions:
            return xmlrpclib.Fault("TOREV_INVALID", "Unknown to_rev.")

        # use lambda to defer execution in the next lines
        if from_rev is None:
            oldcontents = lambda: ""
        else:
            oldpage = Page(self.request, pagename, rev=from_rev)
            oldcontents = lambda: oldpage.get_raw_body_str()

        if to_rev is None:
            newpage = currentpage
            newcontents = lambda: currentpage.get_raw_body_str()
        else:
            newpage = Page(self.request, pagename, rev=to_rev)
            newcontents = lambda: newpage.get_raw_body_str()

        if oldcontents() and oldpage.get_real_rev() == newpage.get_real_rev():
            return xmlrpclib.Fault("ALREADY_CURRENT", "There are no changes.")

        if n_name is not None:
            tags = TagStore(newpage)
            last_tag = tags.get_last_tag()
            if last_tag is not None and last_tag.normalised_name != n_name:
                return xmlrpclib.Fault("INVALID_TAG", "The used tag is incorrect because the normalised name does not match.")

        newcontents = newcontents()
        conflict = wikiutil.containsConflictMarker(newcontents)
        diffblob = xmlrpclib.Binary(compress(textdiff(oldcontents(), newcontents)))

        return {"conflict": conflict, "diff": diffblob, "diffversion": 1, "current": currentpage.get_real_rev()}

    def xmlrpc_interwikiName(self):
        """ Returns the interwiki name and the IWID of the current wiki. """
        name = self.request.cfg.interwikiname
        iwid = self.request.cfg.iwid
        if name is None:
            return [None, iwid]
        else:
            return [self._outstr(name), iwid]

    def xmlrpc_mergeDiff(self, pagename, diff, local_rev, delta_remote_rev, last_remote_rev, interwiki_name, normalised_name):
        """ Merges a diff sent by the remote machine and returns the number of the new revision.
            Additionally, this method tags the new revision.

            @param pagename: The pagename that is currently dealt with.
            @param diff: The diff that can be applied to the version specified by delta_remote_rev.
                If it is None, the page is deleted.
            @param local_rev: The revno of the page on the other wiki system, used for the tag.
            @param delta_remote_rev: The revno that the diff is taken against.
            @param last_remote_rev: The last revno of the page `pagename` that is known by the other wiki site.
            @param interwiki_name: Used to build the interwiki tag.
            @param normalised_name: The normalised pagename that is common to both wikis.

            @return Returns the current revision number after the merge was done. Or one of the following errors:
                * "SUCCESS" - the page could be merged and tagged successfully.
                * "NOT_EXIST" - item does not exist and there was not any content supplied.
                * "LASTREV_INVALID" - the page was changed and the revision got invalid
                * "INTERNAL_ERROR" - there was an internal error
                * "NOT_ALLOWED" - you are not allowed to do the merge operation on the page
        """
        from MoinMoin.util.bdiff import decompress, patch
        from MoinMoin.wikisync import TagStore, BOTH
        from MoinMoin.packages import unpackLine
        LASTREV_INVALID = xmlrpclib.Fault("LASTREV_INVALID", "The page was changed")

        pagename = self._instr(pagename)

        comment = u"Remote Merge - %r" % unpackLine(interwiki_name)[-1]

        # User may read page?
        if not self.request.user.may.read(pagename) or not self.request.user.may.write(pagename):
            return xmlrpclib.Fault("NOT_ALLOWED", "You are not allowed to write to this page.")

        # XXX add locking here!

        # current version of the page
        currentpage = PageEditor(self.request, pagename, do_editor_backup=0)

        if last_remote_rev is not None and currentpage.get_real_rev() != last_remote_rev:
            return LASTREV_INVALID

        if not currentpage.exists() and diff is None:
            return xmlrpclib.Fault("NOT_EXIST", "The page does not exist and no diff was supplied.")

        if diff is None: # delete the page
            try:
                currentpage.deletePage(comment)
            except PageEditor.AccessDenied, (msg, ):
                return xmlrpclib.Fault("NOT_ALLOWED", msg)
            return currentpage.get_real_rev()

        # base revision used for the diff
        basepage = Page(self.request, pagename, rev=(delta_remote_rev or 0))

        # generate the new page revision by applying the diff
        newcontents = patch(basepage.get_raw_body_str(), decompress(str(diff)))
        #print "Diff against %r" % basepage.get_raw_body_str()

        # write page
        try:
            currentpage.saveText(newcontents.decode("utf-8"), last_remote_rev or 0, comment=comment)
        except PageEditor.Unchanged: # could happen in case of both wiki's pages being equal
            pass
        except PageEditor.EditConflict:
            return LASTREV_INVALID

        current_rev = currentpage.get_real_rev()

        tags = TagStore(currentpage)
        tags.add(remote_wiki=interwiki_name, remote_rev=local_rev, current_rev=current_rev, direction=BOTH, normalised_name=normalised_name)

        # XXX unlock page

        return current_rev


    # XXX BEGIN WARNING XXX
    # All xmlrpc_*Attachment* functions have to be considered as UNSTABLE API -
    # they are neither standard nor are they what we need when we have switched
    # attachments (1.5 style) to mimetype items (hopefully in 1.6).
    # They will be partly removed, esp. the semantics of the function "listAttachments"
    # cannot be sensibly defined for items.
    # If the first beta or more stable release of 1.6 will have new item semantics,
    # we will remove the functions before it is released.
    def xmlrpc_listAttachments(self, pagename):
        """ Get all attachments associated with pagename
        Deprecated.

        @param pagename: pagename (utf-8)
        @rtype: list
        @return: a list of utf-8 attachment names
        """
        pagename = self._instr(pagename)
        # User may read page?
        if not self.request.user.may.read(pagename):
            return self.notAllowedFault()

        result = AttachFile._get_files(self.request, pagename)
        return result

    def xmlrpc_getAttachment(self, pagename, attachname):
        """ Get attachname associated with pagename

        @param pagename: pagename (utf-8)
        @param attachname: attachment name (utf-8)
        @rtype base64
        @return base64 data
        """
        pagename = self._instr(pagename)
        # User may read page?
        if not self.request.user.may.read(pagename):
            return self.notAllowedFault()

        attachname = wikiutil.taintfilename(self._instr(attachname))
        filename = AttachFile.getFilename(self.request, pagename, attachname)
        if not os.path.isfile(filename):
            return self.noSuchPageFault()
        return self._outlob(open(filename, 'rb').read())

    def xmlrpc_putAttachment(self, pagename, attachname, data):
        """ Set attachname associated with pagename to data

        @param pagename: pagename (utf-8)
        @param attachname: attachment name (utf-8)
        @param data: file data (base64)
        @rtype boolean
        @return True if attachment was set
        """
        pagename = self._instr(pagename)
        # User may read page?
        if not self.request.user.may.read(pagename):
            return self.notAllowedFault()

        # also check ACLs
        if not self.request.user.may.write(pagename):
            return xmlrpclib.Fault(1, "You are not allowed to edit this page")

        attachname = wikiutil.taintfilename(self._instr(attachname))
        filename = AttachFile.getFilename(self.request, pagename, attachname)
        if os.path.exists(filename) and not os.path.isfile(filename):
            return self.noSuchPageFault()
        open(filename, 'wb+').write(data.data)
        AttachFile._addLogEntry(self.request, 'ATTNEW', pagename, attachname)
        return xmlrpclib.Boolean(1)

    # XXX END WARNING XXX


    def xmlrpc_getBotTranslations(self):
        """ Return translations to be used by notification bot

        @return: a dict (indexed by language) of dicts of translated strings (indexed by original ones)
        """
        from MoinMoin.i18n import bot_translations
        return bot_translations(self.request)


class XmlRpc1(XmlRpcBase):

    def __init__(self, request):
        XmlRpcBase.__init__(self, request)
        self.version = 1

    def _instr(self, text):
        """ Convert string we get from xmlrpc into internal representation

        @param text: quoted text (str or unicode object)
        @rtype: unicode
        @return: text
        """
        return wikiutil.url_unquote(text) # config.charset must be utf-8

    def _outstr(self, text):
        """ Convert string from internal representation to xmlrpc

        @param text: unicode or string in config.charset
        @rtype: str
        @return: text encoded in utf-8 and quoted
        """
        return wikiutil.url_quote(text) # config.charset must be utf-8


class XmlRpc2(XmlRpcBase):

    def __init__(self, request):
        XmlRpcBase.__init__(self, request)
        self.version = 2

    def _instr(self, text):
        """ Convert string we get from xmlrpc into internal representation

        @param text: unicode or utf-8 string
        @rtype: unicode
        @return: text
        """
        if not isinstance(text, unicode):
            text = unicode(text, 'utf-8')
        return text

    def _outstr(self, text):
        """ Convert string from internal representation to xmlrpc

        @param text: unicode or string in config.charset
        @rtype: str
        @return: text encoded in utf-8
        """
        if isinstance(text, unicode):
            text = text.encode('utf-8')
        elif config.charset != 'utf-8':
            text = unicode(text, config.charset).encode('utf-8')
        return text


def xmlrpc(request):
    XmlRpc1(request).process()


def xmlrpc2(request):
    XmlRpc2(request).process()

