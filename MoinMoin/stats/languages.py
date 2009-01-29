# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Language Statistics

    @copyright: 2002-2004 Juergen Hermann <jh@web.de>,  # Part of the code is
                2007 MoinMoin:ThomasWaldmann,           # from useragents.py
                2007 Nina Kuisma <ninnnu@gmail.com>
    @license: GNU GPL, see COPYING for details.
"""


from MoinMoin import user, i18n


def linkto(pagename, request, params=''):
    return used_languages(request)


def get_data(request):
    _ = request.getText
    data = {}

    users = user.getUserList(request)
    for userID in users:
        current_user = user.User(request, userID)
        if current_user.language == u'':
            # User is using <Browser setting>, attempting to look up if we've managed to store the real language...
            try:
                data[current_user.real_language] = data.get(current_user.real_language, 0) + 1
            except AttributeError: # Couldn't find the used language at all...
                data[u''] = data.get(u'', 0) + 1
        else:
            data[current_user.language] = data.get(current_user.language, 0) + 1
    if u'' in data:
        data[u'browser'] = data.pop(u'') # In case we have users whose languages aren't detectable.
    data = [(cnt, current_user_language) for current_user_language, cnt in data.items()]
    data.sort()
    data.reverse()
    return data


def used_languages(request):
    from MoinMoin.util.dataset import TupleDataset, Column
    from MoinMoin.widget.browser import DataBrowserWidget

    _ = request.getText

    data = get_data(request)

    total = 0.0
    for cnt, lang in data:
        total += cnt


    languages = TupleDataset()
    languages.columns = [Column('language', label=_("Language"), align='left'),
                         Column('value', label='%', align='right')]

    cnt_printed = 0
    data = data[:10]

    # Preparing "<Browser setting>"
    browserlang = _('<Browser setting>')
    browserlang = browserlang[1:len(browserlang) - 1].capitalize()
    if total:
        for cnt, lang in data:
            try:
                if lang == u'browser':
                    languages.addRow((browserlang, "%(percent).2f%% (%(count)d)" % {
                        'percent': 100.0 * cnt / total,
                        'count': cnt}))
                else:
                    lang = i18n.wikiLanguages()[lang]['x-language-in-english']
                    languages.addRow((lang, "%(percent).2f%% (%(count)d)" % {
                        'percent': 100.0 * cnt / total,
                        'count': cnt}))
                cnt_printed += cnt
            except UnicodeError:
                pass
        if total > cnt_printed:
            languages.addRow((_('Others'), "%(percent).2f%% (%(count)d)" % {
                'percent': 100.0 * (total - cnt_printed) / total,
                'count': total - cnt_printed}))

    else: # If we don't have any users, we can safely assume that the only real user is the visitor (who is normally ignored, though) who is using "Browser setting"
        languages.addRow((browserlang, "100% (1)"))

    table = DataBrowserWidget(request)
    table.setData(languages)
    return table.render(method="GET")

