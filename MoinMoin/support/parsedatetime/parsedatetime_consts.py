#!/usr/bin/env python

"""
The Constants class defines all constants used by parsedatetime.py.
"""

__license__ = """Copyright (c) 2004-2006 Mike Taylor, All rights reserved.

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
__author__       = 'Mike Taylor <http://code-bear.com>'
__contributors__ = [ 'Darshana Chhajed <mailto://darshana@osafoundation.org>',
                   ]


try:
    import PyICU as pyicu
except:
    pyicu = None


import string
import datetime, time


class pdtLocale_en:
    """
    en_US Locale constants

    This class will be used to initialize C{Constants} if PyICU is not located.

    Defined as class variables are the lists and strings needed by parsedatetime
    to evaluate strings in English (US)
    """

    localeID      = 'en_US'   # don't use a unicode string
    dateSep       = u'/'
    timeSep       = u':'
    meridian      = [ u'AM', u'PM' ]
    usesMeridian  = True
    uses24        = False

    Weekdays      = [ u'sunday', u'monday', u'tuesday',
                      u'wednesday', u'thursday', u'friday', u'saturday',
                    ]
    shortWeekdays = [ u'sun', u'mon', u'tues',
                      u'wed', u'thu', u'fri', u'sat',
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
    re_consts     = { 'specials':      'in|on|of|at',
                      'timeseperator': ':',
                      'daysuffix':     'rd|st|nd|th',
                      'meridian':      'am|pm|a.m.|p.m.|a|p',
                      'qunits':        'h|m|s|d|w|m|y',
                      'now':           [ 'now' ],
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
                  'this':       0,
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
                    }


class pdtLocale_es:
    """
    es Locale constants

    This class will be used to initialize C{Constants} if PyICU is not located.

    Defined as class variables are the lists and strings needed by parsedatetime
    to evaluate strings in Spanish

    Note that I don't speak Spanish so many of the items below are still in English
    """

    localeID      = 'es'   # don't use a unicode string
    dateSep       = u'/'
    timeSep       = u':'
    meridian      = []
    usesMeridian  = False
    uses24        = True

    Weekdays      = [ u'domingo', u'lunes', u'martes',
                      u'mi\xe9rcoles', u'jueves', u'viernes', u's\xe1bado',
                    ]
    shortWeekdays = [ 'dom', u'lun', u'mar',
                      u'mi\xe9', u'jue', u'vie', u's\xe1b',
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
    re_consts     = { 'specials':      'in|on|of|at',
                      'timeseperator': timeSep,
                      'dateseperator': dateSep,
                      'daysuffix':     'rd|st|nd|th',
                      'qunits':        'h|m|s|d|w|m|y',
                      'now':           [ 'now' ],
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
                  'this':       0,
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
    re_sources    = { 'noon':      { 'hr': 12,  'mn': 0, 'sec': 0 },
                      'lunch':     { 'hr': 12,  'mn': 0, 'sec': 0 },
                      'morning':   { 'hr':  6,  'mn': 0, 'sec': 0 },
                      'breakfast': { 'hr':  8,  'mn': 0, 'sec': 0 },
                      'dinner':    { 'hr': 19,  'mn': 0, 'sec': 0 },
                      'evening':   { 'hr': 18,  'mn': 0, 'sec': 0 },
                      'midnight':  { 'hr':  0,  'mn': 0, 'sec': 0 },
                      'night':     { 'hr': 21,  'mn': 0, 'sec': 0 },
                      'tonight':   { 'hr': 21,  'mn': 0, 'sec': 0 },
                    }


pdtLocales = { 'en_US': pdtLocale_en,
               'es':    pdtLocale_es,
             }


def _initLocale(ptc):
    """
    Helper function to initialize the different lists and strings
    from either PyICU or one of the locale pdt Locales and store
    them into ptc.
    """
    if pyicu and ptc.usePyICU:
        ptc.icuLocale = pyicu.Locale(ptc.localeID)

        if not ptc.icuLocale:
            ptc.icuLocale = pyicu.Locale('en_US')

        ptc.icuSymbols    = pyicu.DateFormatSymbols(ptc.icuLocale)

        ptc.Weekdays      = map(string.lower, ptc.icuSymbols.getWeekdays()[1:])
        ptc.shortWeekdays = map(string.lower, ptc.icuSymbols.getShortWeekdays()[1:])
        ptc.Months        = map(string.lower, ptc.icuSymbols.getMonths())
        ptc.shortMonths   = map(string.lower, ptc.icuSymbols.getShortMonths())

          # not quite sure how to init this so for now
          # set it to none so it will be set to the en_US defaults for now
        ptc.re_consts     = None

        ptc.icu_df        = { 'full':   pyicu.DateFormat.createDateInstance(pyicu.DateFormat.kFull,   ptc.icuLocale),
                              'long':   pyicu.DateFormat.createDateInstance(pyicu.DateFormat.kLong,   ptc.icuLocale),
                              'medium': pyicu.DateFormat.createDateInstance(pyicu.DateFormat.kMedium, ptc.icuLocale),
                              'short':  pyicu.DateFormat.createDateInstance(pyicu.DateFormat.kShort,  ptc.icuLocale),
                            }
        ptc.icu_tf        = { 'full':   pyicu.DateFormat.createTimeInstance(pyicu.DateFormat.kFull,   ptc.icuLocale),
                              'long':   pyicu.DateFormat.createTimeInstance(pyicu.DateFormat.kLong,   ptc.icuLocale),
                              'medium': pyicu.DateFormat.createTimeInstance(pyicu.DateFormat.kMedium, ptc.icuLocale),
                              'short':  pyicu.DateFormat.createTimeInstance(pyicu.DateFormat.kShort,  ptc.icuLocale),
                            }

        ptc.dateFormats   = { 'full':   ptc.icu_df['full'].toPattern(),
                              'long':   ptc.icu_df['long'].toPattern(),
                              'medium': ptc.icu_df['medium'].toPattern(),
                              'short':  ptc.icu_df['short'].toPattern(),
                            }
        ptc.timeFormats   = { 'full':   ptc.icu_tf['full'].toPattern(),
                              'long':   ptc.icu_tf['long'].toPattern(),
                              'medium': ptc.icu_tf['medium'].toPattern(),
                              'short':  ptc.icu_tf['short'].toPattern(),
                            }
    else:
        if not ptc.localeID in pdtLocales:
            ptc.localeID = 'en_US'

        ptc.locale = pdtLocales[ptc.localeID]

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

    ptc.re_values['months']      = '%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s' % tuple(ptc.Months)
    ptc.re_values['shortmonths'] = '%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s|%s' % tuple(ptc.shortMonths)
    ptc.re_values['days']        = '%s|%s|%s|%s|%s|%s|%s' % tuple(ptc.Weekdays)
    ptc.re_values['shortdays']   = '%s|%s|%s|%s|%s|%s|%s' % tuple(ptc.shortWeekdays)

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
    ptc.timeSep  = u':'
    ptc.dateSep  = u'/'
    ptc.meridian = [ u'AM', u'PM' ]

    ptc.usesMeridian = True
    ptc.uses24       = False

    if pyicu:
        am = u''
        pm = u''

          # ICU doesn't seem to provide directly the
          # date or time seperator - so we have to
          # figure it out

        p = pyicu.FieldPosition(pyicu.DateFormat.AM_PM_FIELD)
        o = ptc.icu_tf['short']

        s = ptc.timeFormats['short']

        ptc.usesMeridian = u'a' in s
        ptc.uses24       = u'H' in s

        s = o.format(datetime.datetime(2003, 10, 30, 11, 45))       # '11:45 AM' or '11:45'

        s = s.replace('11', '').replace('45', '')                   # ': AM' or ':'

        if len(s) > 0:
            ptc.timeSep = s[0]

        if ptc.usesMeridian:
            am = s[1:].strip()                                      # 'AM'

            s = o.format(datetime.datetime(2003, 10, 30, 23, 45))   # '23:45 AM' or '23:45'

            if ptc.uses24:
                s = s.replace('23', '')
            else:
                s = s.replace('11', '')

            pm = s.replace('45', '').replace(ptc.timeSep, '').strip()  # 'PM' or ''

        ptc.meridian = [ am, pm ]

    else:
        ptc.timeSep      = ptc.locale.timeSep
        ptc.dateSep      = ptc.locale.dateSep
        ptc.meridian     = ptc.locale.meridian
        ptc.usesMeridian = ptc.locale.usesMeridian
        ptc.uses24       = ptc.locale.uses24

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

    ptc.RE_DATE3     = r'(?P<date>((?P<mthname>(%(months)s|%(shortmonths)s))\s?((?P<day>\d\d?)(\s|%(daysuffix)s|,|$)+)?(?P<year>\d\d\d\d)?))' % ptc.re_values
    ptc.RE_MONTH     = r'(?P<month>((?P<mthname>(%(months)s|%(shortmonths)s))(\s?(?P<year>(\d\d\d\d)))?))' % ptc.re_values
    ptc.RE_WEEKDAY   = r'(?P<weekday>(%(days)s|%(shortdays)s))' % ptc.re_values

    ptc.RE_SPECIAL   = r'(?P<special>^[%(specials)s]+)\s+' % ptc.re_values
    ptc.RE_UNITS     = r'(?P<qty>(-?\d+\s*(?P<units>((%(units)s)s?))))' % ptc.re_values
    ptc.RE_QUNITS    = r'(?P<qty>(-?\d+\s?(?P<qunits>%(qunits)s)(\s|,|$)))' % ptc.re_values
    ptc.RE_MODIFIER  = r'(?P<modifier>(previous|prev|last|next|this|eo|(end\sof)|(in\sa)))' % ptc.re_values
    ptc.RE_MODIFIER2 = r'(?P<modifier>(from|before|after|ago|prior))' % ptc.re_values
    ptc.RE_TIMEHMS   = r'(?P<hours>\d\d?)(?P<tsep>%(timeseperator)s|)(?P<minutes>\d\d)(?:(?P=tsep)(?P<seconds>\d\d(?:[.,]\d+)?))?' % ptc.re_values

    ptc.RE_TIMEHMS2  = r'(?P<hours>(\d\d?))((?P<tsep>%(timeseperator)s|)(?P<minutes>(\d\d?))(?:(?P=tsep)(?P<seconds>\d\d?(?:[.,]\d+)?))?)?' % ptc.re_values

    if 'meridian' in ptc.re_values:
        ptc.RE_TIMEHMS2 += r'\s?(?P<meridian>(%(meridian)s))' % ptc.re_values

    ptc.RE_DATE      = r'(?P<date>\d+([/.\\]\d+)+)'
    ptc.RE_DATE2     = r'[/.\\]'
    ptc.RE_DAY       = r'(?P<day>(today|tomorrow|yesterday))' % ptc.re_values
    ptc.RE_TIME      = r'\s*(?P<time>(morning|breakfast|noon|lunch|evening|midnight|tonight|dinner|night|now))' % ptc.re_values
    ptc.RE_REMAINING = r'\s+'

      # Regex for date/time ranges

    ptc.RE_RTIMEHMS  = r'(\d\d?)%(timeseperator)s(\d\d)(%(timeseperator)s(\d\d))?' % ptc.re_values

    ptc.RE_RTIMEHMS2 = r'(\d\d?)(%(timeseperator)s(\d\d?))?(%(timeseperator)s(\d\d?))?' % ptc.re_values

    if 'meridian' in ptc.re_values:
        ptc.RE_RTIMEHMS2 += r'\s?(%(meridian)s)' % ptc.re_values

    ptc.RE_RDATE     = r'(\d+([/.\\]\d+)+)'
    ptc.RE_RDATE3    = r'((((%(months)s))\s?((\d\d?)(\s|%(daysuffix)s|,|$)+)?(\d\d\d\d)?))' % ptc.re_values
    ptc.DATERNG1     = ptc.RE_RDATE     + r'\s?-\s?' + ptc.RE_RDATE     # "06/07/06 - 08/09/06"
    ptc.DATERNG2     = ptc.RE_RDATE3    + r'\s?-\s?' + ptc.RE_RDATE3    # "march 31 - june 1st, 2006"
    ptc.DATERNG3     = ptc.RE_RDATE3    + r'\s?' + r'-' + r'\s?(\d\d?)\s?(rd|st|nd|th)?' % ptc.re_values # "march 1rd -13th"
    ptc.TIMERNG1     = ptc.RE_RTIMEHMS2 + r'\s?-\s?'+ ptc.RE_RTIMEHMS2  # "4:00:55 pm - 5:90:44 am",'4p-5p'
    ptc.TIMERNG2     = ptc.RE_RTIMEHMS  + r'\s?-\s?'+ ptc.RE_RTIMEHMS   # "4:00 - 5:90 ","4:55:55-3:44:55"
    ptc.TIMERNG3     = r'\d\d?\s?-\s?'+ ptc.RE_RTIMEHMS2                # "4-5pm "


def _initConstants(ptc):
    """
    Create localized versions of the units, week and month names
    """
      # build weekday offsets - yes, it assumes the Weekday and shortWeekday
      # lists are in the same order and Sun..Sat
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
    ptc.DaysInMonth  = {}

    o = 1
    for key in ptc.Months:
        ptc.MonthOffsets[key] = o
        ptc.DaysInMonth[key]  = ptc.DaysInMonthList[o - 1]
        o += 1
    o = 1
    for key in ptc.shortMonths:
        ptc.MonthOffsets[key] = o
        ptc.DaysInMonth[key]  = ptc.DaysInMonthList[o - 1]
        o += 1


class Constants:
    """
    Default set of constants for parsedatetime.

    If PyICU is present, then the class will initialize itself to
    the current default locale or to the locale specified by C{localeID}.

    If PyICU is not present then the class will initialize itself to
    en_US locale or if C{localeID} is passed in and the value matches one
    of the defined pdtLocales then that will be used.
    """
    def __init__(self, localeID=None, usePyICU=True):
        if localeID is None:
            self.localeID = 'en_US'
        else:
            self.localeID = localeID

          # define non-locale specific constants

        self.locale   = None
        self.usePyICU = usePyICU

        self.Second =   1
        self.Minute =  60 * self.Second
        self.Hour   =  60 * self.Minute
        self.Day    =  24 * self.Hour
        self.Week   =   7 * self.Day
        self.Month  =  30 * self.Day
        self.Year   = 365 * self.Day

        self.DaysInMonthList = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)

        _initLocale(self)
        _initConstants(self)
        _initSymbols(self)
        _initPatterns(self)


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
            values = self.re_sources[item]

            for key in defaults.keys():
                if not key in values:
                    values[key] = defaults[key]

            sources[item] = ( values['yr'], values['mth'], values['dy'],
                              values['hr'], values['mn'], values['sec'], wd, yd, isdst )

        return sources

