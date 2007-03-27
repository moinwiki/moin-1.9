# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Pagesize Statistics

    This macro creates a bar graph of page size classes.

    @copyright: 2002-2004 Juergen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

_debug = 0

from MoinMoin import wikiutil
from MoinMoin.Page import Page


def linkto(pagename, request, params=''):
    _ = request.getText

    if not request.cfg.chart_options:
        return (request.formatter.sysmsg(1) +
                request.formatter.text(_('Charts are not available!')) +
                request.formatter.sysmsg(0))

    if _debug:
        return draw(pagename, request)

    page = Page(request, pagename)

    # Create escaped query string from dict and params
    querystr = {'action': 'chart', 'type': 'pagesize'}
    querystr = wikiutil.makeQueryString(querystr)
    querystr = wikiutil.escape(querystr)
    if params:
        querystr += '&amp;' + params

    data = {'url': page.url(request, querystr)}
    data.update(request.cfg.chart_options)
    result = ('<img src="%(url)s" width="%(width)d" height="%(height)d"'
              ' alt="pagesize chart">') % data
    return result


def _slice(data, lo, hi):
    data = data[:]
    if lo: data[:lo] = [None] * lo
    if hi < len(data):
        data[hi:] = [None] * (len(data)-hi)
    return data


def draw(pagename, request):
    import bisect, shutil, cStringIO
    from MoinMoin.stats.chart import Chart, ChartData, Color

    _ = request.getText
    style = Chart.GDC_3DBAR

    # get data
    pages = request.rootpage.getPageDict()
    sizes = []
    for name, page in pages.items():
        sizes.append((page.size(), name.encode('iso-8859-1', 'replace')) ) # gdchart does no utf-8
    sizes.sort()

    upper_bound = sizes[-1][0]
    bounds = [s*128 for s in range(1, 9)]
    if upper_bound >= 1024:
        bounds.extend([s*1024 for s in range(2, 9)])
    if upper_bound >= 8192:
        bounds.extend([s*8192 for s in range(2, 9)])
    if upper_bound >= 65536:
        bounds.extend([s*65536 for s in range(2, 9)])

    data = [None] * len(bounds)
    for size, name in sizes:
        idx = bisect.bisect(bounds, size)
        ##idx = int((size / upper_bound) * classes)
        data[idx] = (data[idx] or 0) + 1

    labels = ["%d" % b for b in bounds]

    # give us a chance to develop this
    if _debug:
        return "<p>data = %s</p>" % \
            '<br>'.join([wikiutil.escape(repr(x)) for x in [labels, data]])

    # create image
    image = cStringIO.StringIO()
    c = Chart()
    ##c.addData(ChartData(data, 'magenta'))
    c.addData(ChartData(_slice(data, 0, 7), 'blue'))
    if upper_bound >= 1024:
        c.addData(ChartData(_slice(data, 7, 14), 'green'))
    if upper_bound >= 8192:
        c.addData(ChartData(_slice(data, 14, 21), 'red'))
    if upper_bound >= 65536:
        c.addData(ChartData(_slice(data, 21, 28), 'magenta'))
    title = ''
    if request.cfg.sitename: title = "%s: " % request.cfg.sitename
    title = title + _('Page Size Distribution')
    c.option(
        annotation=(bisect.bisect(bounds, upper_bound), Color('black'), "%d %s" % sizes[-1]),
        title=title.encode('iso-8859-1', 'replace'), # gdchart can't do utf-8
        xtitle=_('page size upper bound [bytes]').encode('iso-8859-1', 'replace'),
        ytitle=_('# of pages of this size').encode('iso-8859-1', 'replace'),
        title_font=c.GDC_GIANT,
        threed_depth=2.0,
        requested_yinterval=1.0,
        stack_type=c.GDC_STACK_LAYER,
    )
    c.draw(style,
        (request.cfg.chart_options['width'], request.cfg.chart_options['height']),
        image, labels)

    headers = [
        "Content-Type: image/gif",
        "Content-Length: %d" % len(image.getvalue()),
    ]
    request.emit_http_headers(headers)

    # copy the image
    image.reset()
    shutil.copyfileobj(image, request, 8192)

