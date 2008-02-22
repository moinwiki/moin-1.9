#!/usr/bin/env python
"""
    read mail text from standard input and
    send an email to all i18n maintainers
    %(lang)s will be replaced by language

    TODO:
    * needs update to 1.6, doesn't work anymore "as is"
    * use MoinMoin.script framework
    * check that sendmail stuff, we also have it in MoinMoin.mail

    @copyright: 2004 Thomas Waldmann
    @license: GNU GPL, see COPYING for details
"""

mail_from = 'tw-public@gmx.de'
mail_subject = 'MoinMoin i18n notification'

mail_smarthost = 'localhost'
mail_login = None
charset = 'iso-8859-1'

from MoinMoin.i18n.meta import languages

def sendmail(mfrom, mto, subject, text):
    """
    Send a mail to the address(es) in 'to', with the given subject and
    mail body 'text'.

    Return a tuple of success or error indicator and message.

    TODO: code duplicated from MoinMoin/util/mail.py

    @param mfrom: source email address
    @param to: target email address
    @param subject: subject of email
    @param text: email body text
    @rtype: tuple
    @return: (is_ok, msg)
    """
    import smtplib, socket, os
    from email.MIMEText import MIMEText
    from email.Header import Header
    from email.Utils import formatdate
    global charset, mail_smarthost, mail_login

    # Create a text/plain message
    msg = MIMEText(text, 'plain', charset)
    msg['From'] = mfrom
    msg['To'] = ', '.join(mto)
    msg['Subject'] = Header(subject, charset)
    msg['Date'] = formatdate()

    try:
        server = smtplib.SMTP(mail_smarthost)
        try:
            #server.set_debuglevel(1)
            if mail_login:
                user, pwd = mail_login.split()
                server.login(user, pwd)
            server.sendmail(mail_from, mto, msg.as_string())
        finally:
            try:
                server.quit()
            except AttributeError:
                # in case the connection failed, SMTP has no "sock" attribute
                pass
    except smtplib.SMTPException, e:
        return (0, str(e))
    except (os.error, socket.error), e:
        return (0, "Connection to mailserver '%(server)s' failed: %(reason)s" % {
            'server': mail_smarthost,
            'reason': str(e)
        })

    return (1, "Mail sent OK")

def notify_maintainer(lang, mail_text):
    mailaddr = languages[lang][4]
    rc = None
    if mailaddr and '***vacant***' not in mailaddr:
        text = mail_text % locals()
        rc = sendmail(mail_from, [mailaddr], mail_subject, text)
    return rc

if __name__ == '__main__':
    langs = languages.keys()
    langs.remove('en') # nothing to do for english, so remove it

    #langs = ['de', ] # for testing

    import sys
    mail_text = sys.stdin.read()

    if len(mail_text) > 10: # do not send mails w/o real content
        for lang in langs:
            notify_maintainer(lang, mail_text)

