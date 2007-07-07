# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - common functions for notification framework

    Code for building messages informing about events (changes)
    happening in the wiki.

    @copyright: 2007 by Karol Nowak <grywacz@gmail.com>
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import user, wikiutil
from MoinMoin.Page import Page
from MoinMoin.action.AttachFile import getAttachUrl

class UnknownChangeType:
    pass

def page_change_message(msgtype, request, page, lang, **kwargs):
    """Prepare a notification text for a page change of given type

    @param msgtype: a type of message to send (page_changed, attachment_added, ...)
    @type msgtype: str or unicode
    @param **kwargs: a dictionary of additional parameters, which depend on msgtype

    @return: a formatted, ready to send message
    @rtype: unicode

    """

    _ = request.getText
    page._ = lambda s, formatted=True, r=request, l=lang: r.getText(s, formatted=formatted, lang=l)
    querystr = {}

    if msgtype == "page_changed":
        revisions = kwargs['revisions']
        if len(kwargs['revisions']) >= 2:
            querystr = {'action': 'diff',
                    'rev2': str(revisions[0]),
                    'rev1': str(revisions[1])}

    if msgtype == "attachment_added":
        attachlink = request.getBaseURL() + \
                        getAttachUrl(page.page_name, kwargs['attach_name'], request)

    pagelink = request.getQualifiedURL(page.url(request, querystr, relative=False))

    if msgtype == "page_changed":
        messageBody = _("Dear Wiki user,\n\n"
        'You have subscribed to a wiki page or wiki category on "%(sitename)s" for change notification.\n\n'
        "The following page has been changed by %(editor)s:\n"
        "%(pagelink)s\n\n", formatted=False) % {
            'editor': page.uid_override or user.getUserIdentification(request),
            'pagelink': pagelink,
            'sitename': page.cfg.sitename or request.getBaseURL(),
        }

        # append a diff (or append full page text if there is no diff)
        if len(revisions) < 2:
            messageBody = messageBody + \
                _("New page:\n", formatted=False) + \
                page.get_raw_body()
        else:
            lines = wikiutil.pagediff(request, page.page_name, revisions[1],
                                      page.page_name, revisions[0])
            if lines:
                messageBody = messageBody + "%s\n%s\n" % (("-" * 78), '\n'.join(lines))
            else:
                messageBody = messageBody + _("No differences found!\n", formatted=False)

    elif msgtype == "attachment_added":
        messageBody = _("Dear Wiki user,\n\n"
        'You have subscribed to a wiki page "%(sitename)s" for change notification.\n\n'
        "An attachment has been added to the following page by %(editor)s:\n"
        "Following detailed information is available:\n"
        "Attachment name: %(attach_name)s\n"
        "Attachment size: %(attach_size)s\n"
        "Download link: %(attach_get)s", formatted=False) % {
            'editor': user.getUserIdentification(request),
            'pagelink': pagelink,
            'sitename': page.cfg.sitename or request.getBaseURL(),
            'attach_name': kwargs['attach_name'],
            'attach_size': kwargs['attach_size'],
            'attach_get': attachlink,
        }

    elif msgtype == "page_deleted":
        messageBody = _("Dear wiki user,\n\n"
            'You have subscribed to a wiki page "%(sitename)s" for change notification.\n\n'
            "The following page has been deleted by %(editor)s:\n"
            "%(pagelink)s\n\n", formatted=False) % {
                'editor': page.uid_override or user.getUserIdentification(request),
                'pagelink': pagelink,
                'sitename': page.cfg.sitename or request.getBaseURL(),
        }
    else:
        raise UnknownChangeType()

    if 'comment' in kwargs and kwargs['comment'] is not None:
        messageBody = messageBody + \
            _("The comment on the change is:\n%(comment)s", formatted=False) % {'comment': kwargs['comment']}

    return messageBody

