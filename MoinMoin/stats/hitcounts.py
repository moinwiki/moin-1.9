# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Hitcount Statistics

    This macro creates a hitcount chart from the data in "event.log".

    TODO: refactor to use a class, this code is ugly.
          A lot of code here is duplicated in stats.useragents.
          Maybe both can use same base class, maybe some parts are useful to other code.

    @copyright: 2002-2004 Juergen Hermann <jh@web.de>,
                2007 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

_debug = 0

import time

from MoinMoin import caching, wikiutil, logfile
from MoinMoin.Page import Page
from MoinMoin.logfile import eventlog

# this is a CONSTANT used for on-disk caching, it must NOT be configurable and
# not depend on request.user!
DATE_FMT = '%04d-%02d-%02d' # % (y, m, d)

def linkto(pagename, request, params=''):
    _ = request.getText

    if not request.cfg.chart_options:
        return text(pagename, request, params)

    if _debug:
        return draw(pagename, request)

    page = Page(request, pagename)

    # Create escaped query string from dict and params
    querystr = {'action': 'chart', 'type': 'hitcounts'}
    querystr = wikiutil.makeQueryString(querystr)
    querystr = wikiutil.escape(querystr)
    if params:
        querystr += '&amp;' + params

    data = {'url': page.url(request, querystr)}
    data.update(request.cfg.chart_options)
    result = ('<img src="%(url)s" width="%(width)d" height="%(height)d"'
              ' alt="hitcounts chart">') % data

    return result


def get_data(pagename, request, filterpage=None):
    cache_days, cache_views, cache_edits = [], [], []
    cache_date = 0

    # Get results from cache
    if filterpage:
        arena = Page(request, pagename)
        cache = caching.CacheEntry(request, arena, 'hitcounts', scope='item', use_pickle=True)
    else:
        arena = 'charts'
        cache = caching.CacheEntry(request, arena, 'hitcounts', scope='wiki', use_pickle=True)

    if cache.exists():
        try:
            cache_date, cache_days, cache_views, cache_edits = cache.content()
        except:
            cache.remove() # cache gone bad

    # Get new results from the log
    log = eventlog.EventLog(request)
    try:
        new_date = log.date()
    except logfile.LogMissing:
        new_date = None

    # prepare data
    days = []
    views = []
    edits = []
    ratchet_day = None
    ratchet_time = None
    if new_date is not None:
        log.set_filter(['VIEWPAGE', 'SAVEPAGE'])
        latest = None
        for event in log.reverse():
            # don't use event_log.date()
            if latest is None:
                latest = event[0]
            event_usecs = event[0]
            if event_usecs <= cache_date:
                break
            eventpage = event[2].get('pagename', '')
            if filterpage and eventpage != filterpage:
                continue
            event_secs = wikiutil.version2timestamp(event_usecs)
            time_tuple = time.gmtime(event_secs) # must be UTC
            day = tuple(time_tuple[0:3])
            if day != ratchet_day:
                # new day
                while ratchet_time:
                    ratchet_time -= 86400 # seconds per day
                    rday = tuple(time.gmtime(ratchet_time)[0:3]) # must be UTC
                    if rday <= day:
                        break
                    days.append(DATE_FMT % rday)
                    views.append(0)
                    edits.append(0)
                days.append(DATE_FMT % day)
                views.append(0)
                edits.append(0)
                ratchet_day = day
                ratchet_time = event_secs
            if event[1] == 'VIEWPAGE':
                views[-1] += 1
            elif event[1] == 'SAVEPAGE':
                edits[-1] += 1

        days.reverse()
        views.reverse()
        edits.reverse()

    # merge the day on the end of the cache
    if cache_days and days and days[0] == cache_days[-1]:
        cache_edits[-1] += edits[0]
        cache_views[-1] += views[0]
        days, views, edits = days[1:], views[1:], edits[1:]

    # Update and save the cache
    cache_days.extend(days)
    cache_views.extend(views)
    cache_edits.extend(edits)
    if new_date is not None:
        cache.update((latest, cache_days, cache_views, cache_edits))

    return cache_days, cache_views, cache_edits


def text(pagename, request, params=''):
    from MoinMoin.util.dataset import TupleDataset, Column
    from MoinMoin.widget.browser import DataBrowserWidget
    _ = request.getText

    # check params
    filterpage = None
    if params.startswith('page='):
        params = params[len('page='):]
        params = wikiutil.url_unquote(params, want_unicode=False)
        filterpage = wikiutil.decodeUserInput(params)

    if request and request.form and 'page' in request.form:
        filterpage = request.form['page'][0]

    days, views, edits = get_data(pagename, request, filterpage)

    hits = TupleDataset()
    hits.columns = [Column('day', label=_("Date"), align='left'),
                    Column('views', label=_("Views/day"), align='right'),
                    Column('edits', label=_("Edits/day"), align='right'),
                    ]

    maxentries = 30

    if maxentries < len(days):
        step = float(len(days))/ maxentries
    else:
        step = 1

    sv = 0.0
    se = 0.0
    sd = 0.0
    cnt = 0

    for i in xrange(len(days)-1, -1, -1):
        d, v, e = days[i], views[i], edits[i]
        # sum up views and edits to step days
        sd += 1
        cnt += 1
        sv += v
        se += e
        if cnt >= step:
            cnt -= step
            hits.addRow((d, "%.1f" % (sv/sd), "%.1f" % (se/sd)))
            sv = 0.0
            se = 0.0
            sd = 0.0

    table = DataBrowserWidget(request)
    table.setData(hits)
    return table.render(method="GET")


def draw(pagename, request):
    import shutil, cStringIO
    from MoinMoin.stats.chart import Chart, ChartData, Color

    _ = request.getText

    # check params
    filterpage = None
    if request and request.form and 'page' in request.form:
        filterpage = request.form['page'][0]

    days, views, edits = get_data(pagename, request, filterpage)

    import math

    try:
        scalefactor = float(max(views))/max(edits)
    except (ZeroDivisionError, ValueError):
        scalefactor = 1.0
    else:
        scalefactor = int(10 ** math.floor(math.log10(scalefactor)))

    # scale edits up
    edits = [x * scalefactor for x in edits]

    # create image
    image = cStringIO.StringIO()
    c = Chart()
    c.addData(ChartData(views, color='green'))
    c.addData(ChartData(edits, color='red'))
    chart_title = ''
    if request.cfg.sitename:
        chart_title = "%s: " % request.cfg.sitename
    chart_title = chart_title + _('Page hits and edits')
    if filterpage:
        chart_title = _("%(chart_title)s for %(filterpage)s") % {
            'chart_title': chart_title,
            'filterpage': filterpage,
        }
    chart_title = "%s\n%sx%d" % (chart_title, _("green=view\nred=edit"), scalefactor)
    c.option(
        title=chart_title.encode('iso-8859-1', 'replace'), # gdchart can't do utf-8
        xtitle=(_('date') + ' (Server)').encode('iso-8859-1', 'replace'),
        ytitle=_('# of hits').encode('iso-8859-1', 'replace'),
        title_font=c.GDC_GIANT,
        #thumblabel = 'THUMB', thumbnail = 1, thumbval = 10,
        #ytitle_color = Color('green'),
        #yaxis2 = 1,
        #ytitle2 = '# of edits',
        #ytitle2_color = Color('red'),
        #ylabel2_color = Color('black'),
        #interpolations = 0,
        threed_depth=1.0,
        requested_yinterval=1.0,
        stack_type=c.GDC_STACK_BESIDE
    )
    c.draw(c.GDC_LINE,
        (request.cfg.chart_options['width'], request.cfg.chart_options['height']),
        image, days)

    headers = [
        "Content-Type: image/gif",
        "Content-Length: %d" % len(image.getvalue()),
    ]
    request.emit_http_headers(headers)

    # copy the image
    image.reset()
    shutil.copyfileobj(image, request, 8192)

