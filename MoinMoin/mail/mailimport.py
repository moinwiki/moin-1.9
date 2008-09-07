"""
    MoinMoin - E-Mail Import into wiki

    Just call this script with the URL of the wiki as a single argument
    and feed the mail into stdin.

    @copyright: 2006 MoinMoin:AlexanderSchremmer,
                2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

import sys, re, time
import email
from email.Utils import getaddresses, parsedate_tz, mktime_tz

from MoinMoin import user
from MoinMoin.action.AttachFile import add_attachment, AttachmentAlreadyExists
from MoinMoin.Page import Page
from MoinMoin.PageEditor import PageEditor
from MoinMoin.request.request_cli import Request as RequestCLI
# python, at least up to 2.4, ships a broken parser for headers
from MoinMoin.support.HeaderFixed import decode_header

infile = sys.stdin

debug = False

re_sigstrip = re.compile("\r?\n-- \r?\n.*$", re.S)

class attachment(object):
    """ Represents an attachment of a mail. """
    def __init__(self, filename, mimetype, data):
        self.filename = filename
        self.mimetype = mimetype
        self.data = data

    def __repr__(self):
        return "<attachment filename=%r mimetype=%r size=%i bytes>" % (
            self.filename, self.mimetype, len(self.data))

class ProcessingError(Exception):
    pass

def log(text):
    if debug:
        print >> sys.stderr, text

def decode_2044(header):
    """ Decodes header field. See RFC 2044. """
    chunks = decode_header(header)
    chunks_decoded = []
    for i in chunks:
        chunks_decoded.append(i[0].decode(i[1] or 'ascii'))
    return u''.join(chunks_decoded).strip()

def email_to_markup(request, email):
    """ transform the (realname, mailaddr) tuple we get in email argument to
        some string usable as wiki markup, that represents that person (either
        HomePage link for a wiki user, or just the realname of the person). """
    realname, mailaddr = email
    u = user.get_by_email_address(request, mailaddr)
    if u:
        markup = u.wikiHomeLink()
    else:
        markup = realname or mailaddr
    return markup

def get_addrs(message, header):
    """ get a list of tuples (realname, mailaddr) from the specified header """
    dec_hdr = [decode_2044(hdr) for hdr in message.get_all(header, [])]
    return getaddresses(dec_hdr)

def process_message(message):
    """ Processes the read message and decodes attachments. """
    attachments = []
    html_data = []
    text_data = []

    from_addr = get_addrs(message, 'From')[0]
    to_addrs = get_addrs(message, 'To')
    cc_addrs = get_addrs(message, 'Cc')
    bcc_addrs = get_addrs(message, 'Bcc') # depending on sending MTA, this can be present or not
    envelope_to_addrs = get_addrs(message, 'X-Original-To') + get_addrs(message, 'X-Envelope-To') # Postfix / Sendmail does this
    target_addrs = to_addrs + cc_addrs + bcc_addrs + envelope_to_addrs

    subject = decode_2044(message['Subject'])
    date = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(mktime_tz(parsedate_tz(message['Date']))))

    log("Processing mail:\n To: %r\n From: %r\n Subject: %r" % (to_addrs[0], from_addr, subject))

    for part in message.walk():
        log(" Part " + repr((part.get_charsets(), part.get_content_charset(), part.get_content_type(), part.is_multipart(), )))
        ct = part.get_content_type()
        cs = part.get_content_charset() or "latin1"
        payload = part.get_payload(None, True)

        fn = part.get_filename()
        if fn is not None and fn.startswith("=?"): # heuristics ...
            fn = decode_2044(fn)

        if fn is None and part["Content-Disposition"] is not None and "attachment" in part["Content-Disposition"]:
            # this doesn't catch the case where there is no content-disposition but there is a file to offer to the user
            # i hope that this can be only found in mails that are older than 10 years,
            # so I won't care about it here
            fn = part["Content-Description"] or "NoName"
        if fn:
            a = attachment(fn, ct, payload)
            attachments.append(a)
        else:
            if ct == 'text/plain':
                text_data.append(payload.decode(cs))
                log(repr(payload.decode(cs)))
            elif ct == 'text/html':
                html_data.append(payload.decode(cs))
            elif not part.is_multipart():
                log("Unknown mail part " + repr((part.get_charsets(), part.get_content_charset(), part.get_content_type(), part.is_multipart(), )))

    return {'text': u"".join(text_data), 'html': u"".join(html_data),
            'attachments': attachments,
            'target_addrs': target_addrs,
            'to_addrs': to_addrs, 'cc_addrs': cc_addrs, 'bcc_addrs': bcc_addrs, 'envelope_to_addrs': envelope_to_addrs,
            'from_addr': from_addr,
            'subject': subject, 'date': date}

def get_pagename_content(request, msg):
    """ Generates pagename and content according to the specification
        that can be found on MoinMoin:FeatureRequests/WikiEmailintegration """
    generate_summary = False
    choose_html = True

    cfg = request.cfg
    email_subpage_template = cfg.mail_import_subpage_template
    email_pagename_envelope = cfg.mail_import_pagename_envelope
    wiki_addrs = cfg.mail_import_wiki_addrs
    search_list = cfg.mail_import_pagename_search
    re_subject = re.compile(cfg.mail_import_pagename_regex)

    subj = msg['subject'].strip()
    pagename_tpl = ""
    for method in search_list:
        if method == 'to':
            for addr in msg['target_addrs']:
                if addr[1].strip().lower() in wiki_addrs:
                    pagename_tpl = addr[0]
                    # special fix for outlook users :-)
                    if pagename_tpl and pagename_tpl[-1] == pagename_tpl[0] == "'":
                        pagename_tpl = pagename_tpl[1:-1]
                    if pagename_tpl:
                        break
        elif method == 'subject':
            m = re_subject.search(subj)
            if m:
                pagename_tpl = m.group(1)
                # remove the pagename template from the subject:
                subj = re_subject.sub('', subj, 1).strip()
        if pagename_tpl:
            break

    pagename_tpl = pagename_tpl.strip()
    # last resort
    if not pagename_tpl:
        pagename_tpl = email_subpage_template

    if not subj:
        subj = '(...)' # we need non-empty subject
    msg['subject'] = subj

    # for normal use, email_pagename_envelope is just u"%s" - so nothing changes.
    # for special use, you can use u"+ %s/" - so you don't need to enter "+"
    # and "/" in every email, but you get the result as if you did.
    pagename_tpl = email_pagename_envelope % pagename_tpl

    if pagename_tpl.endswith("/"):
        pagename_tpl += email_subpage_template

    subject = msg['subject'].replace('/', '\\') # we can't use / in pagenames

    # rewrite using string.formatter when python 2.4 is mandatory
    pagename = (pagename_tpl.replace("$from", msg['from_addr'][0]).
                replace("$date", msg['date']).
                replace("$subject", subject))

    if pagename.startswith("+ ") and "/" in pagename:
        generate_summary = True
        pagename = pagename[1:].lstrip()

    pagename = request.normalizePagename(pagename)

    if choose_html and msg['html']:
        content = "{{{#!html\n%s\n}}}" % msg['html'].replace("}}}", "} } }")
    else:
        # strip signatures ...
        content = re_sigstrip.sub("", msg['text'])

    return {'pagename': pagename, 'content': content, 'generate_summary': generate_summary}

def import_mail_from_string(request, string):
    """ Reads an RFC 822 compliant message from a string and imports it
        to the wiki. """
    return import_mail_from_message(request, email.message_from_string(string))

def import_mail_from_file(request, infile):
    """ Reads an RFC 822 compliant message from the file `infile` and imports it to
        the wiki. """
    return import_mail_from_message(request, email.message_from_file(infile))

def import_mail_from_message(request, message):
    """ Reads a message generated by the email package and imports it
        to the wiki. """
    _ = request.getText
    msg = process_message(message)

    wiki_addrs = request.cfg.mail_import_wiki_addrs

    request.user = user.get_by_email_address(request, msg['from_addr'][1])

    if not request.user:
        raise ProcessingError("No suitable user found for mail address %r" % (msg['from_addr'][1], ))

    d = get_pagename_content(request, msg)
    pagename = d['pagename']
    generate_summary = d['generate_summary']

    comment = u"Mail: '%s'" % (msg['subject'], )

    page = PageEditor(request, pagename, do_editor_backup=0)

    if not request.user.may.save(page, "", 0):
        raise ProcessingError("Access denied for page %r" % pagename)

    attachments = []

    for att in msg['attachments']:
        i = 0
        while 1:
            if i == 0:
                fname = att.filename
            else:
                components = att.filename.split(".")
                new_suffix = "-" + str(i)
                # add the counter before the file extension
                if len(components) > 1:
                    fname = u"%s%s.%s" % (u".".join(components[:-1]), new_suffix, components[-1])
                else:
                    fname = att.filename + new_suffix
            try:
                # get the fname again, it might have changed
                fname, fsize = add_attachment(request, pagename, fname, att.data)
                attachments.append(fname)
            except AttachmentAlreadyExists:
                i += 1
            else:
                break

    # build an attachment link table for the page with the e-mail
    attachment_links = [""] + [u'''[[attachment:%s|%s]]''' % ("%s/%s" % (pagename, att), att) for att in attachments]

    # assemble old page content and new mail body together
    old_content = Page(request, pagename).get_raw_body()
    if old_content:
        new_content = u"%s\n-----\n" % old_content
    else:
        new_content = ''

    #if not (generate_summary and "/" in pagename):
    #generate header in any case:
    new_content += u"'''Mail: %s (%s, <<DateTime(%s)>>)'''\n\n" % (msg['subject'], email_to_markup(request, msg['from_addr']), msg['date'])

    new_content += d['content']
    new_content += "\n" + u"\n * ".join(attachment_links)

    try:
        page.saveText(new_content, 0, comment=comment)
    except page.AccessDenied:
        raise ProcessingError("Access denied for page %r" % pagename)

    if generate_summary and "/" in pagename:
        parent_page = u"/".join(pagename.split("/")[:-1])
        old_content = Page(request, parent_page).get_raw_body().splitlines()

        found_table = None
        table_ends = None
        for lineno, line in enumerate(old_content):
            if line.startswith("## mail_overview") and old_content[lineno+1].startswith("||"):
                found_table = lineno
            elif found_table is not None and line.startswith("||"):
                table_ends = lineno + 1
            elif table_ends is not None and not line.startswith("||"):
                break

        # in order to let the gettext system recognise the <<GetText>> calls used below,
        # we must repeat them here:
        [_("Date"), _("From"), _("To"), _("Content"), _("Attachments")]

        table_header = (u"\n\n## mail_overview (don't delete this line)\n" +
                        u"|| '''<<GetText(Date)>> ''' || '''<<GetText(From)>> ''' || '''<<GetText(To)>> ''' || '''<<GetText(Content)>> ''' || '''<<GetText(Attachments)>> ''' ||\n"
                       )

        from_col = email_to_markup(request, msg['from_addr'])
        to_col = ' '.join([email_to_markup(request, (realname, mailaddr))
                           for realname, mailaddr in msg['target_addrs'] if not mailaddr in wiki_addrs])
        subj_col = '[[%s|%s]]' % (pagename, msg['subject'])
        date_col = msg['date']
        attach_col = " ".join(attachment_links)
        new_line = u'|| <<DateTime(%s)>> || %s || %s || %s || %s ||' % (date_col, from_col, to_col, subj_col, attach_col)
        if found_table is not None:
            content = "\n".join(old_content[:table_ends] + [new_line] + old_content[table_ends:])
        else:
            content = "\n".join(old_content) + table_header + new_line

        page = PageEditor(request, parent_page, do_editor_backup=0)
        page.saveText(content, 0, comment=comment)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = 'localhost/'

    request = RequestCLI(url=url)

    try:
        import_mail_from_file(request, infile)
    except ProcessingError, e:
        print >> sys.stderr, "An error occured while processing the message:", e.args

