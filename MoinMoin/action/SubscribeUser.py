"""
   MoinMoin - Subscribeuser - Action
   Subscribe a user to a page

   @copyright: 2003 Daniela Nicklas <nicklas@informatik.uni-stuttgart.de>,
               2005 MoinMoin:AlexanderSchremmer
   @license: GNU GPL, see COPYING for details.
"""

import sys, os
#sys.path.append("YOUR CONFIG DIRECTORY HERE")

from MoinMoin.Page import Page
from MoinMoin import user
from MoinMoin import wikiutil

def show_form(pagename, request):
    _ = request.getText
    request.emit_http_headers()
    request.theme.send_title(_("Subscribe users to the page %s") % pagename, pagename=pagename)

    request.write("""
<form action="%s/%s" method="POST" enctype="multipart/form-data">
<input type="hidden" name="action" value="SubscribeUser">
%s <input type="text" name="users" size="50">
<input type="submit" value="Subscribe">
</form>
""" % (request.getScriptname(), wikiutil.quoteWikinameURL(pagename),
      _("Enter user names (comma separated):")))
    request.theme.send_footer(pagename)
    request.theme.send_closing_html()

def show_result(pagename, request):
    _ = request.getText
    request.emit_http_headers()

    request.theme.send_title(_("Subscribed for %s:") % pagename, pagename=pagename)

    from MoinMoin.formatter.text_html import Formatter
    formatter = Formatter(request)

    result = subscribe_users(request, request.form['users'][0].split(","), pagename, formatter)
    request.write(result)

    request.theme.send_footer(pagename)
    request.theme.send_closing_html()

def subscribe_users(request, usernamelist, pagename, formatter):
    _ = request.getText

    if not Page(request, pagename).exists():
        return u"Page does not exist."

    result = []

    realusers = []              # usernames that are really wiki users

    # get user object - only with IDs!
    for userid in user.getUserList(request):
        success = False
        userobj = user.User(request, userid)

        if userobj.name in usernamelist:   # found a user
            realusers.append(userobj.name)
            if userobj.isSubscribedTo([pagename]):
                success = True
            elif not userobj.email and not userobj.jid:
                success = False
            elif userobj.subscribe(pagename):
                success = True
            if success:
                result.append(formatter.smiley('{OK}'))
                result.append(formatter.text(" "))
            else:
                result.append(formatter.smiley('{X}'))
                result.append(formatter.text(" "))
            result.append(formatter.url(1, Page(request, userobj.name).url(request)))
            result.append(formatter.text(userobj.name))
            result.append(formatter.url(0))
            result.append(formatter.linebreak(preformatted=0))

    result.extend([''.join([formatter.smiley('{X}'), formatter.text(" " + _("Not a user:") + " " + username), formatter.linebreak(preformatted=0)]) for username in usernamelist if username not in realusers])

    return ''.join(result)

def execute(pagename, request):
    _ = request.getText
    if not request.user.may.admin(pagename):
        thispage = Page(request, pagename)
        request.theme.add_msg(_("You are not allowed to perform this action."), "error")
        return thispage.send_page()
    elif 'users' not in request.form:
        show_form(pagename, request)
    else:
        show_result(pagename, request)

if __name__ == '__main__':
    args = sys.argv
    if not len(args) > 1:
        print >>sys.stderr, """Subscribe users

%(myname)s pagename username[,username[,username[,...]]] [URL]

Subscribes the users to a page.
URL is just needed for a farmconfig scenario.

Example:
%(myname)s FrontPage TestUser,MatthewSimpson

""" % {"myname": os.path.basename(args[0])}
        raise SystemExit

    pagename = args[1]
    usernames = args[2]

    if len(args) > 3:
        request_url = args[3]
    else:
        request_url = "localhost/"

    # Setup MoinMoin environment
    from MoinMoin.request import request_cli
    request = request_cli.Request(url=request_url)
    request.form = request.args = request.setup_args()

    from MoinMoin.formatter.text_plain import Formatter
    formatter = Formatter(request)

    print subscribe_users(request, usernames.split(","), pagename, formatter)

