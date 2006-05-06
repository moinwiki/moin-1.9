# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - login action

    The real login is done in MoinMoin.request.
    Here is only some user notification in case something went wrong.

    @copyright: 2005-2006 by Radomirs Cirskis <nad2000@gmail.com>
    @copyright: 2006 by Thomas Waldmann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import user, wikiutil, userform
from MoinMoin.Page import Page

def execute(pagename, request):
    return LoginHandler(pagename, request).handle()

class LoginHandler:
    def __init__(self, pagename, request):
        self.request = request
        self._ = request.getText
        self.cfg = request.cfg
        self.pagename = pagename
        self.page = Page(request, pagename)

    def handle(self):
        _ = self._
        request = self.request
        form = request.form

        error = None

        islogin = form.get('login', [''])[0]

        if islogin: # user pressed login button
            # Trying to login with a user name and a password
            # Require valid user name
            name = form.get('name', [''])[0]
            if not user.isValidName(request, name):
                 error = _("""Invalid user name {{{'%s'}}}.
Name may contain any Unicode alpha numeric character, with optional one
space between words. Group page name is not allowed.""") % name

            # Check that user exists
            elif not user.getUserId(request, name):
                error = _('Unknown user name: {{{"%s"}}}. Please enter'
                             ' user name and password.') % name

            # Require password
            else:
                password = form.get('password',[None])[0]
                if not password:
                    error = _("Missing password. Please enter user name and"
                             " password.")
                else:
                    if not request.user.valid:
                        error = _("Sorry, wrong password.")

            return self.page.send_page(request, msg=error)
        
        else: # show login form
            request.http_headers()
            wikiutil.send_title(request, _("Login"), pagename=self.pagename)
            # Start content (important for RTL support)
            request.write(request.formatter.startContent("content"))
            
            request.write(userform.getLogin(request))
            
            # End content and send footer
            request.write(request.formatter.endContent())
            wikiutil.send_footer(request, self.pagename)

