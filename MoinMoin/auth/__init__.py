# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - modular authentication handling

    Each authentication method is an object instance containing
    three methods:
      * login(request, user_obj, **kw)
      * logout(request, user_obj, **kw)
      * request(request, user_obj, **kw)
    
    The kw arguments that are passed in are currently:
       username: the value of the 'username' form field (or None)
                 [login only]
       password: the value of the 'password' form field (or None)
                 [login only]
       multistage: boolean indicating multistage login continuation
                   [may not be present, login only]

    More may be added.

    The request method is called for each request except login/logout.

    The 'request' and 'logout' methods must return a tuple (user_obj, continue)
    where 'user_obj' can be
      * None, to throw away any previous user_obj from previous auth methods
      * the passed in user_obj for no changes
      * a newly created MoinMoin.user.User instance
    and 'continue' is a boolean to indicate whether the next authentication
    method should be tried.

    The 'login' method must return a tuple
        (user_obj, continue, multistage, message).

    The user_obj and continue values have the same semantics as for the request
    and logout methods.

    The messages that are returned by the various auth methods will be
    displayed to the user, since they will all be displayed usually auth
    methods will use the message feature only along with returning False for
    the continue flag.

    The multistage item in the tuple must evaluate to false or be callable.
    If it is callable, this indicates that the authentication method requires
    a second login stage. In that case, the multistage item will be called
    with the request as the only parameter. It should return an instance of
    MoinMoin.widget.html.FORM and the generic code will append some required
    hidden fields to it. It is also permissible to return some valid HTML,
    but that feature has very limited use since it breaks the authentication
    method chain.

    Note that because multistage login does not depend on anonymous session
    support, it is possible that users jump directly into the second stage
    by giving the appropriate parameters to the login action. Hence, auth
    methods should take care to recheck everything and not assume the user
    has gone through all previous stages.

    After the user has submitted the required form, execution of the auth
    login methods resumes with the auth item that requested the multistage
    login and its login method is called with the 'multistage' keyword
    parameter set to True.

    Each authentication method instance must also contain the members
     * login_inputs: a list of required inputs, currently supported are
                      - 'username': username entry field
                      - 'password': password entry field
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
    not be changed by the user in UserPreferences.
    You also have to give the keyword argument "auth_method" containing the
    name of the authentication method.

    @copyright: 2005-2006 Bastian Blank, Florian Festi,
                          MoinMoin:AlexanderSchremmer, Nick Phillips,
                          MoinMoin:FrankieChow, MoinMoin:NirSoffer,
                2005-2007 MoinMoin:ThomasWaldmann,
                2007      MoinMoin:JohannesBerg

    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import user

class BaseAuth:
    name = None
    login_inputs = []
    logout_possible = False
    def __init__(self):
        pass
    def login(self, request, user_obj, **kw):
        return user_obj, True, None, None
    def request(self, request, user_obj, **kw):
        return user_obj, True
    def logout(self, request, user_obj, **kw):
        if self.name and user_obj and user_obj.auth_method == self.name:
            user_obj.valid = False
        return user_obj, True

class MoinLogin(BaseAuth):
    """ handle login from moin login form """
    def __init__(self, verbose=False):
        BaseAuth.__init__(self)
        self.verbose = verbose

    login_inputs = ['username', 'password']
    name = 'moin_login'
    logout_possible = True

    def login(self, request, user_obj, **kw):
        username = kw.get('username')
        password = kw.get('password')

        if not username and not password:
            return user_obj, True, None, None

        _ = request.getText

        verbose = self.verbose

        if verbose: request.log("moin_login performing login action")

        if username and not password:
            return user_obj, True, None, _('Missing password. Please enter user name and password.')

        u = user.User(request, name=username, password=password, auth_method=self.name)
        if u.valid:
            if verbose: request.log("moin_login got valid user...")
            return u, True, None, None
        else:
            if verbose: request.log("moin_login not valid, previous valid=%d." % user_obj.valid)
            return user_obj, True, None, _("Invalid username or password.")
