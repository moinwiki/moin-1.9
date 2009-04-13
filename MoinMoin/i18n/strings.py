# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - lists of translateable strings

    MoinMoin uses some translateable strings that do not appear at other
    places in the source code (and thus, are not found by gettext when
    extracting translateable strings).
    Also, some strings need to be organized somehow.

    @copyright: 2009 MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

_ = lambda x: x # dummy translation function

# TODO: check lists against SystemPagesInEnglishGroup

essential_system_pages = [
    _('FrontPage'),
    _('RecentChanges'),
    _('TitleIndex'),
    _('WordIndex'),
    _('FindPage'),
    _('SiteNavigation'),
    _('HelpContents'),
    _('HelpOnFormatting'),
    _('WikiLicense'),
    _('MissingPage'),
    _('MissingHomePage'),
]

optional_system_pages = [
]

system_pages = essential_system_pages + optional_system_pages

# we use Sun at index 0 and 7 to be compatible with EU/US day indexing scheme,
# like it is also done by crontab entries etc.
weekdays = [_('Sun'), _('Mon'), _('Tue'), _('Wed'), _('Thu'), _('Fri'), _('Sat'), _('Sun')]

actions = [
    _('AttachFile'),
    _('DeletePage'),
    _('LikePages'),
    _('LocalSiteMap'),
    _('RenamePage'),
    _('SpellCheck'),
]

misc = [
    # the editbar link text of the default supplementation page link:
    _('Discussion'),
]

del _ # delete the dummy translation function

