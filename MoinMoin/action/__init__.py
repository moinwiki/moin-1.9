# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Action Implementation

    Actions are triggered by the user clicking on special links on the page
    (e.g. the "edit" link). The name of the action is passed in the "action"
    CGI parameter.

    The sub-package "MoinMoin.action" contains external actions, you can
    place your own extensions there (similar to extension macros). User
    actions that start with a capital letter will be displayed in a list
    at the bottom of each page.

    User actions starting with a lowercase letter can be used to work
    together with a user macro; those actions a likely to work only if
    invoked BY that macro, and are thus hidden from the user interface.
    
    Additionally to the usual stuff, we provide an ActionBase class here with
    some of the usual base functionality for an action, like checking
    actions_excluded, making and checking tickets, rendering some form,
    displaying errors and doing stuff after an action.
    
    @copyright: 2000-2004 by Jürgen Hermann <jh@web.de>,
                2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin.util import pysupport
from MoinMoin import wikiutil
from MoinMoin.Page import Page

# create a list of extension actions from the package directory
modules = pysupport.getPackageModules(__file__)

# builtin-stuff (see do_<name> below):
names = ['show', 'recall', 'raw', 'format', 'content', 'print', 'refresh', 'goto', 'userform', ]

class ActionBase:
    """ action base class with some generic stuff to inherit

    Note: the action name is the class name of the derived class
    """
    def __init__(self, pagename, request):
        self.request = request
        self.form = request.form
        self.cfg = request.cfg
        self._ = _ = request.getText
        self.pagename = pagename
        self.actionname = self.__class__.__name__
        self.use_ticket = False # set this to True if you want to use a ticket
        self.user_html = '''Just checking.''' # html fragment for make_form
        self.form_cancel = "cancel" # form key for cancelling action
        self.form_cancel_label = _("Cancel") # label for the cancel button
        self.form_trigger = "doit" # form key for triggering action (override with e.g. 'rename')
        self.form_trigger_label = _("Do it.") # label for the trigger button
        self.page = Page(request, pagename)
        self.error = ''

    # CHECKS -----------------------------------------------------------------
    def is_excluded(self):
        """ Return True if action is excluded """
        return self.actionname in self.cfg.actions_excluded

    def is_allowed(self):
        """ Return True if action is allowed (by ACL) """
        return True

    def check_condition(self):
        """ Check if some other condition is not allowing us to do that action,
            return error msg or None if there is no problem.

            You can use this to e.g. check if a page exists.
        """
        return None

    def ticket_ok(self):
        """ Return True if we check for tickets and there is some valid ticket
            in the form data or if we don't check for tickets at all.
            Use this to make sure someone really used the web interface.
        """
        if not self.use_ticket:
            return True
        # Require a valid ticket. Make outside attacks harder by
        # requiring two full HTTP transactions
        ticket = self.form.get('ticket', [''])[0]
        return wikiutil.checkTicket(ticket)

    # UI ---------------------------------------------------------------------
    def get_form_html(self, buttons_html):
        """ Override this to assemble the inner part of the form,
            for convenience we give him some pre-assembled html for the buttons.
        """
        _ = self._
        prompt = _("Execute action %(actionname)s?") % {'actionname': self.actionname}
        return "<p>%s</p>%s" % (prompt, buttons_html)

    def make_buttons(self):
        """ return a list of form buttons for the action form """
        return [
            (self.form_trigger, self.form_trigger_label),
            (self.form_cancel, self.form_cancel_label),
        ]

    def make_form(self):
        """ Make some form html for later display.

        The form might contain an error that happened when trying to do the action.
        """
        from MoinMoin.widget.dialog import Dialog
        _ = self._

        if self.error:
            error_html = u'<p class="error">%s</p>\n' % self.error
        else:
            error_html = ''

        buttons = self.make_buttons()
        buttons_html = []
        for button in buttons:
            buttons_html.append('<input type="submit" name="%s" value="%s">' % button)
        buttons_html = "".join(buttons_html)

        if self.use_ticket:
            ticket_html = '<input type="hidden" name="ticket" value="%s">' % wikiutil.createTicket()
        else:
            ticket_html = ''

        d = {
            'error_html': error_html,
            'actionname': self.actionname,
            'pagename': self.pagename,
            'ticket_html': ticket_html,
            'user_html': self.get_form_html(buttons_html),
        }

        form_html = '''
%(error_html)s
<form method="post" action="">
<input type="hidden" name="action" value="%(actionname)s">
%(ticket_html)s
%(user_html)s
</form>''' % d

        return Dialog(self.request, content=form_html)

    def render_msg(self, msg):
        """ Called to display some message (can also be the action form) """
        self.page.send_page(self.request, msg=msg)

    def render_success(self, msg):
        """ Called to display some message when the action succeeded """
        self.page.send_page(self.request, msg=msg)

    def render_cancel(self):
        """ Called when user has hit the cancel button """
        self.page.send_page(self.request) # we don't tell user he has hit cancel :)

    def render(self):
        """ Render action - this is the main function called by action's
            execute() function.

            We usually render a form here, check for posted forms, etc.
        """
        _ = self._
        form = self.form

        if form.has_key(self.form_cancel):
            self.render_cancel()
            return

        # Validate allowance, user rights and other conditions.
        error = None
        if self.is_excluded():
            error = _('Action %(actionname)s is excluded in this wiki!') % {'actionname': self.actionname }
        elif not self.is_allowed():
            error = _('You are not allowed to use action %(actionname)s on this page!') % {'actionname': self.actionname }
        if error is None:
            error = self.check_condition()
        if error:
            self.render_msg(error)
        elif form.has_key(self.form_trigger): # user hit the trigger button
            if self.ticket_ok():
                success, self.error = self.do_action()
            else:
                success = False
                self.error = _('Please use the interactive user interface to use action %(actionname)s!') % {'actionname': self.actionname }
            self.do_action_finish(success)
        else:
            # Return a new form
            self.render_msg(self.make_form())

    # Executing the action ---------------------------------------------------
    def do_action(self):
        """ Do the action and either return error msg or None, if there was no error. """
        return None

    # AFTER the action -------------------------------------------------------
    def do_action_finish(self, success):
        """ Override this to handle success or failure (with error in self.error) of your action.
        """
        if success:
            self.render_success(self.error)
        else:
            self.render_msg(self.make_form()) # display the form again


# Builtin Actions ------------------------------------------------------------

def do_raw(pagename, request):
    """ send raw content of a page (e.g. wiki markup) """
    if not request.user.may.read(pagename):
        Page(request, pagename).send_page(request)
    else:
        try:
            rev = int(request.form.get('rev', [0])[0])
        except StandardError:
            rev = 0
        Page(request, pagename, rev=rev).send_raw()

def do_show(pagename, request, count_hit=1, cacheable=1):
    """ show a page, either current revision or the revision given by rev form value.
        if count_hit is non-zero, we count the request for statistics.
    """
    # We must check if the current page has different ACLs.
    if not request.user.may.read(pagename):
        Page(request, pagename).send_page(request)
    else:
        mimetype = request.form.get('mimetype', [u"text/html"])[0]
        try:
            rev = int(request.form.get('rev', [0])[0])
        except StandardError:
            rev = 0
        if rev == 0:
            request.cacheable = cacheable
        Page(request, pagename, rev=rev, formatter=mimetype).send_page(request, count_hit=count_hit)

def do_format(pagename, request):
    """ send a page using a specific formatter given by mimetype form key.
        Since 5.5.2006 this functionality is also done by do_show, but do_format
        has a default of text/plain when no format is given.
        It also does not count in statistics and also does not set the cacheable flag.
        DEPRECATED: remove this action when we don't need it any more for compatibility.
    """
    if not request.form.has_key('mimetype'):
        request.form['mimetype'] = [u"text/plain"]
    do_show(pagename, request, count_hit=0, cacheable=0)

def do_content(pagename, request):
    """ same as do_show, but we only show the content """
    request.emit_http_headers()
    page = Page(request, pagename)
    request.write('<!-- Transclusion of %s -->' % request.getQualifiedURL(page.url(request)))
    page.send_page(request, count_hit=0, content_only=1)

def do_print(pagename, request):
    """ same as do_show, but send_page will notice the print mode """
    do_show(pagename, request)

def do_recall(pagename, request):
    """ same as do_show, but never caches and never counts hits """
    do_show(pagename, request, count_hit=0, cacheable=0)

def do_refresh(pagename, request):
    """ Handle refresh action """
    # Without arguments, refresh action will refresh the page text_html cache.
    arena = request.form.get('arena', ['Page.py'])[0]
    if arena == 'Page.py':
        arena = Page(request, pagename)
    key = request.form.get('key', ['text_html'])[0]

    # Remove cache entry (if exists), and send the page
    from MoinMoin import caching
    caching.CacheEntry(request, arena, key, scope='item').remove()
    caching.CacheEntry(request, arena, "pagelinks", scope='item').remove()
    do_show(pagename, request)

def do_goto(pagename, request):
    """ redirect to another page """
    target = request.form.get('target', [''])[0]
    request.http_redirect(Page(request, target).url(request, escape=0, relative=False))

def do_userform(pagename, request):
    """ save data posted from UserPreferences """
    from MoinMoin import userform
    savemsg = userform.savedata(request)
    Page(request, pagename).send_page(request, msg=savemsg)

# Dispatching ----------------------------------------------------------------
def getNames(cfg):
    if hasattr(cfg, 'action_names'):
        return cfg.action_names
    else:
        lnames = names[:]
        lnames.extend(wikiutil.getPlugins('action', cfg))
        cfg.action_names = lnames # remember it
        return lnames

def getHandler(request, action, identifier="execute"):
    """ return a handler function for a given action or None """
    # check for excluded actions
    if action in request.cfg.actions_excluded:
        return None

    try:
        handler = wikiutil.importPlugin(request.cfg, "action", action, identifier)
    except wikiutil.PluginMissingError:
        handler = globals().get('do_' + action)

    return handler

