# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - show some statistics chart

    @copyright: 2000-2004 Juergen Hermann <jh@web.de>,
                2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""
from MoinMoin.util import pysupport

def execute(pagename, request):
    """ Show page charts """
    _ = request.getText
    if not request.user.may.read(pagename):
        msg = _("You are not allowed to view this page.")
        return request.page.send_page(msg=msg)

    if not request.cfg.chart_options:
        msg = _("Charts are not available!")
        return request.page.send_page(msg=msg)

    chart_type = request.form.get('type', [''])[0].strip()
    if not chart_type:
        msg = _('You need to provide a chart type!')
        return request.page.send_page(msg=msg)

    try:
        func = pysupport.importName("MoinMoin.stats.%s" % chart_type, 'draw')
    except (ImportError, AttributeError):
        msg = _('Bad chart type "%s"!') % chart_type
        return request.page.send_page(msg=msg)

    func(pagename, request)

