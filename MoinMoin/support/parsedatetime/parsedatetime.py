#!/usr/bin/env python

"""
Parse human-readable date/time text.
"""

__license__ = """
Copyright (c) 2004-2008 Mike Taylor
Copyright (c) 2006-2008 Darshana Chhajed
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

_debug = False


import re
import time
import datetime
import rfc822
import parsedatetime_consts


# Copied from feedparser.py
# Universal Feedparser
# Copyright (c) 2002-2006, Mark Pilgrim, All rights reserved.
# Originally a def inside of _parse_date_w3dtf()
def _extract_date(m):
    year = int(m.group('year'))
    if year < 100:
        year = 100 * int(time.gmtime()[0] / 100) + int(year)
    if year < 1000:
        return 0, 0, 0
    julian = m.group('julian')
    if julian:
        julian = int(julian)
        month = julian / 30 + 1
        day = julian % 30 + 1
        jday = None
        while jday != julian:
            t = time.mktime((year, month, day, 0, 0, 0, 0, 0, 0))
            jday = time.gmtime(t)[-2]
            diff = abs(jday - julian)
            if jday > julian:
                if diff < day:
                    day = day - diff
                else:
                    month = month - 1
                    day = 31
            elif jday < julian:
                if day + diff < 28:
                    day = day + diff
                else:
                    month = month + 1
        return year, month, day
    month = m.group('month')
    day = 1
    if month is None:
        month = 1
    else:
        month = int(month)
        day = m.group('day')
        if day:
            day = int(day)
        else:
            day = 1
    return year, month, day

# Copied from feedparser.py
# Universal Feedparser
# Copyright (c) 2002-2006, Mark Pilgrim, All rights reserved.
# Originally a def inside of _parse_date_w3dtf()
def _extract_time(m):
    if not m:
        return 0, 0, 0
    hours = m.group('hours')
    if not hours:
        return 0, 0, 0
    hours = int(hours)
    minutes = int(m.group('minutes'))
    seconds = m.group('seconds')
    if seconds:
        seconds = int(seconds)
    else:
        seconds = 0
    return hours, minutes, seconds


# Copied from feedparser.py
# Universal Feedparser
# Copyright (c) 2002-2006, Mark Pilgrim, All rights reserved.
# Modified to return a tuple instead of mktime
#
# Original comment:
#   W3DTF-style date parsing adapted from PyXML xml.utils.iso8601, written by
#   Drake and licensed under the Python license.  Removed all range checking
#   for month, day, hour, minute, and second, since mktime will normalize
#   these later
def _parse_date_w3dtf(dateString):
    # the __extract_date and __extract_time methods were
    # copied-out so they could be used by my code --bear
    def __extract_tzd(m):
        '''Return the Time Zone Designator as an offset in seconds from UTC.'''
        if not m:
            return 0
        tzd = m.group('tzd')
        if not tzd:
            return 0
        if tzd == 'Z':
            return 0
        hours = int(m.group('tzdhours'))
        minutes = m.group('tzdminutes')
        if minutes:
            minutes = int(minutes)
        else:
            minutes = 0
        offset = (hours*60 + minutes) * 60
        if tzd[0] == '+':
            return -offset
        return offset

    __date_re = ('(?P<year>\d\d\d\d)'
                 '(?:(?P<dsep>-|)'
                 '(?:(?P<julian>\d\d\d)'
                 '|(?P<month>\d\d)(?:(?P=dsep)(?P<day>\d\d))?))?')
    __tzd_re = '(?P<tzd>[-+](?P<tzdhours>\d\d)(?::?(?P<tzdminutes>\d\d))|Z)'
    __tzd_rx = re.compile(__tzd_re)
    __time_re = ('(?P<hours>\d\d)(?P<tsep>:|)(?P<minutes>\d\d)'
                 '(?:(?P=tsep)(?P<seconds>\d\d(?:[.,]\d+)?))?'
                 + __tzd_re)
    __datetime_re = '%s(?:T%s)?' % (__date_re, __time_re)
    __datetime_rx = re.compile(__datetime_re)
    m = __datetime_rx.match(dateString)
    if (m is None) or (m.group() != dateString): return
    return _extract_date(m) + _extract_time(m) + (0, 0, 0)


# Copied from feedparser.py
# Universal Feedparser
# Copyright (c) 2002-2006, Mark Pilgrim, All rights reserved.
# Modified to return a tuple instead of mktime
#
def _parse_date_rfc822(dateString):
    '''Parse an RFC822, RFC1123, RFC2822, or asctime-style date'''
    data = dateString.split()
    if data[0][-1] in (',', '.') or data[0].lower() in rfc822._daynames:
        del data[0]
    if len(data) == 4:
        s = data[3]
        i = s.find('+')
        if i > 0:
            data[3:] = [s[:i], s[i+1:]]
        else:
            data.append('')
        dateString = " ".join(data)
    if len(data) < 5:
        dateString += ' 00:00:00 GMT'
    return rfc822.parsedate_tz(dateString)

# rfc822.py defines several time zones, but we define some extra ones.
# 'ET' is equivalent to 'EST', etc.
_additional_timezones = {'AT': -400, 'ET': -500,
                         'CT': -600, 'MT': -700,
                         'PT': -800}
rfc822._timezones.update(_additional_timezones)


class Calendar:
    """
    A collection of routines to input, parse and manipulate date and times.
    The text can either be 'normal' date values or it can be human readable.
    """

    def __init__(self, constants=None):
        """
        Default constructor for the L{Calendar} class.

        @type  constants: object
        @param constants: Instance of the class L{parsedatetime_consts.Constants}

        @rtype:  object
        @return: L{Calendar} instance
        """
          # if a constants reference is not included, use default
        if constants is None:
            self.ptc = parsedatetime_consts.Constants()
        else:
            self.ptc = constants

        self.weekdyFlag    = False  # monday/tuesday/...
        self.dateStdFlag   = False  # 07/21/06
        self.dateStrFlag   = False  # July 21st, 2006
        self.timeStdFlag   = False  # 5:50 
        self.meridianFlag  = False  # am/pm
        self.dayStrFlag    = False  # tomorrow/yesterday/today/..
        self.timeStrFlag   = False  # lunch/noon/breakfast/...
        self.modifierFlag  = False  # after/before/prev/next/..
        self.modifier2Flag = False  # after/before/prev/next/..
        self.unitsFlag     = False  # hrs/weeks/yrs/min/..
        self.qunitsFlag    = False  # h/m/t/d..

        self.timeFlag      = 0
        self.dateFlag      = 0


    def _convertUnitAsWords(self, unitText):
        """
        Converts text units into their number value

        Five = 5
        Twenty Five = 25
        Two hundred twenty five = 225
        Two thousand and twenty five = 2025
        Two thousand twenty five = 2025

        @type  unitText: string
        @param unitText: number text to convert

        @rtype:  integer
        @return: numerical value of unitText
        """
        # TODO: implement this
        pass


    def _buildTime(self, source, quantity, modifier, units):
        """
        Take C{quantity}, C{modifier} and C{unit} strings and convert them into values.
        After converting, calcuate the time and return the adjusted sourceTime.

        @type  source:   time
        @param source:   time to use as the base (or source)
        @type  quantity: string
        @param quantity: quantity string
        @type  modifier: string
        @param modifier: how quantity and units modify the source time
        @type  units:    string
        @param units:    unit of the quantity (i.e. hours, days, months, etc)

        @rtype:  struct_time
        @return: C{struct_time} of the calculated time
        """
        if _debug:
            print '_buildTime: [%s][%s][%s]' % (quantity, modifier, units)

        if source is None:
            source = time.localtime()

        if quantity is None:
            quantity = ''
        else:
            quantity = quantity.strip()

        if len(quantity) == 0:
            qty = 1
        else:
            try:
                qty = int(quantity)
            except ValueError:
                qty = 0

        if modifier in self.ptc.Modifiers:
            qty = qty * self.ptc.Modifiers[modifier]

            if units is None or units == '':
                units = 'dy'

        # plurals are handled by regex's (could be a bug tho)

        (yr, mth, dy, hr, mn, sec, _, _, _) = source

        start  = datetime.datetime(yr, mth, dy, hr, mn, sec)
        target = start

        if units.startswith('y'):
            target        = self.inc(start, year=qty)
            self.dateFlag = 1
        elif units.endswith('th') or units.endswith('ths'):
            target        = self.inc(start, month=qty)
            self.dateFlag = 1
        else:
            if units.startswith('d'):
                target        = start + datetime.timedelta(days=qty)
                self.dateFlag = 1
            elif units.startswith('h'):
                target        = start + datetime.timedelta(hours=qty)
                self.timeFlag = 2
            elif units.startswith('m'):
                target        = start + datetime.timedelta(minutes=qty)
                self.timeFlag = 2
            elif units.startswith('s'):
                target        = start + datetime.timedelta(seconds=qty)
                self.timeFlag = 2
            elif units.startswith('w'):
                target        = start + datetime.timedelta(weeks=qty)
                self.dateFlag = 1

        return target.timetuple()


    def parseDate(self, dateString):
        """
        Parse short-form date strings::

            '05/28/2006' or '04.21'

        @type  dateString: string
        @param dateString: text to convert to a C{datetime}

        @rtype:  struct_time
        @return: calculated C{struct_time} value of dateString
        """
        yr, mth, dy, hr, mn, sec, wd, yd, isdst = time.localtime()

        # values pulled from regex's will be stored here and later
        # assigned to mth, dy, yr based on information from the locale
        # -1 is used as the marker value because we want zero values
        # to be passed thru so they can be flagged as errors later
        v1 = -1
        v2 = -1
        v3 = -1

        s = dateString
        m = self.ptc.CRE_DATE2.search(s)
        if m is not None:
            index = m.start()
            v1    = int(s[:index])
            s     = s[index + 1:]

        m = self.ptc.CRE_DATE2.search(s)
        if m is not None:
            index = m.start()
            v2    = int(s[:index])
            v3    = int(s[index + 1:])
        else:
            v2 = int(s.strip())

        v = [ v1, v2, v3 ]
        d = { 'm': mth, 'd': dy, 'y': yr }

        for i in range(0, 3):
            n = v[i]
            c = self.ptc.dp_order[i]
            if n >= 0:
                d[c] = n

        # if the year is not specified and the date has already
        # passed, increment the year
        if v3 == -1 and ((mth > d['m']) or (mth == d['m'] and dy > d['d'])):
            yr = d['y'] + 1
        else:
            yr  = d['y']

        mth = d['m']
        dy  = d['d']

        # birthday epoch constraint
        if yr < self.ptc.BirthdayEpoch:
            yr += 2000
        elif yr < 100:
            yr += 1900

        if _debug:
            print 'parseDate: ', yr, mth, dy, self.ptc.daysInMonth(mth, yr)

        if (mth > 0 and mth <= 12) and \
           (dy > 0 and dy <= self.ptc.daysInMonth(mth, yr)):
            sourceTime = (yr, mth, dy, hr, mn, sec, wd, yd, isdst)
        else:
            self.dateFlag = 0
            self.timeFlag = 0
            sourceTime    = time.localtime() # return current time if date
                                             # string is invalid

        return sourceTime


    def parseDateText(self, dateString):
        """
        Parse long-form date strings::

            'May 31st, 2006'
            'Jan 1st'
            'July 2006'

        @type  dateString: string
        @param dateString: text to convert to a datetime

        @rtype:  struct_time
        @return: calculated C{struct_time} value of dateString
        """
        yr, mth, dy, hr, mn, sec, wd, yd, isdst = time.localtime()

        currentMth = mth
        currentDy  = dy

        s   = dateString.lower()
        m   = self.ptc.CRE_DATE3.search(s)
        mth = m.group('mthname')
        mth = self.ptc.MonthOffsets[mth]

        if m.group('day') !=  None:
            dy = int(m.group('day'))
        else:
            dy = 1

        if m.group('year') !=  None:
            yr = int(m.group('year'))

            # birthday epoch constraint
            if yr < self.ptc.BirthdayEpoch:
                yr += 2000
            elif yr < 100:
                yr += 1900

        elif (mth < currentMth) or (mth == currentMth and dy < currentDy):
            # if that day and month have already passed in this year,
            # then increment the year by 1
            yr += 1

        if dy > 0 and dy <= self.ptc.daysInMonth(mth, yr):
            sourceTime = (yr, mth, dy, hr, mn, sec, wd, yd, isdst)
        else:
            # Return current time if date string is invalid
            self.dateFlag = 0
            self.timeFlag = 0
            sourceTime    = time.localtime()

        return sourceTime


    def evalRanges(self, datetimeString, sourceTime=None):
        """
        Evaluate the C{datetimeString} text and determine if
        it represents a date or time range.

        @type  datetimeString: string
        @param datetimeString: datetime text to evaluate
        @type  sourceTime:     struct_time
        @param sourceTime:     C{struct_time} value to use as the base

        @rtype:  tuple
        @return: tuple of: start datetime, end datetime and the invalid flag
        """
        startTime = ''
        endTime   = ''
        startDate = ''
        endDate   = ''
        rangeFlag = 0

        s = datetimeString.strip().lower()

        if self.ptc.rangeSep in s:
            s = s.replace(self.ptc.rangeSep, ' %s ' % self.ptc.rangeSep)
            s = s.replace('  ', ' ')

        m = self.ptc.CRE_TIMERNG1.search(s)
        if m is not None:
            rangeFlag = 1
        else:
            m = self.ptc.CRE_TIMERNG2.search(s)
            if m is not None:
                rangeFlag = 2
            else:
                m = self.ptc.CRE_TIMERNG4.search(s)
                if m is not None:
                    rangeFlag = 7
                else:
                    m = self.ptc.CRE_TIMERNG3.search(s)
                    if m is not None:
                        rangeFlag = 3
                    else:
                        m = self.ptc.CRE_DATERNG1.search(s)
                        if m is not None:
                            rangeFlag = 4
                        else:
                            m = self.ptc.CRE_DATERNG2.search(s)
                            if m is not None:
                                rangeFlag = 5
                            else:
                                m = self.ptc.CRE_DATERNG3.search(s)
                                if m is not None:
                                    rangeFlag = 6

        if _debug:
            print 'evalRanges: rangeFlag =', rangeFlag, '[%s]' % s

        if m is not None:
            if (m.group() != s):
                # capture remaining string
                parseStr = m.group()
                chunk1   = s[:m.start()]
                chunk2   = s[m.end():]
                s        = '%s %s' % (chunk1, chunk2)
                flag     = 1

                sourceTime, flag = self.parse(s, sourceTime)

                if flag == 0:
                    sourceTime = None
            else:
                parseStr = s

        if rangeFlag == 1:
            m                = re.search(self.ptc.rangeSep, parseStr)
            startTime, sflag = self.parse((parseStr[:m.start()]),       sourceTime)
            endTime, eflag   = self.parse((parseStr[(m.start() + 1):]), sourceTime)

            if (eflag != 0)  and (sflag != 0):
                return (startTime, endTime, 2)

        elif rangeFlag == 2:
            m                = re.search(self.ptc.rangeSep, parseStr)
            startTime, sflag = self.parse((parseStr[:m.start()]),       sourceTime)
            endTime, eflag   = self.parse((parseStr[(m.start() + 1):]), sourceTime)

            if (eflag != 0)  and (sflag != 0):
                return (startTime, endTime, 2)

        elif rangeFlag == 3 or rangeFlag == 7:
            m = re.search(self.ptc.rangeSep, parseStr)
            # capturing the meridian from the end time
            if self.ptc.usesMeridian:
                ampm = re.search(self.ptc.am[0], parseStr)

                # appending the meridian to the start time
                if ampm is not None:
                    startTime, sflag = self.parse((parseStr[:m.start()] + self.ptc.meridian[0]), sourceTime)
                else:
                    startTime, sflag = self.parse((parseStr[:m.start()] + self.ptc.meridian[1]), sourceTime)
            else:
                startTime, sflag = self.parse((parseStr[:m.start()]), sourceTime)

            endTime, eflag = self.parse(parseStr[(m.start() + 1):], sourceTime)

            if (eflag != 0)  and (sflag != 0):
                return (startTime, endTime, 2)

        elif rangeFlag == 4:
            m                = re.search(self.ptc.rangeSep, parseStr)
            startDate, sflag = self.parse((parseStr[:m.start()]),       sourceTime)
            endDate, eflag   = self.parse((parseStr[(m.start() + 1):]), sourceTime)

            if (eflag != 0)  and (sflag != 0):
                return (startDate, endDate, 1)

        elif rangeFlag == 5:
            m       = re.search(self.ptc.rangeSep, parseStr)
            endDate = parseStr[(m.start() + 1):]

            # capturing the year from the end date
            date    = self.ptc.CRE_DATE3.search(endDate)
            endYear = date.group('year')

            # appending the year to the start date if the start date
            # does not have year information and the end date does.
            # eg : "Aug 21 - Sep 4, 2007"
            if endYear is not None:
                startDate = (parseStr[:m.start()]).strip()
                date      = self.ptc.CRE_DATE3.search(startDate)
                startYear = date.group('year')

                if startYear is None:
                    startDate = startDate + ', ' + endYear
            else:
                startDate = parseStr[:m.start()]

            startDate, sflag = self.parse(startDate, sourceTime)
            endDate, eflag   = self.parse(endDate, sourceTime)

            if (eflag != 0)  and (sflag != 0):
                return (startDate, endDate, 1)

        elif rangeFlag == 6:
            m = re.search(self.ptc.rangeSep, parseStr)

            startDate = parseStr[:m.start()]

            # capturing the month from the start date
            mth = self.ptc.CRE_DATE3.search(startDate)
            mth = mth.group('mthname')

            # appending the month name to the end date
            endDate = mth + parseStr[(m.start() + 1):]

            startDate, sflag = self.parse(startDate, sourceTime)
            endDate, eflag   = self.parse(endDate, sourceTime)

            if (eflag != 0)  and (sflag != 0):
                return (startDate, endDate, 1)
        else:
            # if range is not found
            sourceTime = time.localtime()

            return (sourceTime, sourceTime, 0)


    def _CalculateDOWDelta(self, wd, wkdy, offset, style, currentDayStyle):
        """
        Based on the C{style} and C{currentDayStyle} determine what
        day-of-week value is to be returned.

        @type  wd:              integer
        @param wd:              day-of-week value for the current day
        @type  wkdy:            integer
        @param wkdy:            day-of-week value for the parsed day
        @type  offset:          integer
        @param offset:          offset direction for any modifiers (-1, 0, 1)
        @type  style:           integer
        @param style:           normally the value set in C{Constants.DOWParseStyle}
        @type  currentDayStyle: integer
        @param currentDayStyle: normally the value set in C{Constants.CurrentDOWParseStyle}

        @rtype:  integer
        @return: calculated day-of-week
        """
        if offset == 1:
            # modifier is indicating future week eg: "next".
            # DOW is calculated as DOW of next week
            diff = 7 - wd + wkdy

        elif offset == -1:
            # modifier is indicating past week eg: "last","previous"
            # DOW is calculated as DOW of previous week
            diff = wkdy - wd - 7

        elif offset == 0:
            # modifier is indiacting current week eg: "this"
            # DOW is calculated as DOW of this week
            diff = wkdy - wd

        elif offset == 2:
            # no modifier is present.
            # i.e. string to be parsed is just DOW
            if style == 1:
                # next occurance of the DOW is calculated
                if currentDayStyle == True:
                    if wkdy >= wd:
                        diff = wkdy - wd
                    else:
                        diff = 7 - wd + wkdy
                else:
                    if wkdy > wd:
                        diff = wkdy - wd
                    else:
                        diff = 7 - wd + wkdy

            elif style == -1:
                # last occurance of the DOW is calculated
                if currentDayStyle == True:
                    if wkdy <= wd:
                        diff = wkdy - wd
                    else:
                        diff = wkdy - wd - 7
                else:
                    if wkdy < wd:
                        diff = wkdy - wd
                    else:
                        diff = wkdy - wd - 7
            else:
                # occurance of the DOW in the current week is calculated
                diff = wkdy - wd

        if _debug:
            print "wd %s, wkdy %s, offset %d, style %d\n" % (wd, wkdy, offset, style)

        return diff


    def _evalModifier(self, modifier, chunk1, chunk2, sourceTime):
        """
        Evaluate the C{modifier} string and following text (passed in
        as C{chunk1} and C{chunk2}) and if they match any known modifiers
        calculate the delta and apply it to C{sourceTime}.

        @type  modifier:   string
        @param modifier:   modifier text to apply to sourceTime
        @type  chunk1:     string
        @param chunk1:     first text chunk that followed modifier (if any)
        @type  chunk2:     string
        @param chunk2:     second text chunk that followed modifier (if any)
        @type  sourceTime: struct_time
        @param sourceTime: C{struct_time} value to use as the base

        @rtype:  tuple
        @return: tuple of: remaining text and the modified sourceTime
        """
        offset = self.ptc.Modifiers[modifier]

        if sourceTime is not None:
            (yr, mth, dy, hr, mn, sec, wd, yd, isdst) = sourceTime
        else:
            (yr, mth, dy, hr, mn, sec, wd, yd, isdst) = time.localtime()

        # capture the units after the modifier and the remaining
        # string after the unit
        m = self.ptc.CRE_REMAINING.search(chunk2)
        if m is not None:
            index  = m.start() + 1
            unit   = chunk2[:m.start()]
            chunk2 = chunk2[index:]
        else:
            unit   = chunk2
            chunk2 = ''

        flag = False

        if unit == 'month' or \
           unit == 'mth' or \
           unit == 'm':
            if offset == 0:
                dy         = self.ptc.daysInMonth(mth, yr)
                sourceTime = (yr, mth, dy, 9, 0, 0, wd, yd, isdst)
            elif offset == 2:
                # if day is the last day of the month, calculate the last day
                # of the next month
                if dy == self.ptc.daysInMonth(mth, yr):
                    dy = self.ptc.daysInMonth(mth + 1, yr)

                start      = datetime.datetime(yr, mth, dy, 9, 0, 0)
                target     = self.inc(start, month=1)
                sourceTime = target.timetuple()
            else:
                start      = datetime.datetime(yr, mth, 1, 9, 0, 0)
                target     = self.inc(start, month=offset)
                sourceTime = target.timetuple()

            flag = True
            self.dateFlag = 1

        if unit == 'week' or \
             unit == 'wk' or \
             unit == 'w':
            if offset == 0:
                start      = datetime.datetime(yr, mth, dy, 17, 0, 0)
                target     = start + datetime.timedelta(days=(4 - wd))
                sourceTime = target.timetuple()
            elif offset == 2:
                start      = datetime.datetime(yr, mth, dy, 9, 0, 0)
                target     = start + datetime.timedelta(days=7)
                sourceTime = target.timetuple()
            else:
                return self._evalModifier(modifier, chunk1, "monday " + chunk2, sourceTime)

            flag          = True
            self.dateFlag = 1

        if unit == 'day' or \
            unit == 'dy' or \
            unit == 'd':
            if offset == 0:
                sourceTime    = (yr, mth, dy, 17, 0, 0, wd, yd, isdst)
                self.timeFlag = 2
            elif offset == 2:
                start      = datetime.datetime(yr, mth, dy, hr, mn, sec)
                target     = start + datetime.timedelta(days=1)
                sourceTime = target.timetuple()
            else:
                start      = datetime.datetime(yr, mth, dy, 9, 0, 0)
                target     = start + datetime.timedelta(days=offset)
                sourceTime = target.timetuple()

            flag          = True
            self.dateFlag = 1

        if unit == 'hour' or \
           unit == 'hr':
            if offset == 0:
                sourceTime = (yr, mth, dy, hr, 0, 0, wd, yd, isdst)
            else:
                start      = datetime.datetime(yr, mth, dy, hr, 0, 0)
                target     = start + datetime.timedelta(hours=offset)
                sourceTime = target.timetuple()

            flag          = True
            self.timeFlag = 2

        if unit == 'year' or \
             unit == 'yr' or \
             unit == 'y':
            if offset == 0:
                sourceTime = (yr, 12, 31, hr, mn, sec, wd, yd, isdst)
            elif offset == 2:
                sourceTime = (yr + 1, mth, dy, hr, mn, sec, wd, yd, isdst)
            else:
                sourceTime = (yr + offset, 1, 1, 9, 0, 0, wd, yd, isdst)

            flag          = True
            self.dateFlag = 1

        if flag == False:
            m = self.ptc.CRE_WEEKDAY.match(unit)
            if m is not None:
                wkdy          = m.group()
                self.dateFlag = 1

                if modifier == 'eod':
                    # Calculate the  upcoming weekday
                    self.modifierFlag = False
                    (sourceTime, _)   = self.parse(wkdy, sourceTime)
                    sources           = self.ptc.buildSources(sourceTime)
                    self.timeFlag     = 2

                    if modifier in sources:
                        sourceTime = sources[modifier]

                else:
                    wkdy       = self.ptc.WeekdayOffsets[wkdy]
                    diff       = self._CalculateDOWDelta(wd, wkdy, offset,
                                                         self.ptc.DOWParseStyle,
                                                         self.ptc.CurrentDOWParseStyle)
                    start      = datetime.datetime(yr, mth, dy, 9, 0, 0)
                    target     = start + datetime.timedelta(days=diff)
                    sourceTime = target.timetuple()

                flag          = True
                self.dateFlag = 1

        if not flag:
            m = self.ptc.CRE_TIME.match(unit)
            if m is not None:
                self.modifierFlag = False
                (yr, mth, dy, hr, mn, sec, wd, yd, isdst), _ = self.parse(unit)

                start      = datetime.datetime(yr, mth, dy, hr, mn, sec)
                target     = start + datetime.timedelta(days=offset)
                sourceTime = target.timetuple()
                flag       = True
            else:
                self.modifierFlag = False

                # check if the remaining text is parsable and if so,
                # use it as the base time for the modifier source time
                t, flag2 = self.parse('%s %s' % (chunk1, unit), sourceTime)

                if flag2 != 0:
                    sourceTime = t

                sources = self.ptc.buildSources(sourceTime)

                if modifier in sources:
                    sourceTime    = sources[modifier]
                    flag          = True
                    self.timeFlag = 2

        # if the word after next is a number, the string is more than likely
        # to be "next 4 hrs" which we will have to combine the units with the
        # rest of the string
        if not flag:
            if offset < 0:
                # if offset is negative, the unit has to be made negative
                unit = '-%s' % unit

            chunk2 = '%s %s' % (unit, chunk2)

        self.modifierFlag = False

        #return '%s %s' % (chunk1, chunk2), sourceTime
        return '%s' % chunk2, sourceTime

    def _evalModifier2(self, modifier, chunk1 , chunk2, sourceTime):
        """
        Evaluate the C{modifier} string and following text (passed in
        as C{chunk1} and C{chunk2}) and if they match any known modifiers
        calculate the delta and apply it to C{sourceTime}.

        @type  modifier:   string
        @param modifier:   modifier text to apply to C{sourceTime}
        @type  chunk1:     string
        @param chunk1:     first text chunk that followed modifier (if any)
        @type  chunk2:     string
        @param chunk2:     second text chunk that followed modifier (if any)
        @type  sourceTime: struct_time
        @param sourceTime: C{struct_time} value to use as the base

        @rtype:  tuple
        @return: tuple of: remaining text and the modified sourceTime
        """
        offset = self.ptc.Modifiers[modifier]
        digit  = r'\d+'

        self.modifier2Flag = False

        # If the string after the negative modifier starts with digits,
        # then it is likely that the string is similar to ' before 3 days'
        # or 'evening prior to 3 days'.
        # In this case, the total time is calculated by subtracting '3 days'
        # from the current date.
        # So, we have to identify the quantity and negate it before parsing
        # the string.
        # This is not required for strings not starting with digits since the
        # string is enough to calculate the sourceTime
        if chunk2 != '':
            if offset < 0:
                m = re.match(digit, chunk2.strip())
                if m is not None:
                    qty    = int(m.group()) * -1
                    chunk2 = chunk2[m.end():]
                    chunk2 = '%d%s' % (qty, chunk2)

            sourceTime, flag1 = self.parse(chunk2, sourceTime)
            if flag1 == 0:
                flag1 = True
            else:
                flag1 = False
            flag2 = False
        else:
            flag1 = False

        if chunk1 != '':
            if offset < 0:
                m = re.search(digit, chunk1.strip())
                if m is not None:
                    qty    = int(m.group()) * -1
                    chunk1 = chunk1[m.end():]
                    chunk1 = '%d%s' % (qty, chunk1)

            tempDateFlag       = self.dateFlag
            tempTimeFlag       = self.timeFlag
            sourceTime2, flag2 = self.parse(chunk1, sourceTime)
        else:
            return sourceTime, (flag1 and flag2)

        # if chunk1 is not a datetime and chunk2 is then do not use datetime
        # value returned by parsing chunk1
        if not (flag1 == False and flag2 == 0):
            sourceTime = sourceTime2
        else:
            self.timeFlag = tempTimeFlag
            self.dateFlag = tempDateFlag

        return sourceTime, (flag1 and flag2)


    def _evalString(self, datetimeString, sourceTime=None):
        """
        Calculate the datetime based on flags set by the L{parse()} routine

        Examples handled::
            RFC822, W3CDTF formatted dates
            HH:MM[:SS][ am/pm]
            MM/DD/YYYY
            DD MMMM YYYY

        @type  datetimeString: string
        @param datetimeString: text to try and parse as more "traditional"
                               date/time text
        @type  sourceTime:     struct_time
        @param sourceTime:     C{struct_time} value to use as the base

        @rtype:  datetime
        @return: calculated C{struct_time} value or current C{struct_time}
                 if not parsed
        """
        s   = datetimeString.strip()
        now = time.localtime()

        # Given string date is a RFC822 date
        if sourceTime is None:
            sourceTime = _parse_date_rfc822(s)

            if sourceTime is not None:
                (yr, mth, dy, hr, mn, sec, wd, yd, isdst, _) = sourceTime
                self.dateFlag = 1

                if (hr != 0) and (mn != 0) and (sec != 0):
                    self.timeFlag = 2

                sourceTime = (yr, mth, dy, hr, mn, sec, wd, yd, isdst)

        # Given string date is a W3CDTF date
        if sourceTime is None:
            sourceTime = _parse_date_w3dtf(s)

            if sourceTime is not None:
                self.dateFlag = 1
                self.timeFlag = 2

        if sourceTime is None:
            s = s.lower()

        # Given string is in the format HH:MM(:SS)(am/pm)
        if self.meridianFlag:
            if sourceTime is None:
                (yr, mth, dy, hr, mn, sec, wd, yd, isdst) = now
            else:
                (yr, mth, dy, hr, mn, sec, wd, yd, isdst) = sourceTime

            m = self.ptc.CRE_TIMEHMS2.search(s)
            if m is not None:
                dt = s[:m.start('meridian')].strip()
                if len(dt) <= 2:
                    hr  = int(dt)
                    mn  = 0
                    sec = 0
                else:
                    hr, mn, sec = _extract_time(m)

                if hr == 24:
                    hr = 0

                sourceTime = (yr, mth, dy, hr, mn, sec, wd, yd, isdst)
                meridian   = m.group('meridian').lower()

                  # if 'am' found and hour is 12 - force hour to 0 (midnight)
                if (meridian in self.ptc.am) and hr == 12:
                    sourceTime = (yr, mth, dy, 0, mn, sec, wd, yd, isdst)

                  # if 'pm' found and hour < 12, add 12 to shift to evening
                if (meridian in self.ptc.pm) and hr < 12:
                    sourceTime = (yr, mth, dy, hr + 12, mn, sec, wd, yd, isdst)

              # invalid time
            if hr > 24 or mn > 59 or sec > 59:
                sourceTime    = now
                self.dateFlag = 0
                self.timeFlag = 0

            self.meridianFlag = False

          # Given string is in the format HH:MM(:SS)
        if self.timeStdFlag:
            if sourceTime is None:
                (yr, mth, dy, hr, mn, sec, wd, yd, isdst) = now
            else:
                (yr, mth, dy, hr, mn, sec, wd, yd, isdst) = sourceTime

            m = self.ptc.CRE_TIMEHMS.search(s)
            if m is not None:
                hr, mn, sec = _extract_time(m)
            if hr == 24:
                hr = 0

            if hr > 24 or mn > 59 or sec > 59:
                # invalid time
                sourceTime    = now
                self.dateFlag = 0
                self.timeFlag = 0
            else:
                sourceTime = (yr, mth, dy, hr, mn, sec, wd, yd, isdst)

            self.timeStdFlag = False

        # Given string is in the format 07/21/2006
        if self.dateStdFlag:
            sourceTime       = self.parseDate(s)
            self.dateStdFlag = False

        # Given string is in the format  "May 23rd, 2005"
        if self.dateStrFlag:
            sourceTime       = self.parseDateText(s)
            self.dateStrFlag = False

        # Given string is a weekday
        if self.weekdyFlag:
            (yr, mth, dy, hr, mn, sec, wd, yd, isdst) = now

            start = datetime.datetime(yr, mth, dy, hr, mn, sec)
            wkdy  = self.ptc.WeekdayOffsets[s]

            if wkdy > wd:
                qty = self._CalculateDOWDelta(wd, wkdy, 2,
                                              self.ptc.DOWParseStyle,
                                              self.ptc.CurrentDOWParseStyle)
            else:
                qty = self._CalculateDOWDelta(wd, wkdy, 2,
                                              self.ptc.DOWParseStyle,
                                              self.ptc.CurrentDOWParseStyle)

            target = start + datetime.timedelta(days=qty)
            wd     = wkdy

            sourceTime      = target.timetuple()
            self.weekdyFlag = False

        # Given string is a natural language time string like
        # lunch, midnight, etc
        if self.timeStrFlag:
            if s in self.ptc.re_values['now']:
                sourceTime = now
            else:
                sources = self.ptc.buildSources(sourceTime)

                if s in sources:
                    sourceTime = sources[s]
                else:
                    sourceTime    = now
                    self.dateFlag = 0
                    self.timeFlag = 0

            self.timeStrFlag = False

        # Given string is a natural language date string like today, tomorrow..
        if self.dayStrFlag:
            if sourceTime is None:
                sourceTime = now

            (yr, mth, dy, hr, mn, sec, wd, yd, isdst) = sourceTime

            if s in self.ptc.dayOffsets:
                offset = self.ptc.dayOffsets[s]
            else:
                offset = 0

            start      = datetime.datetime(yr, mth, dy, 9, 0, 0)
            target     = start + datetime.timedelta(days=offset)
            sourceTime = target.timetuple()

            self.dayStrFlag = False

        # Given string is a time string with units like "5 hrs 30 min"
        if self.unitsFlag:
            modifier = ''  # TODO

            if sourceTime is None:
                sourceTime = now

            m = self.ptc.CRE_UNITS.search(s)
            if m is not None:
                units    = m.group('units')
                quantity = s[:m.start('units')]

            sourceTime     = self._buildTime(sourceTime, quantity, modifier, units)
            self.unitsFlag = False

        # Given string is a time string with single char units like "5 h 30 m"
        if self.qunitsFlag:
            modifier = ''  # TODO

            if sourceTime is None:
                sourceTime = now

            m = self.ptc.CRE_QUNITS.search(s)
            if m is not None:
                units    = m.group('qunits')
                quantity = s[:m.start('qunits')]

            sourceTime      = self._buildTime(sourceTime, quantity, modifier, units)
            self.qunitsFlag = False

          # Given string does not match anything
        if sourceTime is None:
            sourceTime    = now
            self.dateFlag = 0
            self.timeFlag = 0

        return sourceTime


    def parse(self, datetimeString, sourceTime=None):
        """
        Splits the given C{datetimeString} into tokens, finds the regex
        patterns that match and then calculates a C{struct_time} value from
        the chunks.

        If C{sourceTime} is given then the C{struct_time} value will be
        calculated from that value, otherwise from the current date/time.

        If the C{datetimeString} is parsed and date/time value found then
        the second item of the returned tuple will be a flag to let you know
        what kind of C{struct_time} value is being returned::

            0 = not parsed at all
            1 = parsed as a C{date}
            2 = parsed as a C{time}
            3 = parsed as a C{datetime}

        @type  datetimeString: string
        @param datetimeString: date/time text to evaluate
        @type  sourceTime:     struct_time
        @param sourceTime:     C{struct_time} value to use as the base

        @rtype:  tuple
        @return: tuple of: modified C{sourceTime} and the result flag
        """

        if sourceTime:
            if isinstance(sourceTime, datetime.datetime):
                if _debug:
                    print 'coercing datetime to timetuple'
                sourceTime = sourceTime.timetuple()
            else:
                if not isinstance(sourceTime, time.struct_time) and \
                   not isinstance(sourceTime, tuple):
                    raise Exception('sourceTime is not a struct_time')

        s         = datetimeString.strip().lower()
        parseStr  = ''
        totalTime = sourceTime

        if s == '' :
            if sourceTime is not None:
                return (sourceTime, self.dateFlag + self.timeFlag)
            else:
                return (time.localtime(), 0)

        self.timeFlag = 0
        self.dateFlag = 0

        while len(s) > 0:
            flag   = False
            chunk1 = ''
            chunk2 = ''

            if _debug:
                print 'parse (top of loop): [%s][%s]' % (s, parseStr)

            if parseStr == '':
                # Modifier like next\prev..
                m = self.ptc.CRE_MODIFIER.search(s)
                if m is not None:
                    self.modifierFlag = True
                    if (m.group('modifier') != s):
                        # capture remaining string
                        parseStr = m.group('modifier')
                        chunk1   = s[:m.start('modifier')].strip()
                        chunk2   = s[m.end('modifier'):].strip()
                        flag     = True
                    else:
                        parseStr = s

            if parseStr == '':
                # Modifier like from\after\prior..
                m = self.ptc.CRE_MODIFIER2.search(s)
                if m is not None:
                    self.modifier2Flag = True
                    if (m.group('modifier') != s):
                        # capture remaining string
                        parseStr = m.group('modifier')
                        chunk1   = s[:m.start('modifier')].strip()
                        chunk2   = s[m.end('modifier'):].strip()
                        flag     = True
                    else:
                        parseStr = s

            if parseStr == '':
                valid_date = False
                for match in self.ptc.CRE_DATE3.finditer(s):
                    # to prevent "HH:MM(:SS) time strings" expressions from triggering
                    # this regex, we checks if the month field exists in the searched 
                    # expression, if it doesn't exist, the date field is not valid
                    if match.group('mthname'):
                        m = self.ptc.CRE_DATE3.search(s, match.start())
                        valid_date = True
                        break

                # String date format
                if valid_date:
                    self.dateStrFlag = True
                    self.dateFlag    = 1
                    if (m.group('date') != s):
                        # capture remaining string
                        parseStr = m.group('date')
                        chunk1   = s[:m.start('date')]
                        chunk2   = s[m.end('date'):]
                        s        = '%s %s' % (chunk1, chunk2)
                        flag     = True
                    else:
                        parseStr = s

            if parseStr == '':
                # Standard date format
                m = self.ptc.CRE_DATE.search(s)
                if m is not None:
                    self.dateStdFlag = True
                    self.dateFlag    = 1
                    if (m.group('date') != s):
                        # capture remaining string
                        parseStr = m.group('date')
                        chunk1   = s[:m.start('date')]
                        chunk2   = s[m.end('date'):]
                        s        = '%s %s' % (chunk1, chunk2)
                        flag     = True
                    else:
                        parseStr = s

            if parseStr == '':
                # Natural language day strings
                m = self.ptc.CRE_DAY.search(s)
                if m is not None:
                    self.dayStrFlag = True
                    self.dateFlag   = 1
                    if (m.group('day') != s):
                        # capture remaining string
                        parseStr = m.group('day')
                        chunk1   = s[:m.start('day')]
                        chunk2   = s[m.end('day'):]
                        s        = '%s %s' % (chunk1, chunk2)
                        flag     = True
                    else:
                        parseStr = s

            if parseStr == '':
                # Quantity + Units
                m = self.ptc.CRE_UNITS.search(s)
                if m is not None:
                    self.unitsFlag = True
                    if (m.group('qty') != s):
                        # capture remaining string
                        parseStr = m.group('qty')
                        chunk1   = s[:m.start('qty')].strip()
                        chunk2   = s[m.end('qty'):].strip()

                        if chunk1[-1:] == '-':
                            parseStr = '-%s' % parseStr
                            chunk1   = chunk1[:-1]

                        s    = '%s %s' % (chunk1, chunk2)
                        flag = True
                    else:
                        parseStr = s

            if parseStr == '':
                # Quantity + Units
                m = self.ptc.CRE_QUNITS.search(s)
                if m is not None:
                    self.qunitsFlag = True

                    if (m.group('qty') != s):
                        # capture remaining string
                        parseStr = m.group('qty')
                        chunk1   = s[:m.start('qty')].strip()
                        chunk2   = s[m.end('qty'):].strip()

                        if chunk1[-1:] == '-':
                            parseStr = '-%s' % parseStr
                            chunk1   = chunk1[:-1]

                        s    = '%s %s' % (chunk1, chunk2)
                        flag = True
                    else:
                        parseStr = s 

            if parseStr == '':
                # Weekday
                m = self.ptc.CRE_WEEKDAY.search(s)
                if m is not None:
                    gv = m.group('weekday')
                    if s not in self.ptc.dayOffsets:
                        self.weekdyFlag = True
                        self.dateFlag   = 1
                        if (gv != s):
                            # capture remaining string
                            parseStr = gv
                            chunk1   = s[:m.start('weekday')]
                            chunk2   = s[m.end('weekday'):]
                            s        = '%s %s' % (chunk1, chunk2)
                            flag     = True
                        else:
                            parseStr = s

            if parseStr == '':
                # Natural language time strings
                m = self.ptc.CRE_TIME.search(s)
                if m is not None:
                    self.timeStrFlag = True
                    self.timeFlag    = 2
                    if (m.group('time') != s):
                        # capture remaining string
                        parseStr = m.group('time')
                        chunk1   = s[:m.start('time')]
                        chunk2   = s[m.end('time'):]
                        s        = '%s %s' % (chunk1, chunk2)
                        flag     = True
                    else:
                        parseStr = s

            if parseStr == '':
                # HH:MM(:SS) am/pm time strings
                m = self.ptc.CRE_TIMEHMS2.search(s)
                if m is not None:
                    self.meridianFlag = True
                    self.timeFlag     = 2
                    if m.group('minutes') is not None:
                        if m.group('seconds') is not None:
                            parseStr = '%s:%s:%s %s' % (m.group('hours'),
                                                        m.group('minutes'),
                                                        m.group('seconds'),
                                                        m.group('meridian'))
                        else:
                            parseStr = '%s:%s %s' % (m.group('hours'),
                                                     m.group('minutes'),
                                                     m.group('meridian'))
                    else:
                        parseStr = '%s %s' % (m.group('hours'),
                                              m.group('meridian'))

                    chunk1 = s[:m.start('hours')]
                    chunk2 = s[m.end('meridian'):]

                    s    = '%s %s' % (chunk1, chunk2)
                    flag = True

            if parseStr == '':
                # HH:MM(:SS) time strings
                m = self.ptc.CRE_TIMEHMS.search(s)
                if m is not None:
                    self.timeStdFlag = True
                    self.timeFlag    = 2
                    if m.group('seconds') is not None:
                        parseStr = '%s:%s:%s' % (m.group('hours'),
                                                 m.group('minutes'),
                                                 m.group('seconds'))
                        chunk1   = s[:m.start('hours')]
                        chunk2   = s[m.end('seconds'):]
                    else:
                        parseStr = '%s:%s' % (m.group('hours'),
                                              m.group('minutes'))
                        chunk1   = s[:m.start('hours')]
                        chunk2   = s[m.end('minutes'):]

                    s    = '%s %s' % (chunk1, chunk2)
                    flag = True

            # if string does not match any regex, empty string to
            # come out of the while loop
            if not flag:
                s = ''

            if _debug:
                print 'parse (bottom) [%s][%s][%s][%s]' % (s, parseStr, chunk1, chunk2)
                print 'weekday %s, dateStd %s, dateStr %s, time %s, timeStr %s, meridian %s' % \
                       (self.weekdyFlag, self.dateStdFlag, self.dateStrFlag, self.timeStdFlag, self.timeStrFlag, self.meridianFlag)
                print 'dayStr %s, modifier %s, modifier2 %s, units %s, qunits %s' % \
                       (self.dayStrFlag, self.modifierFlag, self.modifier2Flag, self.unitsFlag, self.qunitsFlag)

            # evaluate the matched string
            if parseStr != '':
                if self.modifierFlag == True:
                    t, totalTime = self._evalModifier(parseStr, chunk1, chunk2, totalTime)
                    # t is the unparsed part of the chunks.
                    # If it is not date/time, return current
                    # totalTime as it is; else return the output
                    # after parsing t.
                    if (t != '') and (t != None):
                        tempDateFlag       = self.dateFlag
                        tempTimeFlag       = self.timeFlag
                        (totalTime2, flag) = self.parse(t, totalTime)

                        if flag == 0 and totalTime is not None:
                            self.timeFlag = tempTimeFlag
                            self.dateFlag = tempDateFlag

                            return (totalTime, self.dateFlag + self.timeFlag)
                        else:
                            return (totalTime2, self.dateFlag + self.timeFlag)

                elif self.modifier2Flag == True:
                    totalTime, invalidFlag = self._evalModifier2(parseStr, chunk1, chunk2, totalTime)

                    if invalidFlag == True:
                        self.dateFlag = 0
                        self.timeFlag = 0

                else:
                    totalTime = self._evalString(parseStr, totalTime)
                    parseStr  = ''

        # String is not parsed at all
        if totalTime is None or totalTime == sourceTime:
            totalTime     = time.localtime()
            self.dateFlag = 0
            self.timeFlag = 0

        return (totalTime, self.dateFlag + self.timeFlag)


    def inc(self, source, month=None, year=None):
        """
        Takes the given C{source} date, or current date if none is
        passed, and increments it according to the values passed in
        by month and/or year.

        This routine is needed because Python's C{timedelta()} function
        does not allow for month or year increments.

        @type  source: struct_time
        @param source: C{struct_time} value to increment
        @type  month:  integer
        @param month:  optional number of months to increment
        @type  year:   integer
        @param year:   optional number of years to increment

        @rtype:  datetime
        @return: C{source} incremented by the number of months and/or years
        """
        yr  = source.year
        mth = source.month
        dy  = source.day

        if year:
            try:
                yi = int(year)
            except ValueError:
                yi = 0

            yr += yi

        if month:
            try:
                mi = int(month)
            except ValueError:
                mi = 0

            m = abs(mi)
            y = m / 12      # how many years are in month increment
            m = m % 12      # get remaining months

            if mi < 0:
                mth = mth - m           # sub months from start month
                if mth < 1:             # cross start-of-year?
                    y   -= 1            #   yes - decrement year
                    mth += 12           #         and fix month
            else:
                mth = mth + m           # add months to start month
                if mth > 12:            # cross end-of-year?
                    y   += 1            #   yes - increment year
                    mth -= 12           #         and fix month

            yr += y

            # if the day ends up past the last day of
            # the new month, set it to the last day
            if dy > self.ptc.daysInMonth(mth, yr):
                dy = self.ptc.daysInMonth(mth, yr)

        d = source.replace(year=yr, month=mth, day=dy)

        return source + (d - source)

