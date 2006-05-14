# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - User Forms

    @copyright: 2001-2004 by Jürgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import wikiutil
from MoinMoin.Page import Page

#############################################################################
### Form definitions
#############################################################################

_required_attributes = ['type', 'name', 'label']

def parseDefinition(request, fielddef, fieldlist):
    """ Parse a form field definition and return the HTML markup for it
    """
    _ = request.getText

    row = '<tr><td nowrap="nowrap" valign="top">&nbsp;%s&nbsp;</td><td>%s</td></tr>\n'
    fields, msg = wikiutil.parseAttributes(request, fielddef)

    if not msg:
        for required in _required_attributes:
            if not fields.has_key(required):
                msg = _('Required attribute "%(attrname)s" missing')  % {
                    'attrname': required}
                break

    if msg:
        # create visible error
        result = row % (msg, fielddef)
    elif fields['type'] == '"caption"':
        # create a centered, bold italic caption
        result = '<tr><td colspan="2" align="center"><em><strong>%s</strong></em></td></tr>\n' % (
            fields['label'][1:-1])
    else:
        # for submit buttons, use `label` as the value
        if fields['type'] == '"submit"':
            fields['value'] = fields['label']
            fields['label'] = ''

        # make sure user cannot use a system name
        fields['name'] = '"form_' + fields['name'][1:]
        fieldlist.append(fields['name'][1:-1])

        wrapper = ('<input', '>\n')
        if fields['type'] == '"textarea"':
            wrapper = ('<textarea', '></textarea>\n')

        result = wrapper[0]
        for key, val in fields.items():
            if key == 'label': continue
            result = '%s %s=%s' % (result, key, val)
        result = result + wrapper[1]

        #result = result + wikiutil.escape(`fields`)

        if fields['type'] == '"submit"':
            result = '<tr><td colspan="2" align="center">%s</td></tr>\n' % result
        else:
            result = row % (fields['label'][1:-1], result)

    return result


def _get_formvalues(form):
    result = {}
    for key in form.keys():
        if key[:5] != 'form_': continue

        val = form.get(key, ["<empty>"])
        if type(val) is type([]):
            # Multiple username fields specified
            val = "|".join(val).replace('\r','')

        result[key] = val

    return result


def do_formtest(pagename, request):
    """ Test a user defined form.
    """
    _ = request.getText

    result = []
    for key, val in _get_formvalues(request.form).items():
        result.append('<li><em>%s</em> = %s</li>' % (key.upper(), repr(wikiutil.escape(val))))
    msg = '%s<ul>\n%s</ul>\n' % (_('Submitted form data:'), '\n'.join(result))

    Page(request, pagename).send_page(request, msg=msg)

