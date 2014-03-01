# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - common functions for notification framework

    Code for building messages informing about events (changes)
    happening in the wiki.

    @copyright: 2007 by Karol Nowak <grywacz@gmail.com>
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import user, wikiutil
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
    """ Used to signal an invalid change event """
    pass


def page_change_message(msgtype, request, page, lang, **kwargs):
    """Prepare a notification text for a page change of given type

    @param msgtype: a type of message to send (page_changed, page_renamed, ...)
    @type msgtype: str or unicode
    @param **kwargs: a dictionary of additional parameters, which depend on msgtype

    @return: dictionary containing data about the changed page
    @rtype: dict

    """
    _ = lambda text: request.getText(text, lang=lang)
    cfg = request.cfg
    data = {}
    data['revision'] = str(page.getRevList()[0])
    data['page_name'] = pagename = page.page_name
    sitename = page.cfg.sitename or request.url_root
    data['editor'] = editor = username = page.uid_override or user.getUserIdentification(request)

    trivial = (kwargs.get('trivial') and _("Trivial ")) or ""

    if msgtype == "page_changed":
        data['subject'] = _(cfg.mail_notify_page_changed_subject) % locals()
        data['text'] = _(cfg.mail_notify_page_changed_intro) % locals()

        revisions = kwargs['revisions']
        # append a diff (or append full page text if there is no diff)
        if len(revisions) < 2:
            data['diff'] = _("New page:\n") + page.get_raw_body()
        else:
            lines = wikiutil.pagediff(request, page.page_name, revisions[1],
                                      page.page_name, revisions[0])
            if lines:
                data['diff'] = '\n'.join(lines)
            else:
                data['diff'] = _("No differences found!\n")

    elif msgtype == "page_deleted":
        data['subject'] = _(cfg.mail_notify_page_deleted_subject) % locals()
        data['text'] = _(cfg.mail_notify_page_deleted_intro) % locals()

        revisions = kwargs['revisions']
        latest_existing = revisions[0]
        lines = wikiutil.pagediff(request, page.page_name, latest_existing,
                                  page.page_name, latest_existing + 1)
        if lines:
            data['diff'] = '\n'.join(lines)
        else:
            data['diff'] = _("No differences found!\n")

    elif msgtype == "page_renamed":
        data['old_name'] = oldname = kwargs['old_name']
        data['subject'] = _(cfg.mail_notify_page_renamed_subject) % locals()
        data['text'] = _(cfg.mail_notify_page_renamed_intro) % locals()
        data['diff'] = ''

    else:
        raise UnknownChangeType()

    if 'comment' in kwargs and kwargs['comment']:
        data['comment'] = kwargs['comment']

    return data


def user_created_message(request, _, sitename, username, email):
    """Formats a message used to notify about accounts being created

    @return: a dict containing message body and subject
    """
    cfg = request.cfg
    sitename = sitename or "Wiki"
    useremail = email

    data = {}
    data['subject'] = _(cfg.mail_notify_user_created_subject) % locals()
    data['text'] = _(cfg.mail_notify_user_created_intro) % locals()
    return data


def attachment_added(request, _, page_name, attach_name, attach_size):
    return _attachment_changed(request, _, page_name, attach_name, attach_size, change="added")


def attachment_removed(request, _, page_name, attach_name, attach_size):
    return _attachment_changed(request, _, page_name, attach_name, attach_size, change="removed")


def _attachment_changed(request, _, page_name, attach_name, attach_size, change):
    """Formats a message used to notify about new / removed attachments

    @param _: a gettext function
    @return: a dict with notification data
    """
    cfg = request.cfg
    pagename = page_name
    sitename = cfg.sitename or request.url_root
    editor = user.getUserIdentification(request)
    data = {}
    data['editor'] = editor
    data['page_name'] = page_name
    data['attach_size'] = attach_size
    data['attach_name'] = attach_name
    if change == "added":
        data['subject'] = _(cfg.mail_notify_att_added_subject) % locals()
        data['text'] = _(cfg.mail_notify_att_added_intro) % locals()
    elif change == "removed":
        data['subject'] = _(cfg.mail_notify_att_removed_subject) % locals()
        data['text'] = _(cfg.mail_notify_att_removed_intro) % locals()
    else:
        raise UnknownChangeType()
    return data


# XXX: clean up this method to take a notification type instead of bool for_jabber
def filter_subscriber_list(event, subscribers, for_jabber):
    """Filter a list of page subscribers to honor event subscriptions

    @param subscribers: list of subscribers (dict of lists, language is the key)
    @param for_jabber: require jid
    @type subscribers: dict

    """
    event_name = event.name

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
