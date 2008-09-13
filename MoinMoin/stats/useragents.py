# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - User-Agent Statistics

    This macro creates a pie chart of the type of user agents
    accessing the wiki.

    TODO: should be refactored after hitcounts.

    @copyright: 2002-2004 Juergen Hermann <jh@web.de>,
                2007 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

_debug = 0

from MoinMoin import wikiutil, caching, logfile
from MoinMoin.Page import Page
from MoinMoin.logfile import eventlog


def linkto(pagename, request, params=''):
    _ = request.getText

    if not request.cfg.chart_options:
        return text(pagename, request)
    if _debug:
        return draw(pagename, request)

    page = Page(request, pagename)

    # Create escaped query string from dict and params
    querystr = {'action': 'chart', 'type': 'useragents'}
    querystr = wikiutil.makeQueryString(querystr)
    querystr = wikiutil.escape(querystr)
    if params:
        querystr += '&amp;' + params

    data = {'url': page.url(request, querystr)}
    data.update(request.cfg.chart_options)
    result = ('<img src="%(url)s" width="%(width)d" height="%(height)d"'
              ' alt="useragents chart">') % data

    return result


def get_data(request):
    # get results from cache
    cache = caching.CacheEntry(request, 'charts', 'useragents', scope='wiki', use_pickle=True)
    cache_date, data = 0, {}
    if cache.exists():
        try:
            cache_date, data = cache.content()
        except:
            cache.remove() # cache gone bad

    log = eventlog.EventLog(request)
    try:
        new_date = log.date()
    except logfile.LogMissing:
        new_date = None

    if new_date is not None:
        log.set_filter(['VIEWPAGE', 'SAVEPAGE'])
        for event in log.reverse():
            if event[0] <= cache_date:
                break
            ua = event[2].get('HTTP_USER_AGENT')
            if ua:
                try:
                    pos = ua.index(" (compatible; ")
                    ua = ua[pos:].split(';')[1].strip()
                except ValueError:
                    ua = ua.split()[0]
                #ua = ua.replace(';', '\n')
                data[ua] = data.get(ua, 0) + 1

        # write results to cache
        cache.update((new_date, data))

    data = [(cnt, ua) for ua, cnt in data.items()]
    data.sort()
    data.reverse()
    return data

def text(pagename, request):
    from MoinMoin.util.dataset import TupleDataset, Column
    from MoinMoin.widget.browser import DataBrowserWidget

    _ = request.getText

    data = get_data(request)

    total = 0.0
    for cnt, ua in data:
        total += cnt


    agents = TupleDataset()
    agents.columns = [Column('agent', label=_("User agent"), align='left'),
                      Column('value', label='%', align='right')]

    cnt_printed = 0
    data = data[:10]

    if total:
        for cnt, ua in data:
            try:
                ua = unicode(ua)
                agents.addRow((ua, "%.2f" % (100.0 * cnt / total)))
                cnt_printed += cnt
            except UnicodeError:
                pass
        if total > cnt_printed:
            agents.addRow((_('Others'), "%.2f" % (100 * (total - cnt_printed) / total)))

    table = DataBrowserWidget(request)
    table.setData(agents)
    return table.render(method="GET")

def draw(pagename, request):
    import shutil, cStringIO
    from MoinMoin.stats.chart import Chart, ChartData, Color

    _ = request.getText

    style = Chart.GDC_3DPIE

    # get data
    colors = ['red', 'mediumblue', 'yellow', 'deeppink', 'aquamarine', 'purple', 'beige',
              'blue', 'forestgreen', 'orange', 'cyan', 'fuchsia', 'lime']
    colors = ([Color(c) for c in colors])

    data = get_data(request)

    maxdata = len(colors) - 1
    if len(data) > maxdata:
        others = [x[0] for x in data[maxdata:]]
        data = data[:maxdata] + [(sum(others), _('Others').encode('iso-8859-1', 'replace'))] # gdchart can't do utf-8

    # shift front to end if others is very small
    if data[-1][0] * 10 < data[0][0]:
        data = data[1:] + data[0:1]

    labels = [x[1] for x in data]
    data = [x[0] for x in data]

    # give us a chance to develop this
    if _debug:
        return "<p>data = %s</p>" % \
            '<br>'.join([wikiutil.escape(repr(x)) for x in [labels, data]])

    # create image
    image = cStringIO.StringIO()
    c = Chart()
    c.addData(data)

    title = ''
    if request.cfg.sitename: title = "%s: " % request.cfg.sitename
    title = title + _('Distribution of User-Agent Types')
    c.option(
        pie_color=colors,
        label_font=Chart.GDC_SMALL,
        label_line=1,
        label_dist=20,
        threed_depth=20,
        threed_angle=225,
        percent_labels=Chart.GDCPIE_PCT_RIGHT,
        title_font=c.GDC_GIANT,
        title=title.encode('iso-8859-1', 'replace')) # gdchart can't do utf-8
    labels = [label.encode('iso-8859-1', 'replace') for label in labels]
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

