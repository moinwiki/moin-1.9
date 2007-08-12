# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - common functions for notification framework

    Code for building messages informing about events (changes)
    happening in the wiki.

    @copyright: 2007 by Karol Nowak <grywacz@gmail.com>
    @license: GNU GPL, see COPYING for details.
"""

import MoinMoin.user
from MoinMoin import user, wikiutil
from MoinMoin.Page import Page
from MoinMoin.events import EventResult

class Result(EventResult):
    """ A base class for results of notification handlers"""
    pass

class Failure(Result):
    """ Used to report a failure in sending notifications """
    def __init__(self, reason, recipients = None):
        """
        @param recipients: a set of recipients
        @type recipients: set
        """
        self.reason = reason
        self.recipient = None

    def __str__(self):
        return self.reason or u""


class Success(Result):
    """ Used to indicate successfull notifications """

    def __init__(self, recipients):
        """
        @param recipients: a set of recipients
        @type recipients: set
        """
        self.recipients = recipients

class UnknownChangeType(Exception):
    """ Used to signal an invalid page change event """
    pass

def page_change_message(msgtype, request, page, lang, **kwargs):
    """Prepare a notification text for a page change of given type

    @param msgtype: a type of message to send (page_changed, attachment_added, ...)
    @type msgtype: str or unicode
    @param **kwargs: a dictionary of additional parameters, which depend on msgtype

    @return: a formatted, ready to send message
    @rtype: unicode

    """
    from MoinMoin.action.AttachFile import getAttachUrl

    _ = request.getText
    page._ = lambda s, formatted=True, r=request, l=lang: r.getText(s, formatted=formatted, lang=l)
    querystr = {}

    if msgtype == "page_changed":
        revisions = kwargs['revisions']
        if len(kwargs['revisions']) >= 2:
            querystr = {'action': 'diff',
                    'rev2': str(revisions[0]),
                    'rev1': str(revisions[1])}

    pagelink = request.getQualifiedURL(page.url(request, querystr, relative=False))

    if msgtype == "page_changed":
        msg_body = _("Dear Wiki user,\n\n"
        'You have subscribed to a wiki page or wiki category on "%(sitename)s" for change notification.\n\n'
        "The following page has been changed by %(editor)s:\n"
        "%(pagelink)s\n\n", formatted=False) % {
            'editor': page.uid_override or user.getUserIdentification(request),
            'pagelink': pagelink,
            'sitename': page.cfg.sitename or request.getBaseURL(),
        }

        # append a diff (or append full page text if there is no diff)
        if len(revisions) < 2:
            messageBody = msg_body + \
                _("New page:\n", formatted=False) + \
                page.get_raw_body()
        else:
            lines = wikiutil.pagediff(request, page.page_name, revisions[1],
                                      page.page_name, revisions[0])
            if lines:
                msg_body = msg_body + "%s\n%s\n" % (("-" * 78), '\n'.join(lines))
            else:
                msg_body = msg_body + _("No differences found!\n", formatted=False)

    elif msgtype == "page_deleted":
        msg_body = _("Dear wiki user,\n\n"
            'You have subscribed to a wiki page "%(sitename)s" for change notification.\n\n'
            "The following page has been deleted by %(editor)s:\n"
            "%(pagelink)s\n\n", formatted=False) % {
                'editor': page.uid_override or user.getUserIdentification(request),
                'pagelink': pagelink,
                'sitename': page.cfg.sitename or request.getBaseURL(),
        }

    elif msgtype == "page_renamed":
        msg_body = _("Dear wiki user,\n\n"
            'You have subscribed to a wiki page "%(sitename)s" for change notification.\n\n'
            "The following page has been renamed from %(oldname)s by %(editor)s:\n"
            "%(pagelink)s\n\n", formatted=False) % {
                'editor': page.uid_override or user.getUserIdentification(request),
                'pagelink': pagelink,
                'sitename': page.cfg.sitename or request.getBaseURL(),
                'oldname': kwargs['old_name']
        }
    else:
        raise UnknownChangeType()

    if 'comment' in kwargs and kwargs['comment']:
        msg_body = msg_body + \
            _("The comment on the change is:\n%(comment)s", formatted=False) % {'comment': kwargs['comment']}

    return msg_body

def user_created_message(request, sitename, username, email):
    """Formats a message used to notify about accounts being created

    @return: a dict containing message body and subject
    """
    _ = request.getText
    subject = _("New user account created on %(sitename)s") % {'sitename': sitename or "Wiki"}
    body = _("""Dear Superuser, a new user has just been created. Details follow:

    User name: %(username)s
    Email address: %(useremail)s""", formatted=False) % {
         'username': username,
         'useremail': email,
         }

    return {'subject': subject, 'body': body}

def attachment_added(request, page_name, attach_name, attach_size):
    """Formats a message used to notify about new attachments

    @return: a dict containing message body and subject
    """
    from MoinMoin.action.AttachFile import getAttachUrl

    _ = request.getText
    page = Page(request, page_name)
    attachlink = request.getBaseURL() + getAttachUrl(page_name, attach_name, request)
    pagelink = request.getQualifiedURL(page.url(request, {}, relative=False))

    subject = _("New attachment added to page %(pagename)s on %(sitename)s") % {
                'pagename': page_name,
                'sitename': request.cfg.sitename or request.getBaseURL(),
                }

    body = _("Dear Wiki user,\n\n"
    'You have subscribed to a wiki page "%(page_name)s" for change notification. '
    "An attachment has been added to that page by %(editor)s. "
    "Following detailed information is available:\n\n"
    "Attachment name: %(attach_name)s\n"
    "Attachment size: %(attach_size)s\n"
    "Download link: %(attach_get)s", formatted=False) % {
        'editor': user.getUserIdentification(request),
        'pagelink': pagelink,
        'page_name': page_name,
        'attach_name': attach_name,
        'attach_size': attach_size,
        'attach_get': attachlink,
    }

    return {'body': body, 'subject': subject}


# XXX: clean up this method to take a notification type instead of bool for_jabber
def filter_subscriber_list(event, subscribers, for_jabber):
    """Filter a list of page subscribers to honor event subscriptions

    @param subscribers: list of subscribers (dict of lists, language is the key)
    @param for_jabber: require jid
    @type subscribers: dict

    """
    event_name = event.__class__.__name__

    # Filter the list by removing users who don't want to receive
    # notifications about this type of event
    for lang in subscribers.keys():
        userlist = []

        if for_jabber:
            for usr in subscribers[lang]:
                if usr.jid and event_name in usr.jabber_subscribed_events:
                    userlist.append(usr)
        else:
            for usr in subscribers[lang]:
                if usr.email and event_name in usr.email_subscribed_events:
                    userlist.append(usr)

        subscribers[lang] = userlist
