"""
    MoinMoin - E-Mail Import

    @copyright: 2006 by MoinMoin:AlexanderSchremmer
    @license: GNU GPL, see COPYING for details.
"""

# TODO: check XXX, auf welchen seiten soll
# eine uebersicht generiert werden?

import os
import re
import sys
import email
import time
from email.Utils import parseaddr, parsedate_tz, mktime_tz
# python, at least up to 2.4, ships a broken parser for headers

# XXX debugging
sys.path.append(r"C:\Dokumente und Einstellungen\Administrator\Eigene Dateien\Progra\Python\MoinMoin\moin-1.6-mail\sa")
sys.path.append(r"C:\Dokumente und Einstellungen\Administrator\Eigene Dateien\Progra\Python\MoinMoin\moin-1.6-mail")

from MoinMoin import user, wikiutil, config
from MoinMoin.action.AttachFile import add_attachment, AttachmentAlreadyExists
from MoinMoin.Page import Page
from MoinMoin.PageEditor import PageEditor
from MoinMoin.request.CLI import Request as RequestCLI
from MoinMoin.support.HeaderFixed import decode_header

#XXX debugging
fname = (
    #r"C:\Dokumente und Einstellungen\Administrator\Eigene Dateien\Progra\Python\MoinMoin\mailint\testmsg.txt"
    #r"C:\Dokumente und Einstellungen\Administrator\Eigene Dateien\Progra\Python\MoinMoin\mailint\rf-mime-torture-test-1.0.msg.txt"
    #r"C:\Dokumente und Einstellungen\Administrator\Eigene Dateien\Progra\Python\MoinMoin\mailint\torture-test.msg.txt"
    r"C:\Dokumente und Einstellungen\Administrator\Eigene Dateien\Progra\Python\MoinMoin\mailint\umlaute2.msg.txt"
    #r"C:\Dokumente und Einstellungen\Administrator\Eigene Dateien\Progra\Python\MoinMoin\mailint\umlaute.msg.txt"
        )
input = file(fname)
#XXX
#input = sys.stdin

debug = False

re_subject = re.compile(r"\[([^\]]*)\]")
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
        print >>sys.stderr, text

def decode_2044(header):
    """ Decodes header field. Compare RFC 2044. """
    chunks = decode_header(header)
    chunks_decoded = []
    for i in chunks:
        chunks_decoded.append(i[0].decode(i[1] or 'ascii'))
        chunks_decoded.append(u" ") # workaround for python bug #1467619
    return u''.join(chunks_decoded).strip()

def generate_unique_name(name, old_names):
    """ Is used to generate unique names among attachments. """
    if name not in old_names:
        return name
    i = 0
    while 1:
        i += 1
        new_name = name + "-" + str(i)
        if new_name not in old_names:
            return new_name

def process_message(message):
    """ Processes the read message and decodes attachments. """
    attachments = []
    html_data = []
    text_data = []
   
    to_addr = parseaddr(decode_2044(message['To']))
    from_addr = parseaddr(decode_2044(message['From']))
    subject = decode_2044(message['Subject'])
    date = time.strftime("%Y-%m-%d %H:%M", time.gmtime(mktime_tz(parsedate_tz(message['Date']))))
    
    log("Processing mail:\n To: %r\n From: %r\n Subject: %r" % (to_addr, from_addr, subject))
    
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
                print "Unknown mail part", repr((part.get_charsets(), part.get_content_charset(), part.get_content_type(), part.is_multipart(), ))

    return {'text': u"".join(text_data), 'html': u"".join(html_data),
            'attachments': attachments, 'to_addr': to_addr, 'from_addr': from_addr,
            'subject': subject, 'date': date}

def get_pagename_content(msg, email_subpage_template):
    """ Generates pagename and content according to the specification
        that can be found on MoinMoin:FeatureRequests/WikiEMoinMoin\mailintegration """

    generate_summary = False
    choose_html = False
    
    pagename_tpl = msg['to_addr'][0]
    if not pagename_tpl:
        m = re_subject.match(msg['subject'])
        if m:
            pagename_tpl = m.group(1)
    else:
        # special fix for outlook users :-)
        if pagename_tpl[-1] == pagename_tpl[0] == "'":
            pagename_tpl = pagename_tpl[1:-1]
    
    if pagename_tpl.endswith("/"):
        pagename_tpl += email_subpage_template

    # last resort
    if not pagename_tpl:
        pagename_tpl = email_subpage_template

    # rewrite using string.formatter when python 2.4 is mandantory
    pagename = (pagename_tpl.replace("$from", msg['from_addr'][0]).
                replace("$date", msg['date']).
                replace("$subj", msg['subject']))

    if pagename.startswith("+ ") and "/" in pagename:
        generate_summary = True
        pagename = pagename[1:].lstrip()

    if choose_html and msg['html']:
        content = "{{{#!html\n%s\n}}}" % msg['html'].replace("}}}", "} } }")
    else:
        # strip signatures ...
        content = re_sigstrip.sub("", msg['text'])

    return {'pagename': pagename, 'content': content, 'generate_summary': generate_summary}

def import_mail_from_file(input):
    """ Reads an RFC 822 message from the file `input` and imports it to
        the wiki. """
    msg = process_message(email.message_from_file(input))

    request = RequestCLI(url = 'localhost/')
    email_subpage_template = request.cfg.email_subpage_template

    request.user = user.get_by_email_address(request, msg['from_addr'][1])
    
    if not request.user:
        raise ProcessingError("No suitable user found for mail address %r" % (msg['from_addr'][1], ))

    d = get_pagename_content(msg, email_subpage_template)
    pagename = d['pagename']
    generate_summary = d['generate_summary']

    comment = u"Imported mail from %s re %s" % (msg['from_addr'][0], msg['subject'])
    
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
                fname = add_attachment(request, pagename, fname, att.data)
                attachments.append(fname)
            except AttachmentAlreadyExists:
                i += 1
            else:
                break

    # build an attachment link table for the page with the e-mail
    attachment_table = [""]
    escape_link = lambda x: x.replace(" ", "%20")
    for x in attachments:
        attachment_table.append(u" * [attachment:%s attachment:%s]" % tuple([escape_link(x)] * 2))

    # assemble old page content and new mail body together
    old_content = Page(request, pagename).get_raw_body()
    if old_content:
        new_content = u"%s-----\n%s" % (old_content, d['content'], )
    else:
        new_content = d['content']
    new_content += u"\n".join(attachment_table)

    try:
        page.saveText(new_content, 0, comment=comment)
    except page.AccessDenied:
        raise ProcessingError("Access denied for page %r" % pagename)
    
    if generate_summary and "/" in pagename:
        parent_page = u"/".join(pagename.split("/")[:-1])
        mail_table = "Here will be added a table with links to the mail later on."
        content = "%s\n\n%s" % (Page(request, parent_page).get_raw_body(), mail_table)
        # XXX Append a table "from / to / subj / date / link to content / link(s) to attachments" to the end of the parent page
        page = PageEditor(request, parent_page, do_editor_backup=0)
        page.saveText(content, 0, comment=comment)

if __name__ == "__main__":
    try:
        import_mail_from_file(input)
    except ProcessingError, e:
        print >>sys.stderr, "An error occured while processing the message:", e.args
