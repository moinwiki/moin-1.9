# -*- coding: iso-8859-1 -*-
# This is some sample code you might find useful when you want to use some
# external cookie (made by some other program, not moin) with moin.
# See the +++ places for customizing it to your needs. You need to put this
# code into your farmconfig.py or wikiconfig.py.

# HINT: this code is slightly outdated, if you fix it to work with 1.7, please send us a copy.
from MoinMoin.config.multiconfig import DefaultConfig
from MoinMoin.auth import BaseAuth

class ExternalCookie(BaseAuth):
    name = 'external_cookie'

    def request(self, request, user_obj, **kw):
        """ authenticate via external cookie """
        import Cookie
        user = None
        try_next = True # if True, moin tries the next auth method
        cookiename = "whatever" # +++ external cookie name you want to use

        try:
            cookie = Cookie.SimpleCookie(request.saved_cookie)
        except Cookie.CookieError:
            # ignore invalid cookies
            cookie = None
        if cookie and cookiename in cookie:
            import urllib
            cookievalue = cookie[cookiename].value
            # +++ now we decode and parse the cookie value - edit this to fit your needs.
            # the minimum we need to get is auth_username. aliasname and email is optional.
            cookievalue = urllib.unquote(cookievalue) # cookie value is urlencoded, decode it
            cookievalue = cookievalue.decode('iso-8859-1') # decode cookie charset to unicode
            cookievalue = cookievalue.split('#') # cookie has format loginname#firstname#lastname#email

            auth_username = cookievalue[0] # having this cookie means user auth has already been done!
            aliasname = email = ''
            try:
                aliasname = "%s %s" % (cookievalue[1], cookievalue[2]) # aliasname is for cosmetical stuff only
                email = cookievalue[3]
            except IndexError: # +++ this is for debugging it, in case it does not work
                if 0:
                    f = open("cookie.log", "w")
                    f.write(repr(cookie))
                    f.write(repr(cookievalue))
                    f.close()
                pass

            from MoinMoin.user import User
            # giving auth_username to User constructor means that authentication has already been done.
            user = User(request, name=auth_username, auth_username=auth_username, auth_method=self.name)

            changed = False
            if aliasname != user.aliasname: # was the aliasname externally updated?
                user.aliasname = aliasname
                changed = True # yes -> update user profile
            if email != user.email: # was the email addr externally updated?
                user.email = email
                changed = True # yes -> update user profile

            if user:
                user.create_or_update(changed)
            if user and user.valid: # did we succeed making up a valid user?
                try_next = False # stop processing auth method list
        return user, try_next

class FarmConfig(DefaultConfig):
    from MoinMoin.auth import MoinAuth
    # use ExternalCookie, also allow the usual moin login
    auth = [ExternalCookie(), MoinAuth()]

    # ... (rest of your config follows here) ...

