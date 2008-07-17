# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - modular authentication handling

    Each authentication method is an object instance containing
    four methods:
      * login(request, user_obj, **kw)
      * logout(request, user_obj, **kw)
      * request(request, user_obj, **kw)
      * login_hint(request)

    The kw arguments that are passed in are currently:
       attended: boolean indicating whether a user (attended=True) or
                 a machine is requesting login, multistage auth is not
                 currently possible for machine logins [login only]
       username: the value of the 'username' form field (or None)
                 [login only]
       password: the value of the 'password' form field (or None)
                 [login only]
       cookie: a Cookie.SimpleCookie instance containing the cookie
               that the browser sent
       multistage: boolean indicating multistage login continuation
                   [may not be present, login only]
       openid_identifier: the OpenID identifier we got from the form
                          (or None) [login only]

    login_hint() should return a HTML text that is displayed to the user right
    below the login form, it should tell the user what to do in case of a
    forgotten password and how to create an account (if applicable.)

    More may be added.

    The request method is called for each request except login/logout.

    The 'request' and 'logout' methods must return a tuple (user_obj, continue)
    where 'user_obj' can be
      * None, to throw away any previous user_obj from previous auth methods
      * the passed in user_obj for no changes
      * a newly created MoinMoin.user.User instance
    and 'continue' is a boolean to indicate whether the next authentication
    method should be tried.

    The 'login' method must return an instance of MoinMoin.auth.LoginReturn
    which contains the members
      * user_obj
      * continue_flag
      * multistage
      * message
      * redirect_to

    There are some helpful subclasses derived from this class for the most
    common cases, namely ContinueLogin(), CancelLogin(), MultistageFormLogin()
    and MultistageRedirectLogin().

    The user_obj and continue_flag members have the same semantics as for the
    request and logout methods.

    The messages that are returned by the various auth methods will be
    displayed to the user, since they will all be displayed usually auth
    methods will use the message feature only along with returning False for
    the continue flag.

    Note, however, that when no username is entered or the username is not
    found in the database, it may be appropriate to return with a message
    and the continue flag set to true (ContinueLogin) because a subsequent auth
    plugin might work even without the username, say the openid plugin for
    example.

    The multistage member must evaluate to false or be callable. If it is
    callable, this indicates that the authentication method requires a second
    login stage. In that case, the multistage item will be called with the
    request as the only parameter. It should return an instance of
    MoinMoin.widget.html.FORM and the generic code will append some required
    hidden fields to it. It is also permissible to return some valid HTML,
    but that feature has very limited use since it breaks the authentication
    method chain.

    Note that because multistage login does not depend on anonymous session
    support, it is possible that users jump directly into the second stage
    by giving the appropriate parameters to the login action. Hence, auth
    methods should take care to recheck everything and not assume the user
    has gone through all previous stages.

    If the multistage login requires querying an external site that involves
    a redirect, the redirect_to member may be set instead of the multistage
    member. If this is set it must be a URL that user should be redirected to.
    Since the user must be able to come back to the authentication, any
    "%return" in the URL is replaced with the url-encoded form of the URL
    to the next authentication stage, any "%return_form" is replaced with
    the url-plus-encoded form (spaces encoded as +) of the same URL.

    After the user has submitted the required form or has been redirected back
    from the external site, execution of the auth login methods resumes with
    the auth item that requested the multistage login and its login method is
    called with the 'multistage' keyword parameter set to True.

    Each authentication method instance must also contain the members
     * login_inputs: a list of required inputs, currently supported are
                      - 'username': username entry field
                      - 'password': password entry field
                      - 'openid_identifier': OpenID entry field
                      - 'special_no_input': manual login is required
                            but no form fields need to be filled in
                            (for example openid with forced provider)
                            in this case the theme may provide a short-
                            cut omitting the login form
     * logout_possible: boolean indicating whether this auth methods
                        supports logging out
     * name: name of the auth method, must be the same as given as the
             user object's auth_method keyword parameter.

    To simplify creating new authentication methods you can inherit from
    MoinMoin.auth.BaseAuth that does nothing for all three methods, but
    allows you to override only some methods.

    cfg.auth is a list of authentication object instances whose methods
    are called in the order they are listed. The session method is called
    for every request, when logging in or out these are called before the
    session method.

    When creating a new MoinMoin.user.User object, you can give a keyword
    argument "auth_attribs" to User.__init__ containing a list of user
    attributes that are determined and fixed by this auth method and may
    not be changed by the user in their preferences.
    You also have to give the keyword argument "auth_method" containing the
    name of the authentication method.

    @copyright: 2005-2006 Bastian Blank, Florian Festi,
                          MoinMoin:AlexanderSchremmer, Nick Phillips,
                          MoinMoin:FrankieChow, MoinMoin:NirSoffer,
                2005-2008 MoinMoin:ThomasWaldmann,
                2007      MoinMoin:JohannesBerg

    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import log
logging = log.getLogger(__name__)

from MoinMoin import user, wikiutil


def get_multistage_continuation_url(request, auth_name, extra_fields={}):
    """get_continuation_url - return a multistage continuation URL

       This function returns a URL that when loaded continues a multistage
       authentication at the auth method requesting it (parameter auth_name.)
       Additional fields are added to the URL from the extra_fields dict.

       @param request: the Moin request
       @param auth_name: name of the auth method requesting the continuation
       @param extra_fields: extra GET fields to add to the URL
    """
    # logically, this belongs to request, but semantically it should
    # live in auth so people do auth.get_multistage_continuation_url()
    fields = {'action': 'login',
              'login': '1',
              'stage': auth_name}
    fields.update(extra_fields)
    if request.page:
        return request.page.url(request, querystr=fields)
    else:
        qstr = wikiutil.makeQueryString(fields)
        return ''.join([request.getBaseURL(), '?', qstr])


class LoginReturn(object):
    """ LoginReturn - base class for auth method login() return value"""
    def __init__(self, user_obj, continue_flag, message=None, multistage=None,
                 redirect_to=None):
        self.user_obj = user_obj
        self.continue_flag = continue_flag
        self.message = message
        self.multistage = multistage
        self.redirect_to = redirect_to

class ContinueLogin(LoginReturn):
    """ ContinueLogin - helper for auth method login that just continues """
    def __init__(self, user_obj, message=None):
        LoginReturn.__init__(self, user_obj, True, message=message)

class CancelLogin(LoginReturn):
    """ CancelLogin - cancel login showing a message """
    def __init__(self, message):
        LoginReturn.__init__(self, None, False, message=message)

class MultistageFormLogin(LoginReturn):
    """ MultistageFormLogin - require user to fill in another form """
    def __init__(self, multistage):
        LoginReturn.__init__(self, None, False, multistage=multistage)

class MultistageRedirectLogin(LoginReturn):
    """ MultistageRedirectLogin - redirect user to another site before continuing login """
    def __init__(self, url):
        LoginReturn.__init__(self, None, False, redirect_to=url)


class BaseAuth:
    name = None
    login_inputs = []
    logout_possible = False
    def __init__(self):
        pass
    def login(self, request, user_obj, **kw):
        return ContinueLogin(user_obj)
    def request(self, request, user_obj, **kw):
        return user_obj, True
    def logout(self, request, user_obj, **kw):
        if self.name and user_obj and user_obj.auth_method == self.name:
            logging.debug("%s: logout - invalidating user %r" % (self.name, user_obj.name))
            user_obj.valid = False
        return user_obj, True
    def login_hint(self, request):
        return None

class MoinAuth(BaseAuth):
    """ handle login from moin login form """
    def __init__(self):
        BaseAuth.__init__(self)

    login_inputs = ['username', 'password']
    name = 'moin'
    logout_possible = True

    def login(self, request, user_obj, **kw):
        username = kw.get('username')
        password = kw.get('password')

        # simply continue if something else already logged in successfully
        if user_obj and user_obj.valid:
            return ContinueLogin(user_obj)

        if not username and not password:
            return ContinueLogin(user_obj)

        _ = request.getText

        logging.debug("%s: performing login action" % self.name)

        if username and not password:
            return ContinueLogin(user_obj, _('Missing password. Please enter user name and password.'))

        u = user.User(request, name=username, password=password, auth_method=self.name)
        if u.valid:
            logging.debug("%s: successfully authenticated user %r (valid)" % (self.name, u.name))
            return ContinueLogin(u)
        else:
            logging.debug("%s: could not authenticate user %r (not valid)" % (self.name, username))
            return ContinueLogin(user_obj, _("Invalid username or password."))

    def login_hint(self, request):
        _ = request.getText
        userprefslink = request.page.url(request, querystr={'action': 'newaccount'})
        sendmypasswordlink = request.page.url(request, querystr={'action': 'recoverpass'})
        return _('If you do not have an account, <a href="%(userprefslink)s">you can create one now</a>. '
                 '<a href="%(sendmypasswordlink)s">Forgot your password?</a>') % {
               'userprefslink': userprefslink,
               'sendmypasswordlink': sendmypasswordlink}

