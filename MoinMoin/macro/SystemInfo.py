# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - SystemInfo Macro

    This macro shows some info about your wiki, wiki software and your system.

    @copyright: 2006 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

Dependencies = ['pages']

import operator, sys, os
from StringIO import StringIO

from MoinMoin import wikiutil, version
from MoinMoin import action, macro, parser
from MoinMoin.logfile import editlog, eventlog
from MoinMoin.Page import Page

def execute(Macro, args):
    """ show SystemInfo: wiki infos, wiki sw version, space usage infos """
    def _formatInReadableUnits(size):
        size = float(size)
        unit = u' Byte'
        if size > 9999:
            unit = u' KiB'
            size /= 1024
        if size > 9999:
            unit = u' MiB'
            size /= 1024
        if size > 9999:
            unit = u' GiB'
            size /= 1024
        return u"%.1f %s" % (size, unit)

    def _getDirectorySize(path):
        try:
            dirsize = 0
            for root, dirs, files in os.walk(path):
                dirsize += sum([os.path.getsize(os.path.join(root, name)) for name in files])
        except EnvironmentError, e:
            dirsize = -1
        return dirsize

    _ = Macro._
    request = Macro.request

    # check for 4XSLT
    try:
        import Ft
        ftversion = Ft.__version__
    except ImportError:
        ftversion = None
    except AttributeError:
        ftversion = 'N/A'

    t_count = None
    try:
        from threading import activeCount
        t_count = activeCount()
    except ImportError:
        pass

    # Get the full pagelist in the wiki
    pagelist = request.rootpage.getPageList(user='')
    totalsize = reduce(operator.add, [Page(request, name).size()
                                      for name in pagelist])

    buf = StringIO()
    row = lambda label, value, buf=buf: buf.write(
        u'<dt>%s</dt><dd>%s</dd>' % (label, value))

    buf.write(u'<dl>')
    row(_('Python Version'), sys.version)
    row(_('MoinMoin Version'), _('Release %s [Revision %s]') % (version.release, version.revision))
    if ftversion:
        row(_('4Suite Version'), ftversion)

    systemPages = [page for page in pagelist
                   if wikiutil.isSystemPage(request, page)]
    row(_('Number of pages'), str(len(pagelist)-len(systemPages)))
    row(_('Number of system pages'), str(len(systemPages)))

    row(_('Accumulated page sizes'), _formatInReadableUnits(totalsize))
    data_dir = request.cfg.data_dir
    row(_('Disk usage of %(data_dir)s/pages/') % {'data_dir': data_dir},
        _formatInReadableUnits(_getDirectorySize(os.path.join(data_dir, 'pages'))))
    row(_('Disk usage of %(data_dir)s/') % {'data_dir': data_dir},
        _formatInReadableUnits(_getDirectorySize(data_dir)))

    edlog = editlog.EditLog(request)
    row(_('Entries in edit log'), "%s (%s)" % (edlog.lines(), _formatInReadableUnits(edlog.size())))

    # This puts a heavy load on the server when the log is large
    eventlogger = eventlog.EventLog(request)
    nonestr = _("NONE")
    row('Event log', _formatInReadableUnits(eventlogger.size()))

    row(_('Global extension macros'), ', '.join(macro.modules) or nonestr)
    row(_('Local extension macros'),
        ', '.join(wikiutil.wikiPlugins('macro', Macro.cfg)) or nonestr)

    glob_actions = [x for x in action.modules
                    if not x in request.cfg.actions_excluded]
    row(_('Global extension actions'), ', '.join(glob_actions) or nonestr)
    loc_actions = [x for x in wikiutil.wikiPlugins('action', Macro.cfg)
                   if not x in request.cfg.actions_excluded]
    row(_('Local extension actions'), ', '.join(loc_actions) or nonestr)

    row(_('Global parsers'), ', '.join(parser.modules) or nonestr)
    row(_('Local extension parsers'),
        ', '.join(wikiutil.wikiPlugins('parser', Macro.cfg)) or nonestr)

    from MoinMoin.search.builtin import Search
    xapState = (_('Disabled'), _('Enabled'))
    idxState = (_('index available'), _('index unavailable'))
    xapRow = xapState[request.cfg.xapian_search]

    if request.cfg.xapian_search:
        idx = Search._xapianIndex(request)
        available = idx and idxState[0] or idxState[1]
        mtime = _('last modified: %s') % (idx and
                request.user.getFormattedDateTime(
                    wikiutil.version2timestamp(idx.mtime())) or
                    _('N/A'))
        xapRow += ', %s, %s' % (available, mtime)

        import xapian
        xapVersion = xapian.xapian_version_string()
    else:
        xapVersion = _('not installed')

    row(_('Xapian search'), xapRow)
    row(_('Xapian Version'), xapVersion)
    row(_('Xapian stemming'), xapState[request.cfg.xapian_stemming])

    row(_('Active threads'), t_count or _('N/A'))
    buf.write(u'</dl>')

    return Macro.formatter.rawHTML(buf.getvalue())

