#!/usr/bin/env python

"""
parsedatetime constants and helper functions to determine
regex values from Locale information if present.

Also contains the internal Locale classes to give some sane
defaults if PyICU is not found.
"""

__license__ = """
Copyright (c) 2004-2008 Mike Taylor
Copyright (c) 2006-2008 Darshana Chhajed
Copyright (c)      2007 Bernd Zeimetz <bzed@debian.org>
All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

try:
    import PyICU as pyicu
except:
    pyicu = None


import datetime
import calendar
import time
import re


class pdtLocale_en:
    """
    en_US Locale constants

    This class will be used to initialize L{Constants} if PyICU is not located.

    Defined as class variables are the lists and strings needed by parsedatetime
    to evaluate strings for USA
    """

    localeID      = 'en_US'   # don't use a unicode string
    dateSep       = [ u'/', u'.' ]
    timeSep       = [ u':' ]
    meridian      = [ u'AM', u'PM' ]
    usesMeridian  = True
    uses24        = False

    Weekdays      = [ u'monday', u'tuesday', u'wednesday',
                      u'thursday', u'friday', u'saturday', u'sunday',
                    ]
    shortWeekdays = [ u'mon', u'tues', u'wed',
                      u'thu', u'fri', u'sat', u'sun',
                    ]
    Months        = [ u'january', u'february', u'march',
                      u'april',   u'may',      u'june',
                      u'july',    u'august',   u'september',
                      u'october', u'november', u'december',
                    ]
    shortMonths   = [ u'jan', u'feb', u'mar',
                      u'apr', u'may', u'jun',
                      u'jul', u'aug', u'sep',
                      u'oct', u'nov', u'dec',
                    ]
    dateFormats   = { 'full':   'EEEE, MMMM d, yyyy',
                      'long':   'MMMM d, yyyy',
                      'medium': 'MMM d, yyyy',
                      'short':  'M/d/yy',
                    }
    timeFormats   = { 'full':   'h:mm:ss a z',
                      'long':   'h:mm:ss a z',
                      'medium': 'h:mm:ss a',
                      'short':  'h:mm a',
                    }

    dp_order = [ u'm', u'd', u'y' ]

      # this will be added to re_consts later
    units = { 'seconds': [ 'second', 'sec' ],
              'minutes': [ 'minute', 'min' ],
              'hours':   [ 'hour',   'hr'  ],
              'days':    [ 'day',    'dy'  ],
              'weeks':   [ 'week',   'wk'  ],
              'months':  [ 'month',  'mth' ],
              'years':   [ 'year',   'yr'  ],
            }

      # text constants to be used by regex's later
    re_consts     = { 'specials':       'in|on|of|at',
                      'timeseperator':  ':',
                      'rangeseperator': '-',
                      'daysuffix':      'rd|st|nd|th',
                      'meridian':       'am|pm|a.m.|p.m.|a|p',
                      'qunits':         'h|m|s|d|w|m|y',
                      'now':            [ 'now' ],
                    }

      # Used to adjust the returned date before/after the source
    modifiers = { 'from':       1,
                  'before':    -1,
                  'after':      1,
                  'ago':       -1,
                  'prior':     -1,
                  'prev':      -1,
                  'last':      -1,
                  'next':       1,
                  'previous':  -1,
                  'in a':       2,
                  'end of':     0,
                  'eod':        0,
                  'eo':         0
                }

    dayoffsets = { 'tomorrow':   1,
                   'today':      0,
                   'yesterday': -1,
                 }

      # special day and/or times, i.e. lunch, noon, evening
      # each element in the dictionary is a dictionary that is used
      # to fill in any value to be replace - the current date/time will
      # already have been populated by the method buildSources
    re_sources    = { 'noon':      { 'hr': 12, 'mn': 0, 'sec': 0 },
                      'lunch':     { 'hr': 12, 'mn': 0, 'sec': 0 },
                      'morning':   { 'hr':  6, 'mn': 0, 'sec': 0 },
                      'breakfast': { 'hr':  8, 'mn': 0, 'sec': 0 },
                      'dinner':    { 'hr': 19, 'mn': 0, 'sec': 0 },
                      'evening':   { 'hr': 18, 'mn': 0, 'sec': 0 },
                      'midnight':  { 'hr':  0, 'mn': 0, 'sec': 0 },
                      'night':     { 'hr': 21, 'mn': 0, 'sec': 0 },
                      'tonight':   { 'hr': 21, 'mn': 0, 'sec': 0 },
                      'eod':       { 'hr': 17, 'mn': 0, 'sec': 0 },
                    }


class pdtLocale_au:
    """
    en_AU Locale constants

    This class will be used to initialize L{Constants} if PyICU is not located.

    Defined as class variables are the lists and strings needed by parsedatetime
    to evaluate strings for Australia
    """

    localeID      = 'en_AU'   # don't use a unicode string
    dateSep       = [ u'-', u'/' ]
    timeSep       = [ u':' ]
    meridian      = [ u'AM', u'PM' ]
    usesMeridian  = True
    uses24        = False

    Weekdays      = [ u'monday', u'tuesday', u'wednesday',
                      u'thursday', u'friday', u'saturday', u'sunday',
                    ]
    shortWeekdays = [ u'mon', u'tues', u'wed',
                      u'thu', u'fri', u'sat', u'sun',
                    ]
    Months        = [ u'january', u'february', u'march',
                      u'april',   u'may',      u'june',
                      u'july',    u'august',   u'september',
                      u'october', u'november', u'december',
                    ]
    shortMonths   = [ u'jan', u'feb', u'mar',
                      u'apr', u'may', u'jun',
                      u'jul', u'aug', u'sep',
                      u'oct', u'nov', u'dec',
                    ]
    dateFormats   = { 'full':   'EEEE, d MMMM yyyy',
                      'long':   'd MMMM yyyy',
                      'medium': 'dd/MM/yyyy',
                      'short':  'd/MM/yy',
                    }
    timeFormats   = { 'full':   'h:mm:ss a z',
                      'long':   'h:mm:ss a',
                      'medium': 'h:mm:ss a',
                      'short':  'h:mm a',
                    }

    dp_order = [ u'd', u'm', u'y' ]

      # this will be added to re_consts later
    units = { 'seconds': [ 'second', 'sec' ],
              'minutes': [ 'minute', 'min' ],
              'hours':   [ 'hour',   'hr'  ],
              'days':    [ 'day',    'dy'  ],
              'weeks':   [ 'week',   'wk'  ],
              'months':  [ 'month',  'mth' ],
              'years':   [ 'year',   'yr'  ],
            }

      # text constants to be used by regex's later
    re_consts     = { 'specials':       'in|on|of|at',
                      'timeseperator':  ':',
                      'rangeseperator': '-',
                      'daysuffix':      'rd|st|nd|th',
                      'meridian':       'am|pm|a.m.|p.m.|a|p',
                      'qunits':         'h|m|s|d|w|m|y',
                      'now':            [ 'now' ],
                    }

      # Used to adjust the returned date before/after the source
    modifiers = { 'from':       1,
                  'before':    -1,
                  'after':      1,
                  'ago':        1,
                  'prior':     -1,
                  'prev':      -1,
                  'last':      -1,
                  'next':       1,
                  'previous':  -1,
                  'in a':       2,
                  'end of':     0,
                  'eo':         0,
                }

    dayoffsets = { 'tomorrow':   1,
                   'today':      0,
                   'yesterday': -1,
                 }

      # special day and/or times, i.e. lunch, noon, evening
      # each element in the dictionary is a dictionary that is used
      # to fill in any value to be replace - the current date/time will
      # already have been populated by the method buildSources
    re_sources    = { 'noon':      { 'hr': 12, 'mn': 0, 'sec': 0 },
                      'lunch':     { 'hr': 12, 'mn': 0, 'sec': 0 },
                      'morning':   { 'hr':  6, 'mn': 0, 'sec': 0 },
                      'breakfast': { 'hr':  8, 'mn': 0, 'sec': 0 },
                      'dinner':    { 'hr': 19, 'mn': 0, 'sec': 0 },
                      'evening':   { 'hr': 18, 'mn': 0, 'sec': 0 },
                      'midnight':  { 'hr':  0, 'mn': 0, 'sec': 0 },
                      'night':     { 'hr': 21, 'mn': 0, 'sec': 0 },
                      'tonight':   { 'hr': 21, 'mn': 0, 'sec': 0 },
                      'eod':       { 'hr': 17, 'mn': 0, 'sec': 0 },
                    }


class pdtLocale_es:
    """
    es Locale constants

    This class will be used to initialize L{Constants} if PyICU is not located.

    Defined as class variables are the lists and strings needed by parsedatetime
    to evaluate strings in Spanish

    Note that I don't speak Spanish so many of the items below are still in English
    """

    localeID      = 'es'   # don't use a unicode string
    dateSep       = [ u'/' ]
    timeSep       = [ u':' ]
    meridian      = []
    usesMeridian  = False
    uses24        = True

    Weekdays      = [ u'lunes', u'martes', u'mi\xe9rcoles',
                      u'jueves', u'viernes', u's\xe1bado', u'domingo',
                    ]
    shortWeekdays = [ u'lun', u'mar', u'mi\xe9',
                      u'jue', u'vie', u's\xe1b', u'dom',
                    ]
    Months        = [ u'enero', u'febrero', u'marzo',
                      u'abril', u'mayo', u'junio',
                      u'julio', u'agosto', u'septiembre',
                      u'octubre', u'noviembre', u'diciembre'
                    ]
    shortMonths   = [ u'ene', u'feb', u'mar',
                      u'abr', u'may', u'jun',
                      u'jul', u'ago', u'sep',
                      u'oct', u'nov', u'dic'
                    ]
    dateFormats   = { 'full':   "EEEE d' de 'MMMM' de 'yyyy",
                      'long':   "d' de 'MMMM' de 'yyyy",
                      'medium': "dd-MMM-yy",
                      'short':  "d/MM/yy",
                    }
    timeFormats   = { 'full':   "HH'H'mm' 'ss z",
                      'long':   "HH:mm:ss z",
                      'medium': "HH:mm:ss",
                      'short':  "HH:mm",
                    }

    dp_order = [ u'd', u'm', u'y' ]

      # this will be added to re_consts later
    units = { 'seconds': [ 'second', 'sec' ],
              'minutes': [ 'minute', 'min' ],
              'hours':   [ 'hour',   'hr'  ],
              'days':    [ 'day',    'dy'  ],
              'weeks':   [ 'week',   'wk'  ],
              'months':  [ 'month',  'mth' ],
              'years':   [ 'year',   'yr'  ],
            }

      # text constants to be used by regex's later
    re_consts     = { 'specials':       'in|on|of|at',
                      'timeseperator':  timeSep,
                      'dateseperator':  dateSep,
                      'rangeseperator': '-',
                      'daysuffix':      'rd|st|nd|th',
                      'qunits':         'h|m|s|d|w|m|y',
                      'now':            [ 'now' ],
                    }

      # Used to adjust the returned date before/after the source
    modifiers = { 'from':      1,
                  'before':   -1,
                  'after':     1,
                  'ago':       1,
                  'prior':    -1,
                  'prev':     -1,
                  'last':     -1,
                  'next':      1,
                  'previous': -1,
                  'in a':      2,
                  'end of':    0,
                  'eo':        0,
                }

    dayoffsets = { 'tomorrow':   1,
                   'today':      0,
                   'yesterday': -1,
                 }

      # special day and/or times, i.e. lunch, noon, evening
      # each element in the dictionary is a dictionary that is used
      # to fill in any value to be replace - the current date/time will
      # already have been populated by the method buildSources
    re_sources    = { 'noon':      { 'hr': 12, 'mn': 0, 'sec': 0 },
                      'lunch':     { 'hr': 12, 'mn': 0, 'sec': 0 },
                      'morning':   { 'hr':  6, 'mn': 0, 'sec': 0 },
                      'breakfast': { 'hr':  8, 'mn': 0, 'sec': 0 },
                      'dinner':    { 'hr': 19, 'mn': 0, 'sec': 0 },
                      'evening':   { 'hr': 18, 'mn': 0, 'sec': 0 },
                      'midnight':  { 'hr':  0, 'mn': 0, 'sec': 0 },
                      'night':     { 'hr': 21, 'mn': 0, 'sec': 0 },
                      'tonight':   { 'hr': 21, 'mn': 0, 'sec': 0 },
                      'eod':       { 'hr': 17, 'mn': 0, 'sec': 0 },
                    }


class pdtLocale_de:
    """
    de_DE Locale constants

    This class will be used to initialize L{Constants} if PyICU is not located.

    Contributed by Debian parsedatetime package maintainer Bernd Zeimetz <bzed@debian.org>

    Defined as class variables are the lists and strings needed by parsedatetime
    to evaluate strings for German
    """

    localeID      = 'de_DE'   # don't use a unicode string
    dateSep       = [ u'.' ]
    timeSep       = [ u':' ]
    meridian      = [ ]
    usesMeridian  = False
    uses24        = True

    Weekdays      = [ u'montag', u'dienstag', u'mittwoch',
                      u'donnerstag', u'freitag', u'samstag', u'sonntag',
                    ]
    shortWeekdays = [ u'mo', u'di', u'mi',
                      u'do', u'fr', u'sa', u'so',
                    ]
    Months        = [ u'januar',  u'februar',  u'm\xe4rz',
                      u'april',   u'mai',      u'juni',
                      u'juli',    u'august',   u'september',
                      u'oktober', u'november', u'dezember',
                    ]
    shortMonths   = [ u'jan', u'feb', u'mrz',
                      u'apr', u'mai', u'jun',
                      u'jul', u'aug', u'sep',
                      u'okt', u'nov', u'dez',
                    ]
    dateFormats   = { 'full':   u'EEEE, d. MMMM yyyy',
                      'long':   u'd. MMMM yyyy',
                      'medium': u'dd.MM.yyyy',
                      'short':  u'dd.MM.yy'
                    }

    timeFormats   = { 'full':   u'HH:mm:ss v',
                      'long':   u'HH:mm:ss z',
                      'medium': u'HH:mm:ss',
                      'short':  u'HH:mm'
                    }

    dp_order = [ u'd', u'm', u'y' ]

      # this will be added to re_consts later
    units = { 'seconds': [ 'sekunden', 'sek',  's' ],
              'minutes': [ 'minuten',  'min' , 'm' ],
              'hours':   [ 'stunden',  'std',  'h' ],
              'days':    [ 'tage',     't' ],
              'weeks':   [ 'wochen',   'w' ],
              'months':  [ 'monate' ], #the short version would be a capital M,
                                       #as I understand it we can't distinguis
                                       #between m for minutes and M for months.
              'years':   [ 'jahre',    'j' ],
            }

      # text constants to be used by regex's later
    re_consts     = { 'specials':       'am|dem|der|im|in|den|zum',
                      'timeseperator':  ':',
                      'rangeseperator': '-',
                      'daysuffix':      '',
                      'qunits':         'h|m|s|t|w|m|j',
                      'now':            [ 'jetzt' ],
                    }

      # Used to adjust the returned date before/after the source
      #still looking for insight on how to translate all of them to german.
    modifiers = { u'from':         1,
                  u'before':      -1,
                  u'after':        1,
                  u'vergangener': -1,
                  u'vorheriger':  -1,
                  u'prev':        -1,
                  u'letzter':     -1,
                  u'n\xe4chster':  1,
                  u'dieser':       0,
                  u'previous':    -1,
                  u'in a':         2,
                  u'end of':       0,
                  u'eod':          0,
                  u'eo':           0,
                }

     #morgen/abermorgen does not work, see http://code.google.com/p/parsedatetime/issues/detail?id=19
    dayoffsets = { u'morgen':        1,
                   u'heute':         0,
                   u'gestern':      -1,
                   u'vorgestern':   -2,
                   u'\xfcbermorgen': 2,
                 }

      # special day and/or times, i.e. lunch, noon, evening
      # each element in the dictionary is a dictionary that is used
      # to fill in any value to be replace - the current date/time will
      # already have been populated by the method buildSources
    re_sources    = { u'mittag':      { 'hr': 12, 'mn': 0, 'sec': 0 },
                      u'mittags':     { 'hr': 12, 'mn': 0, 'sec': 0 },
                      u'mittagessen': { 'hr': 12, 'mn': 0, 'sec': 0 },
                      u'morgen':      { 'hr':  6, 'mn': 0, 'sec': 0 },
                      u'morgens':     { 'hr':  6, 'mn': 0, 'sec': 0 },
                      u'fr\e4hst\xe4ck': { 'hr':  8, 'mn': 0, 'sec': 0 },
                      u'abendessen':  { 'hr': 19, 'mn': 0, 'sec': 0 },
                      u'abend':       { 'hr': 18, 'mn': 0, 'sec': 0 },
                      u'abends':      { 'hr': 18, 'mn': 0, 'sec': 0 },
                      u'mitternacht': { 'hr':  0, 'mn': 0, 'sec': 0 },
                      u'nacht':       { 'hr': 21, 'mn': 0, 'sec': 0 },
                      u'nachts':      { 'hr': 21, 'mn': 0, 'sec': 0 },
                      u'heute abend': { 'hr': 21, 'mn': 0, 'sec': 0 },
                      u'heute nacht': { 'hr': 21, 'mn': 0, 'sec': 0 },
                      u'feierabend':  { 'hr': 17, 'mn': 0, 'sec': 0 },
                    }


pdtLocales = { 'en_US': pdtLocale_en,
               'en_AU': pdtLocale_au,
               'es_ES': pdtLocale_es,
               'de_DE': pdtLocale_de,
             }


def _initLocale(ptc):
    """
    Helper function to initialize the different lists and strings
    from either PyICU or one of the internal pdt Locales and store
    them into ptc.
    """

    def lcase(x):
        return x.lower()

    if pyicu and ptc.usePyICU:
        ptc.icuLocale = None

        if ptc.localeID is not None:
            ptc.icuLocale = pyicu.Locale(ptc.localeID)

        if ptc.icuLocale is None:
            for id in range(0, len(ptc.fallbackLocales)):
                ptc.localeID  = ptc.fallbackLocales[id]
                ptc.icuLocale = pyicu.Locale(ptc.localeID)

                if ptc.icuLocale is not None:
                    break

        ptc.icuSymbols = pyicu.DateFormatSymbols(ptc.icuLocale)

          # grab ICU list of weekdays, skipping first entry which
          # is always blank
        wd  = map(lcase, ptc.icuSymbols.getWeekdays()[1:])
        swd = map(lcase, ptc.icuSymbols.getShortWeekdays()[1:])

          # store them in our list with Monday first (ICU puts Sunday first)
        ptc.Weekdays      = wd[1:] + wd[0:1]
        ptc.shortWeekdays = swd[1:] + swd[0:1]
        ptc.Months        = map(lcase, ptc.icuSymbols.getMonths())
        ptc.shortMonths   = map(lcase, ptc.icuSymbols.getShortMonths())

          # not quite sure how to init this so for now
          # set it to none so it will be set to the en_US defaults for now
        ptc.re_consts   = None
        ptc.icu_df      = { 'full':   pyicu.DateFormat.createDateInstance(pyicu.DateFormat.kFull,   ptc.icuLocale),
                            'long':   pyicu.DateFormat.createDateInstance(pyicu.DateFormat.kLong,   ptc.icuLocale),
                            'medium': pyicu.DateFormat.createDateInstance(pyicu.DateFormat.kMedium, ptc.icuLocale),
                            'short':  pyicu.DateFormat.createDateInstance(pyicu.DateFormat.kShort,  ptc.icuLocale),
                          }
        ptc.icu_tf      = { 'full':   pyicu.DateFormat.createTimeInstance(pyicu.DateFormat.kFull,   ptc.icuLocale),
                            'long':   pyicu.DateFormat.createTimeInstance(pyicu.DateFormat.kLong,   ptc.icuLocale),
                            'medium': pyicu.DateFormat.createTimeInstance(pyicu.DateFormat.kMedium, ptc.icuLocale),
                            'short':  pyicu.DateFormat.createTimeInstance(pyicu.DateFormat.kShort,  ptc.icuLocale),
                          }
        ptc.dateFormats = { 'full':   ptc.icu_df['full'].toPattern(),
                            'long':   ptc.icu_df['long'].toPattern(),
                            'medium': ptc.icu_df['medium'].toPattern(),
                            'short':  ptc.icu_df['short'].toPattern(),
                          }
        ptc.timeFormats = { 'full':   ptc.icu_tf['full'].toPattern(),
                            'long':   ptc.icu_tf['long'].toPattern(),
                            'medium': ptc.icu_tf['medium'].toPattern(),
                            'short':  ptc.icu_tf['short'].toPattern(),
                          }
    else:
        if not ptc.localeID in pdtLocales:
            for id in range(0, len(ptc.fallbackLocales)):
                ptc.localeID  = ptc.fallbackLocales[id]

                if ptc.localeID in pdtLocales:
                    break

        ptc.locale   = pdtLocales[ptc.localeID]
        ptc.usePyICU = False

        ptc.Weekdays      = ptc.locale.Weekdays
        ptc.shortWeekdays = ptc.locale.shortWeekdays
        ptc.Months        = ptc.locale.Months
        ptc.shortMonths   = ptc.locale.shortMonths
        ptc.dateFormats   = ptc.locale.dateFormats
        ptc.timeFormats   = ptc.locale.timeFormats

      # these values are used to setup the various bits 
      # of the regex values used to parse
      #
      # check if a local set of constants has been
      # provided, if not use en_US as the default
    if ptc.localeID in pdtLocales:
        ptc.re_sources = pdtLocales[ptc.localeID].re_sources
        ptc.re_values  = pdtLocales[ptc.localeID].re_consts

        units = pdtLocales[ptc.localeID].units

        ptc.Modifiers  = pdtLocales[ptc.localeID].modifiers
        ptc.dayOffsets = pdtLocales[ptc.localeID].dayoffsets

          # for now, pull over any missing keys from the US set
        for key in pdtLocales['en_US'].re_consts:
            if not key in ptc.re_values:
                ptc.re_values[key] = pdtLocales['en_US'].re_consts[key]
    else:
        ptc.re_sources = pdtLocales['en_US'].re_sources
        ptc.re_values  = pdtLocales['en_US'].re_consts
        ptc.Modifiers  = pdtLocales['en_US'].modifiers
        ptc.dayOffsets = pdtLocales['en_US'].dayoffsets
        units          = pdtLocales['en_US'].units

      # escape any regex special characters that may be found
    wd   = tuple(map(re.escape, ptc.Weekdays))
    swd  = tuple(map(re.escape, ptc.shortWeekdays))
    mth  = tuple(map(re.escape, ptc.Months))
    smth = tuple(map(re.escape, ptc.shortMonths))

    ptc.re_values['months']      = '%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s' % mth
    ptc.re_values['shortmonths'] = '%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s' % smth
    ptc.re_values['days']        = '%s|%s|%s|%s|%s|%s|%s' % wd
    ptc.re_values['shortdays']   = '%s|%s|%s|%s|%s|%s|%s' % swd

    l = []
    for unit in units:
        l.append('|'.join(units[unit]))

    ptc.re_values['units'] = '|'.join(l)
    ptc.Units              = ptc.re_values['units'].split('|')


def _initSymbols(ptc):
    """
    Helper function to initialize the single character constants
    and other symbols needed.
    """
    ptc.timeSep  = [ u':' ]
    ptc.dateSep  = [ u'/' ]
    ptc.meridian = [ u'AM', u'PM' ]

    ptc.usesMeridian = True
    ptc.uses24       = False

    if pyicu and ptc.usePyICU:
        am = u''
        pm = u''
        ts = ''

        # ICU doesn't seem to provide directly the
        # date or time seperator - so we have to
        # figure it out
        o = ptc.icu_tf['short']
        s = ptc.timeFormats['short']

        ptc.usesMeridian = u'a' in s
        ptc.uses24       = u'H' in s

        # '11:45 AM' or '11:45'
        s = o.format(datetime.datetime(2003, 10, 30, 11, 45))

        # ': AM' or ':'
        s = s.replace('11', '').replace('45', '')

        if len(s) > 0:
            ts = s[0]

        if ptc.usesMeridian:
            # '23:45 AM' or '23:45'
            am = s[1:].strip()
            s  = o.format(datetime.datetime(2003, 10, 30, 23, 45))

            if ptc.uses24:
                s = s.replace('23', '')
            else:
                s = s.replace('11', '')

            # 'PM' or ''
            pm = s.replace('45', '').replace(ts, '').strip()

        ptc.timeSep  = [ ts ]
        ptc.meridian = [ am, pm ]

        o = ptc.icu_df['short']
        s = o.format(datetime.datetime(2003, 10, 30, 11, 45))
        s = s.replace('10', '').replace('30', '').replace('03', '').replace('2003', '')

        if len(s) > 0:
            ds = s[0]
        else:
            ds = '/'

        ptc.dateSep = [ ds ]
        s           = ptc.dateFormats['short']
        l           = s.lower().split(ds)
        dp_order    = []

        for s in l:
            if len(s) > 0:
                dp_order.append(s[:1])

        ptc.dp_order = dp_order
    else:
        ptc.timeSep      = ptc.locale.timeSep
        ptc.dateSep      = ptc.locale.dateSep
        ptc.meridian     = ptc.locale.meridian
        ptc.usesMeridian = ptc.locale.usesMeridian
        ptc.uses24       = ptc.locale.uses24
        ptc.dp_order     = ptc.locale.dp_order

      # build am and pm lists to contain
      # original case, lowercase and first-char
      # versions of the meridian text

    if len(ptc.meridian) > 0:
        am     = ptc.meridian[0]
        ptc.am = [ am ]

        if len(am) > 0:
            ptc.am.append(am[0])
            am = am.lower()
            ptc.am.append(am)
            ptc.am.append(am[0])
    else:
        am     = ''
        ptc.am = [ '', '' ]

    if len(ptc.meridian) > 1:
        pm     = ptc.meridian[1]
        ptc.pm = [ pm ]

        if len(pm) > 0:
            ptc.pm.append(pm[0])
            pm = pm.lower()
            ptc.pm.append(pm)
            ptc.pm.append(pm[0])
    else:
        pm     = ''
        ptc.pm = [ '', '' ]


def _initPatterns(ptc):
    """
    Helper function to take the different localized bits from ptc and
    create the regex strings.
    """
    # TODO add code to parse the date formats and build the regexes up from sub-parts
    # TODO find all hard-coded uses of date/time seperators

    ptc.RE_DATE4     = r'''(?P<date>(((?P<day>\d\d?)(?P<suffix>%(daysuffix)s)?(,)?(\s)?)
                                      (?P<mthname>(%(months)s|%(shortmonths)s))\s?
                                      (?P<year>\d\d(\d\d)?)?
                                    )
                           )''' % ptc.re_values

    # I refactored DATE3 to fix Issue 16 http://code.google.com/p/parsedatetime/issues/detail?id=16
    # I suspect the final line was for a trailing time - but testing shows it's not needed
    # ptc.RE_DATE3     = r'''(?P<date>((?P<mthname>(%(months)s|%(shortmonths)s))\s?
    #                                  ((?P<day>\d\d?)(\s?|%(daysuffix)s|$)+)?
    #                                  (,\s?(?P<year>\d\d(\d\d)?))?))
    #                        (\s?|$|[^0-9a-zA-Z])''' % ptc.re_values
    ptc.RE_DATE3     = r'''(?P<date>(
                                     (((?P<mthname>(%(months)s|%(shortmonths)s))|
                                     ((?P<day>\d\d?)(?P<suffix>%(daysuffix)s)?))(\s)?){1,2}
                                     ((,)?(\s)?(?P<year>\d\d(\d\d)?))?
                                    )
                           )''' % ptc.re_values
    ptc.RE_MONTH     = r'''(\s?|^)
                           (?P<month>(
                                      (?P<mthname>(%(months)s|%(shortmonths)s))
                                      (\s?(?P<year>(\d\d\d\d)))?
                                     ))
                           (\s?|$|[^0-9a-zA-Z])''' % ptc.re_values
    ptc.RE_WEEKDAY   = r'''(\s?|^)
                           (?P<weekday>(%(days)s|%(shortdays)s))
                           (\s?|$|[^0-9a-zA-Z])''' % ptc.re_values

    ptc.RE_SPECIAL   = r'(?P<special>^[%(specials)s]+)\s+' % ptc.re_values
    ptc.RE_UNITS     = r'''(?P<qty>(-?\d+\s*
                                    (?P<units>((%(units)s)s?))
                                   ))''' % ptc.re_values
    ptc.RE_QUNITS    = r'''(?P<qty>(-?\d+\s?
                                    (?P<qunits>%(qunits)s)
                                    (\s?|,|$)
                                   ))''' % ptc.re_values
    ptc.RE_MODIFIER  = r'''(\s?|^)
                           (?P<modifier>
                            (previous|prev|last|next|eod|eo|(end\sof)|(in\sa)))''' % ptc.re_values
    ptc.RE_MODIFIER2 = r'''(\s?|^)
                           (?P<modifier>
                            (from|before|after|ago|prior))
                           (\s?|$|[^0-9a-zA-Z])''' % ptc.re_values
    ptc.RE_TIMEHMS   = r'''(\s?|^)
                           (?P<hours>\d\d?)
                           (?P<tsep>%(timeseperator)s|)
                           (?P<minutes>\d\d)
                           (?:(?P=tsep)(?P<seconds>\d\d(?:[.,]\d+)?))?''' % ptc.re_values
    ptc.RE_TIMEHMS2  = r'''(?P<hours>(\d\d?))
                           ((?P<tsep>%(timeseperator)s|)
                            (?P<minutes>(\d\d?))
                            (?:(?P=tsep)
                               (?P<seconds>\d\d?
                                (?:[.,]\d+)?))?)?''' % ptc.re_values

    if 'meridian' in ptc.re_values:
        ptc.RE_TIMEHMS2 += r'\s?(?P<meridian>(%(meridian)s))' % ptc.re_values

    dateSeps = ''.join(ptc.dateSep) + '.'

    ptc.RE_DATE      = r'''(\s?|^)
                           (?P<date>(\d\d?[%s]\d\d?([%s]\d\d(\d\d)?)?))
                           (\s?|$|[^0-9a-zA-Z])''' % (dateSeps, dateSeps)
    ptc.RE_DATE2     = r'[%s]' % dateSeps
    ptc.RE_DAY       = r'''(\s?|^)
                           (?P<day>(today|tomorrow|yesterday))
                           (\s?|$|[^0-9a-zA-Z])''' % ptc.re_values
    ptc.RE_DAY2      = r'''(?P<day>\d\d?)|(?P<suffix>%(daysuffix)s)
                        ''' % ptc.re_values
    ptc.RE_TIME      = r'''(\s?|^)
                           (?P<time>(morning|breakfast|noon|lunch|evening|midnight|tonight|dinner|night|now))
                           (\s?|$|[^0-9a-zA-Z])''' % ptc.re_values
    ptc.RE_REMAINING = r'\s+'

    # Regex for date/time ranges
    ptc.RE_RTIMEHMS  = r'''(\s?|^)
                           (\d\d?)%(timeseperator)s
                           (\d\d)
                           (%(timeseperator)s(\d\d))?
                           (\s?|$)''' % ptc.re_values
    ptc.RE_RTIMEHMS2 = r'''(\s?|^)
                           (\d\d?)
                           (%(timeseperator)s(\d\d?))?
                           (%(timeseperator)s(\d\d?))?''' % ptc.re_values

    if 'meridian' in ptc.re_values:
        ptc.RE_RTIMEHMS2 += r'\s?(%(meridian)s)' % ptc.re_values

    ptc.RE_RDATE  = r'(\d+([%s]\d+)+)' % dateSeps
    ptc.RE_RDATE3 = r'''((((%(months)s))\s?
                         ((\d\d?)
                          (\s?|%(daysuffix)s|$)+)?
                         (,\s?\d\d\d\d)?))''' % ptc.re_values

    # "06/07/06 - 08/09/06"
    ptc.DATERNG1 = ptc.RE_RDATE + r'\s?%(rangeseperator)s\s?' + ptc.RE_RDATE
    ptc.DATERNG1 = ptc.DATERNG1 % ptc.re_values

    # "march 31 - june 1st, 2006"
    ptc.DATERNG2 = ptc.RE_RDATE3 + r'\s?%(rangeseperator)s\s?' + ptc.RE_RDATE3
    ptc.DATERNG2 = ptc.DATERNG2 % ptc.re_values

    # "march 1rd -13th"
    ptc.DATERNG3 = ptc.RE_RDATE3 + r'\s?%(rangeseperator)s\s?(\d\d?)\s?(rd|st|nd|th)?'
    ptc.DATERNG3 = ptc.DATERNG3 % ptc.re_values

    # "4:00:55 pm - 5:90:44 am", '4p-5p'
    ptc.TIMERNG1 = ptc.RE_RTIMEHMS2 + r'\s?%(rangeseperator)s\s?' + ptc.RE_RTIMEHMS2
    ptc.TIMERNG1 = ptc.TIMERNG1 % ptc.re_values

    # "4:00 - 5:90 ", "4:55:55-3:44:55"
    ptc.TIMERNG2 = ptc.RE_RTIMEHMS + r'\s?%(rangeseperator)s\s?' + ptc.RE_RTIMEHMS
    ptc.TIMERNG2 = ptc.TIMERNG2 % ptc.re_values

    # "4-5pm "
    ptc.TIMERNG3 = r'\d\d?\s?%(rangeseperator)s\s?' + ptc.RE_RTIMEHMS2
    ptc.TIMERNG3 = ptc.TIMERNG3 % ptc.re_values

    # "4:30-5pm "
    ptc.TIMERNG4 = ptc.RE_RTIMEHMS + r'\s?%(rangeseperator)s\s?' + ptc.RE_RTIMEHMS2
    ptc.TIMERNG4 = ptc.TIMERNG4 % ptc.re_values


def _initConstants(ptc):
    """
    Create localized versions of the units, week and month names
    """
      # build weekday offsets - yes, it assumes the Weekday and shortWeekday
      # lists are in the same order and Mon..Sun (Python style)
    ptc.WeekdayOffsets = {}

    o = 0
    for key in ptc.Weekdays:
        ptc.WeekdayOffsets[key] = o
        o += 1
    o = 0
    for key in ptc.shortWeekdays:
        ptc.WeekdayOffsets[key] = o
        o += 1

      # build month offsets - yes, it assumes the Months and shortMonths
      # lists are in the same order and Jan..Dec
    ptc.MonthOffsets = {}

    o = 1
    for key in ptc.Months:
        ptc.MonthOffsets[key] = o
        o += 1
    o = 1
    for key in ptc.shortMonths:
        ptc.MonthOffsets[key] = o
        o += 1

    # ptc.DaySuffixes = ptc.re_consts['daysuffix'].split('|')


class Constants:
    """
    Default set of constants for parsedatetime.

    If PyICU is present, then the class will first try to get PyICU
    to return a locale specified by C{localeID}.  If either C{localeID} is
    None or if the locale does not exist within PyICU, then each of the
    locales defined in C{fallbackLocales} is tried in order.

    If PyICU is not present or none of the specified locales can be used,
    then the class will initialize itself to the en_US locale.

    if PyICU is not present or not requested, only the locales defined by
    C{pdtLocales} will be searched.
    """
    def __init__(self, localeID=None, usePyICU=True, fallbackLocales=['en_US']):
        self.localeID        = localeID
        self.fallbackLocales = fallbackLocales

        if 'en_US' not in self.fallbackLocales:
            self.fallbackLocales.append('en_US')

          # define non-locale specific constants

        self.locale   = None
        self.usePyICU = usePyICU

        # starting cache of leap years
        # daysInMonth will add to this if during
        # runtime it gets a request for a year not found
        self._leapYears = [ 1904, 1908, 1912, 1916, 1920, 1924, 1928, 1932, 1936, 1940, 1944,
                            1948, 1952, 1956, 1960, 1964, 1968, 1972, 1976, 1980, 1984, 1988,
                            1992, 1996, 2000, 2004, 2008, 2012, 2016, 2020, 2024, 2028, 2032,
                            2036, 2040, 2044, 2048, 2052, 2056, 2060, 2064, 2068, 2072, 2076,
                            2080, 2084, 2088, 2092, 2096 ]

        self.Second =   1
        self.Minute =  60 * self.Second
        self.Hour   =  60 * self.Minute
        self.Day    =  24 * self.Hour
        self.Week   =   7 * self.Day
        self.Month  =  30 * self.Day
        self.Year   = 365 * self.Day

        self.rangeSep = u'-'

        self._DaysInMonthList = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)

        self.BirthdayEpoch = 50

        # DOWParseStyle controls how we parse "Tuesday"
        # If the current day was Thursday and the text to parse is "Tuesday"
        # then the following table shows how each style would be returned
        # -1, 0, +1
        #
        # Current day marked as ***
        #
        #          Sun Mon Tue Wed Thu Fri Sat
        # week -1
        # current         -1,0     ***
        # week +1          +1
        #
        # If the current day was Monday and the text to parse is "Tuesday"
        # then the following table shows how each style would be returned
        # -1, 0, +1
        #
        #          Sun Mon Tue Wed Thu Fri Sat
        # week -1           -1
        # current      *** 0,+1
        # week +1

        self.DOWParseStyle = 1

        # CurrentDOWParseStyle controls how we parse "Friday"
        # If the current day was Friday and the text to parse is "Friday"
        # then the following table shows how each style would be returned
        # True/False. This also depends on DOWParseStyle.
        #
        # Current day marked as ***
        #
        # DOWParseStyle = 0
        #          Sun Mon Tue Wed Thu Fri Sat
        # week -1
        # current                      T,F
        # week +1
        #
        # DOWParseStyle = -1
        #          Sun Mon Tue Wed Thu Fri Sat
        # week -1                       F
        # current                       T
        # week +1
        #
        # DOWParseStyle = +1
        #
        #          Sun Mon Tue Wed Thu Fri Sat
        # week -1
        # current                       T
        # week +1                       F

        self.CurrentDOWParseStyle = False

        # initalize attributes to empty values to ensure
        # they are defined
        self.re_sources     = None
        self.re_values      = None
        self.Modifiers      = None
        self.dayOffsets     = None
        self.WeekdayOffsets = None
        self.MonthOffsets   = None
        self.dateSep        = None
        self.timeSep        = None
        self.am             = None
        self.pm             = None
        self.meridian       = None
        self.usesMeridian   = None
        self.uses24         = None
        self.dp_order       = None

        self.RE_DATE4     = r''
        self.RE_DATE3     = r''
        self.RE_MONTH     = r''
        self.RE_WEEKDAY   = r''
        self.RE_SPECIAL   = r''
        self.RE_UNITS     = r''
        self.RE_QUNITS    = r''
        self.RE_MODIFIER  = r''
        self.RE_MODIFIER2 = r''
        self.RE_TIMEHMS   = r''
        self.RE_TIMEHMS2  = r''
        self.RE_DATE      = r''
        self.RE_DATE2     = r''
        self.RE_DAY       = r''
        self.RE_DAY2      = r''
        self.RE_TIME      = r''
        self.RE_REMAINING = r''
        self.RE_RTIMEHMS  = r''
        self.RE_RTIMEHMS2 = r''
        self.RE_RDATE     = r''
        self.RE_RDATE3    = r''
        self.DATERNG1     = r''
        self.DATERNG2     = r''
        self.DATERNG3     = r''
        self.TIMERNG1     = r''
        self.TIMERNG2     = r''
        self.TIMERNG3     = r''
        self.TIMERNG4     = r''

        _initLocale(self)
        _initConstants(self)
        _initSymbols(self)
        _initPatterns(self)

        self.re_option = re.IGNORECASE + re.VERBOSE
        self.cre_source = { 'CRE_SPECIAL':   self.RE_SPECIAL,
                            'CRE_UNITS':     self.RE_UNITS,
                            'CRE_QUNITS':    self.RE_QUNITS,
                            'CRE_MODIFIER':  self.RE_MODIFIER,
                            'CRE_MODIFIER2': self.RE_MODIFIER2,
                            'CRE_TIMEHMS':   self.RE_TIMEHMS,
                            'CRE_TIMEHMS2':  self.RE_TIMEHMS2,
                            'CRE_DATE':      self.RE_DATE,
                            'CRE_DATE2':     self.RE_DATE2,
                            'CRE_DATE3':     self.RE_DATE3,
                            'CRE_DATE4':     self.RE_DATE4,
                            'CRE_MONTH':     self.RE_MONTH,
                            'CRE_WEEKDAY':   self.RE_WEEKDAY,
                            'CRE_DAY':       self.RE_DAY,
                            'CRE_DAY2':      self.RE_DAY2,
                            'CRE_TIME':      self.RE_TIME,
                            'CRE_REMAINING': self.RE_REMAINING,
                            'CRE_RTIMEHMS':  self.RE_RTIMEHMS,
                            'CRE_RTIMEHMS2': self.RE_RTIMEHMS2,
                            'CRE_RDATE':     self.RE_RDATE,
                            'CRE_RDATE3':    self.RE_RDATE3,
                            'CRE_TIMERNG1':  self.TIMERNG1,
                            'CRE_TIMERNG2':  self.TIMERNG2,
                            'CRE_TIMERNG3':  self.TIMERNG3,
                            'CRE_TIMERNG4':  self.TIMERNG4,
                            'CRE_DATERNG1':  self.DATERNG1,
                            'CRE_DATERNG2':  self.DATERNG2,
                            'CRE_DATERNG3':  self.DATERNG3,
                          }
        self.cre_keys = self.cre_source.keys()


    def __getattr__(self, name):
        if name in self.cre_keys:
            value = re.compile(self.cre_source[name], self.re_option)
            setattr(self, name, value)
            return value
        else:
            raise AttributeError, name

    def daysInMonth(self, month, year):
        """
        Take the given month (1-12) and a given year (4 digit) return
        the number of days in the month adjusting for leap year as needed
        """
        result = None

        if month > 0 and month <= 12:
            result = self._DaysInMonthList[month - 1]

            if month == 2:
                if year in self._leapYears:
                    result += 1
                else:
                    if calendar.isleap(year):
                        self._leapYears.append(year)
                        result += 1

        return result

    def buildSources(self, sourceTime=None):
        """
        Return a dictionary of date/time tuples based on the keys
        found in self.re_sources.

        The current time is used as the default and any specified
        item found in self.re_sources is inserted into the value
        and the generated dictionary is returned.
        """
        if sourceTime is None:
            (yr, mth, dy, hr, mn, sec, wd, yd, isdst) = time.localtime()
        else:
            (yr, mth, dy, hr, mn, sec, wd, yd, isdst) = sourceTime

        sources  = {}
        defaults = { 'yr': yr, 'mth': mth, 'dy':  dy,
                     'hr': hr, 'mn':  mn,  'sec': sec, }

        for item in self.re_sources:
            values = {}
            source = self.re_sources[item]

            for key in defaults.keys():
                if key in source:
                    values[key] = source[key]
                else:
                    values[key] = defaults[key]

            sources[item] = ( values['yr'], values['mth'], values['dy'],
                              values['hr'], values['mn'], values['sec'], wd, yd, isdst )

        return sources

