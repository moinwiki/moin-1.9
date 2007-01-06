# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - login and sendmail form

    @copyright: 2005-2006 by Radomirs Cirskis <nad2000@gmail.com>
    @copyright: 2006 Reimar Bauer, Oliver Siemoneit
    @license: GNU GPL, see COPYING for details.
"""
from MoinMoin.widget import html
from MoinMoin import userform

def make_row(table, label, cell, **kw):
    """ Create a row in the form table.
    """
    table.append(html.TR().extend([
        html.TD(**kw).extend([html.B().append(label), '   ']),
        html.TD().extend(cell),
    ]))
    return table

def execute(macro, args):
    """ Show the login form (but only when not logged in) """
    request = macro.request
    _ = request.getText
    formatter = macro.formatter
    if not args:
        if request.user.valid:
            data = u''
        else:
            data = userform.getLogin(request)
        return data
    elif args == "sendmail":
        sn = request.getScriptname()
        pi = request.getPathinfo()
        action = u"%s%s" % (sn, pi)
        form = html.FORM(action=action)
        table = html.TABLE()

        if not request.cfg.mail_enabled:
            return _("This wiki is not enabled for mail processing.\nContact the owner of the wiki, who can enable email.")
        else:
            buttons = []
            action = u"%s%s" % (sn, pi)
            form = html.FORM(action=action)
            table = html.TABLE(border="0")

            # Add form fields
            for key, label, type, length, textafter in request.cfg.user_form_fields:
                if key == 'email':
                    table = make_row(table, _(label),
                                     [html.INPUT(type=type, size=length, name=key,
                                     value=''), ' ', ])
            # Add buttons
            buttons.append(("account_sendmail", _('Mail me my account data')))
            button_cell = []
            for name, label in buttons:
                if not name in request.cfg.user_form_remove:
                    button_cell.extend([
                        html.INPUT(type="submit", name=name, value=label),
                        ' ',
                    ])
            make_row(table, '', button_cell)

            # Use the user interface language and direction
            lang_attr = request.theme.ui_lang_attr()
            form.append(html.Raw('<div class="userpref"%s>' % lang_attr))
            form.append(html.INPUT(type="hidden", name="action", value="userform"))
            form.append(table)
            form.append(html.Raw("</div>"))

            return unicode(form)
    else:
        return 
