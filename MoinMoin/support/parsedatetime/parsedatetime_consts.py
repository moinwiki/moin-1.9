#!/usr/bin/env python

"""
CalendarConstants defines all constants used by parsedatetime.py.
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
__contributors__ = ['Darshana Chhajed <mailto://darshana@osafoundation.org>',
                   ]


class CalendarConstants:
    def __init__(self):
        self.Locale = 'American'

        self.TIMESEP      = ':'

        self.RE_SPECIAL   = r'(?P<special>^[in|on|of|at]+)\s+'
        self.RE_UNITS     = r'(?P<qty>(-?\d+\s*(?P<units>((hour|hr|minute|min|second|sec|day|dy|week|wk|month|mth|year|yr)s?))))'
        self.RE_QUNITS    = r'(?P<qty>(-?\d+\s?(?P<qunits>h|m|s|d|w|m|y)(\s|,|$)))'
        self.RE_MODIFIER  = r'(?P<modifier>(previous|prev|last|next|this|eo|(end\sof)|(in\sa)))'
        self.RE_MODIFIER2 = r'(?P<modifier>(from|before|after|ago|prior))'
        self.RE_TIMEHMS   = r'(?P<hours>\d\d?)(?P<tsep>:|)(?P<minutes>\d\d)(?:(?P=tsep)(?P<seconds>\d\d(?:[.,]\d+)?))?'
        self.RE_TIMEHMS2  = r'(?P<hours>(\d\d?))((?P<tsep>:|)(?P<minutes>(\d\d?))(?:(?P=tsep)(?P<seconds>\d\d?(?:[.,]\d+)?))?)?\s?(?P<meridian>(am|pm|a.m.|p.m.|a|p))'
        self.RE_DATE      = r'(?P<date>\d+([/.\\]\d+)+)'
        self.RE_DATE2     = r'[/.\\-]'
        self.RE_DATE3     = r'(?P<date>((?P<mthname>(january|february|march|april|may|june|july|august|september|october|november|december))\s?((?P<day>\d\d?)(\s|rd|st|nd|th|,|$)+)?(?P<year>\d\d\d\d)?))'
        self.RE_MONTH     = r'(?P<month>((?P<mthname>(january|february|march|april|may|june|july|august|september|october|november|december))(\s?(?P<year>(\d\d\d\d)))?))'
        self.RE_WEEKDAY   = r'(?P<weekday>(monday|mon|tuesday|tue|wednesday|wed|thursday|thu|friday|saturday|sat|sunday|sun))'
        self.RE_DAY       = r'(?P<day>(today|tomorrow|yesterday))'
        self.RE_TIME      = r'\s*(?P<time>(morning|breakfast|noon|lunch|evening|midnight|tonight|dinner|night|now))' 
        self.RE_REMAINING = r'\s+'

          # Used to adjust the returned date before/after the source

        self.Modifiers = { 'from':       1,
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

        self.Second =   1
        self.Minute =  60 * self.Second
        self.Hour   =  60 * self.Minute
        self.Day    =  24 * self.Hour
        self.Week   =   7 * self.Day
        self.Month  =  30 * self.Day
        self.Year   = 365 * self.Day

        self.WeekDays = { 'monday':    0,
                          'mon':       0,
                          'tuesday':   1,
                          'tue':       1,
                          'wednesday': 2,
                          'wed':       2,
                          'thursday':  3,
                          'thu':       3,
                          'friday':    4,
                          'fri':       4,
                          'saturday':  5,
                          'sat':       5,
                          'sunday':    6,
                          'sun':       6,
                        }

          # dictionary to allow for locale specific text
          # NOTE: The keys are the localized values - the parsing
          #       code will be using Target_Text using the values
          #       extracted *from* the user's input

        self.Target_Text = { 'datesep':   '-',
                             'timesep':   ':',
                             'day':       'day',
                             'dy':        'dy',
                             'd':         'd',
                             'week':      'week',
                             'wk':        'wk',
                             'w':         'w',
                             'month':     'month',
                             'mth':       'mth',
                             'year':      'year',
                             'yr':        'yr',
                             'y':         'y',
                             'hour':      'hour',
                             'hr':        'hr',
                             'h':         'h',
                             'minute':    'minute',
                             'min':       'min',
                             'm':         'm',
                             'second':    'second',
                             'sec':       'sec',
                             's':         's',
                             'now':       'now',
                             'noon':      'noon',
                             'morning':   'morning',
                             'evening':   'evening',
                             'breakfast': 'breakfast',
                             'lunch':     'lunch',
                             'dinner':    'dinner',
                             'monday':    'monday',
                             'mon':       'mon',
                             'tuesday':   'tuesday',
                             'tue':       'tue',
                             'wednesday': 'wednesday',
                             'wed':       'wed',
                             'thursday':  'thursday',
                             'thu':       'thu',
                             'friday':    'friday',
                             'fri':       'fri',
                             'saturday':  'saturday',
                             'sat':       'sat',
                             'sunday':    'sunday',
                             'sun':       'sun',
                             'january':   'january',
                             'jan':       'jan',
                             'febuary':   'febuary',
                             'feb':       'feb',
                             'march':     'march',
                             'mar':       'mar',
                             'april':     'april',
                             'apr':       'apr',
                             'may':       'may',
                             'may':       'may',
                             'june':      'june',
                             'jun':       'jun',
                             'july':      'july',
                             'jul':       'jul',
                             'august':    'august',
                             'aug':       'aug',
                             'september': 'september',
                             'sept':      'sep',
                             'october':   'october',
                             'oct':       'oct',
                             'november':  'november',
                             'nov':       'nov',
                             'december':  'december',
                             'dec':       'dec',
                           }

          # FIXME: there *has* to be a standard routine that does this

        self.DOW_Text = [self.Target_Text['mon'],
                         self.Target_Text['tue'],
                         self.Target_Text['wed'],
                         self.Target_Text['thu'],
                         self.Target_Text['fri'],
                         self.Target_Text['sat'],
                         self.Target_Text['sun'],
                        ]

        self.DaysInMonthList = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)

        self.DaysInMonth = {}
        self.DaysInMonth[self.Target_Text['january']]   = self.DaysInMonthList[0]
        self.DaysInMonth[self.Target_Text['febuary']]   = self.DaysInMonthList[1]
        self.DaysInMonth[self.Target_Text['march']]     = self.DaysInMonthList[2]
        self.DaysInMonth[self.Target_Text['april']]     = self.DaysInMonthList[3]
        self.DaysInMonth[self.Target_Text['may']]       = self.DaysInMonthList[4]
        self.DaysInMonth[self.Target_Text['june']]      = self.DaysInMonthList[5]
        self.DaysInMonth[self.Target_Text['july']]      = self.DaysInMonthList[6]
        self.DaysInMonth[self.Target_Text['august']]    = self.DaysInMonthList[7]
        self.DaysInMonth[self.Target_Text['september']] = self.DaysInMonthList[8]
        self.DaysInMonth[self.Target_Text['october']]   = self.DaysInMonthList[9]
        self.DaysInMonth[self.Target_Text['november']]  = self.DaysInMonthList[10]
        self.DaysInMonth[self.Target_Text['december']]  = self.DaysInMonthList[11]

        self.Month_Text = [ self.Target_Text['january'],
                            self.Target_Text['febuary'],
                            self.Target_Text['march'],
                            self.Target_Text['april'],
                            self.Target_Text['may'],
                            self.Target_Text['june'],
                            self.Target_Text['july'],
                            self.Target_Text['august'],
                            self.Target_Text['september'],
                            self.Target_Text['october'],
                            self.Target_Text['november'],
                            self.Target_Text['december'],
                          ]


        self.MthNames = { 'january':    1,
                          'february':   2,
                          'march':      3,
                          'april':      4,
                          'may' :       5,
                          'june':       6,
                          'july':       7,
                          'august':     8,
                          'september':  9,
                          'october':   10,
                          'november':  11,
                          'december':  12,
                        }



          # This looks hokey - but it is a nice simple way to get
          # the proper unit value and it has the advantage that
          # later I can morph it into something localized.
          # Any trailing s will be removed before lookup.

        self.Units = {}
        self.Units[self.Target_Text['second']] = self.Second
        self.Units[self.Target_Text['sec']]    = self.Second
        self.Units[self.Target_Text['s']]      = self.Second
        self.Units[self.Target_Text['minute']] = self.Minute
        self.Units[self.Target_Text['min']]    = self.Minute
        self.Units[self.Target_Text['m']]      = self.Minute
        self.Units[self.Target_Text['hour']]   = self.Hour
        self.Units[self.Target_Text['hr']]     = self.Hour
        self.Units[self.Target_Text['h']]      = self.Hour
        self.Units[self.Target_Text['day']]    = self.Day
        self.Units[self.Target_Text['dy']]     = self.Day
        self.Units[self.Target_Text['d']]      = self.Day
        self.Units[self.Target_Text['week']]   = self.Week
        self.Units[self.Target_Text['wk']]     = self.Week
        self.Units[self.Target_Text['w']]      = self.Week
        self.Units[self.Target_Text['month']]  = self.Month
        self.Units[self.Target_Text['mth']]    = self.Month
        self.Units[self.Target_Text['year']]   = self.Year
        self.Units[self.Target_Text['yr']]     = self.Year
        self.Units[self.Target_Text['y']]      = self.Year

        self.Units_Text = { 'one':        1,
                            'two':        2,
                            'three':      3,
                            'four':       4,
                            'five':       5,
                            'six':        6,
                            'seven':      7,
                            'eight':      8,
                            'nine':       9,
                            'ten':       10,
                            'eleven':    11,
                            'twelve':    12,
                            'thirteen':  13,
                            'fourteen':  14,
                            'fifteen':   15,
                            'sixteen':   16,
                            'seventeen': 17,
                            'eighteen':  18,
                            'nineteen':  19,
                            'twenty':    20,
                            'thirty':    30,
                            'forty':     40,
                            'fifty':     50,
                            'sixty':     60,
                            'seventy':   70,
                            'eighty':    80,
                            'ninety':    90,
                            'half':      0.5,
                            'quarter':  0.25,
                         }

