#!/usr/bin/env python

"""
Parse human-readable date/time text.
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

_debug = False


import string, re, time
import datetime, calendar, rfc822
import parsedatetime_consts


# Copied from feedparser.py
# Universal Feedparser, Copyright (c) 2002-2006, Mark Pilgrim, All rights reserved.
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
# Universal Feedparser, Copyright (c) 2002-2006, Mark Pilgrim, All rights reserved.
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
# Universal Feedparser, Copyright (c) 2002-2006, Mark Pilgrim, All rights reserved.
# Modified to return a tuple instead of mktime
#
# Original comment:
#       W3DTF-style date parsing adapted from PyXML xml.utils.iso8601, written by
#       Drake and licensed under the Python license.  Removed all range checking
#       for month, day, hour, minute, and second, since mktime will normalize
#       these later
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
# Universal Feedparser, Copyright (c) 2002-2006, Mark Pilgrim, All rights reserved.
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
_additional_timezones = {'AT': -400, 'ET': -500, 'CT': -600, 'MT': -700, 'PT': -800}
rfc822._timezones.update(_additional_timezones)


class Calendar:
    """
    A collection of routines to input, parse and manipulate date and times.
    The text can either be 'normal' date values or it can be human readable.
    """

    def __init__(self, constants=None):
        """
        Default constructor for the Calendar class.

        @type  constants: object
        @param constants: Instance of the class L{CalendarConstants}

        @rtype:  object
        @return: Calendar instance
        """
          # if a constants reference is not included, use default
        if constants is None:
            self.ptc = parsedatetime_consts.Constants()
        else:
            self.ptc = constants

        self.CRE_SPECIAL   = re.compile(self.ptc.RE_SPECIAL,   re.IGNORECASE)
        self.CRE_UNITS     = re.compile(self.ptc.RE_UNITS,     re.IGNORECASE)
        self.CRE_QUNITS    = re.compile(self.ptc.RE_QUNITS,    re.IGNORECASE)
        self.CRE_MODIFIER  = re.compile(self.ptc.RE_MODIFIER,  re.IGNORECASE)
        self.CRE_MODIFIER2 = re.compile(self.ptc.RE_MODIFIER2, re.IGNORECASE)
        self.CRE_TIMEHMS   = re.compile(self.ptc.RE_TIMEHMS,   re.IGNORECASE)
        self.CRE_TIMEHMS2  = re.compile(self.ptc.RE_TIMEHMS2,  re.IGNORECASE)
        self.CRE_DATE      = re.compile(self.ptc.RE_DATE,      re.IGNORECASE)
        self.CRE_DATE2     = re.compile(self.ptc.RE_DATE2,     re.IGNORECASE)
        self.CRE_DATE3     = re.compile(self.ptc.RE_DATE3,     re.IGNORECASE)
        self.CRE_MONTH     = re.compile(self.ptc.RE_MONTH,     re.IGNORECASE)
        self.CRE_WEEKDAY   = re.compile(self.ptc.RE_WEEKDAY,   re.IGNORECASE)
        self.CRE_DAY       = re.compile(self.ptc.RE_DAY,       re.IGNORECASE)
        self.CRE_TIME      = re.compile(self.ptc.RE_TIME,      re.IGNORECASE)
        self.CRE_REMAINING = re.compile(self.ptc.RE_REMAINING, re.IGNORECASE)

        #regex for date/time ranges
        self.CRE_RTIMEHMS  = re.compile(self.ptc.RE_RTIMEHMS,  re.IGNORECASE)
        self.CRE_RTIMEHMS2 = re.compile(self.ptc.RE_RTIMEHMS2, re.IGNORECASE)
        self.CRE_RDATE     = re.compile(self.ptc.RE_RDATE,     re.IGNORECASE)
        self.CRE_RDATE3    = re.compile(self.ptc.RE_RDATE3,    re.IGNORECASE)

        self.CRE_TIMERNG1  = re.compile(self.ptc.TIMERNG1, re.IGNORECASE)
        self.CRE_TIMERNG2  = re.compile(self.ptc.TIMERNG2, re.IGNORECASE)
        self.CRE_TIMERNG3  = re.compile(self.ptc.TIMERNG3, re.IGNORECASE)
        self.CRE_DATERNG1  = re.compile(self.ptc.DATERNG1, re.IGNORECASE)
        self.CRE_DATERNG2  = re.compile(self.ptc.DATERNG2, re.IGNORECASE)
        self.CRE_DATERNG3  = re.compile(self.ptc.DATERNG3, re.IGNORECASE)

        self.invalidFlag   = False  # Is set if the datetime string entered cannot be parsed at all
        self.weekdyFlag    = False  # monday/tuesday/...
        self.dateStdFlag   = False  # 07/21/06
        self.dateStrFlag   = False  # July 21st, 2006
        self.timeFlag      = False  # 5:50 
        self.meridianFlag  = False  # am/pm
        self.dayStrFlag    = False  # tomorrow/yesterday/today/..
        self.timeStrFlag   = False  # lunch/noon/breakfast/...
        self.modifierFlag  = False  # after/before/prev/next/..
        self.modifier2Flag = False  # after/before/prev/next/..
        self.unitsFlag     = False  # hrs/weeks/yrs/min/..
        self.qunitsFlag    = False  # h/m/t/d..


    def _convertUnitAsWords(self, unitText):
        """
        Converts text units into their number value

        Five = 5
        Twenty Five = 25
        Two hundred twenty five = 225
        Two thousand and twenty five = 2025
        Two thousand twenty five = 2025

        @type  unitText: string
        @param unitText: number string

        @rtype:  integer
        @return: numerical value of unitText
        """
        # TODO: implement this
        pass


    def _buildTime(self, source, quantity, modifier, units):
        """
        Take quantity, modifier and unit strings and convert them into values.
        Then calcuate the time and return the adjusted sourceTime

        @type  source:   time
        @param source:   time to use as the base (or source)
        @type  quantity: string
        @param quantity: quantity string
        @type  modifier: string
        @param modifier: how quantity and units modify the source time
        @type  units:    string
        @param units:    unit of the quantity (i.e. hours, days, months, etc)

        @rtype:  timetuple
        @return: timetuple of the calculated time
        """
        if _debug:
            print '_buildTime: [%s][%s][%s]' % (quantity, modifier, units)

        if source is None:
            source = time.localtime()

        if quantity is None:
            quantity = ''
        else:
            quantity = string.strip(quantity)

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

        (yr, mth, dy, hr, mn, sec, wd, yd, isdst) = source

        start  = datetime.datetime(yr, mth, dy, hr, mn, sec)
        target = start

        if units.startswith('y'):
            target = self.inc(start, year=qty)
        elif units.endswith('th') or units.endswith('ths'):
            target = self.inc(start, month=qty)
        else:
            if units.startswith('d'):
                target = start + datetime.timedelta(days=qty)
            elif units.startswith('h'):
                target = start + datetime.timedelta(hours=qty)
            elif units.startswith('m'):
                target = start + datetime.timedelta(minutes=qty)
            elif units.startswith('s'):
                target = start + datetime.timedelta(seconds=qty)
            elif units.startswith('w'):
                target = start + datetime.timedelta(weeks=qty)

        if target != start:
            self.invalidFlag = False

        return target.timetuple()


    def parseDate(self, dateString):
        """
        Parses strings like 05/28/200 or 04.21

        @type  dateString: string
        @param dateString: text to convert to a datetime

        @rtype:  datetime
        @return: calculated datetime value of dateString
        """
        yr, mth, dy, hr, mn, sec, wd, yd, isdst = time.localtime()

        s = dateString
        m = self.CRE_DATE2.search(s)
        if m is not None:
            index = m.start()
            mth   = int(s[:index])
            s     = s[index + 1:]

        m = self.CRE_DATE2.search(s)
        if m is not None:
            index = m.start()
            dy    = int(s[:index])
            yr    = int(s[index + 1:])
            # TODO should this have a birthday epoch constraint?
            if yr < 99:
                yr += 2000
        else:
            dy = int(string.strip(s))

        if (mth > 0 and mth <= 12) and (dy > 0 and dy <= self.ptc.DaysInMonthList[mth - 1]):
            sourceTime = (yr, mth, dy, hr, mn, sec, wd, yd, isdst)
        else:
            self.invalidFlag = True
            sourceTime       = time.localtime() #return current time if date string is invalid

        return sourceTime


    def parseDateText(self, dateString):
        """
        Parses strings like "May 31st, 2006" or "Jan 1st" or "July 2006"

        @type  dateString: string
        @param dateString: text to convert to a datetime

        @rtype:  datetime
        @return: calculated datetime value of dateString
        """
        yr, mth, dy, hr, mn, sec, wd, yd, isdst = time.localtime()

        currentMth = mth
        currentDy  = dy

        s   = dateString.lower()
        m   = self.CRE_DATE3.search(s)
        mth = m.group('mthname')
        mth = self.ptc.MonthOffsets[mth]

        if m.group('day') !=  None:
            dy = int(m.group('day'))
        else:
            dy = 1

        if m.group('year') !=  None:
            yr = int(m.group('year'))
        elif (mth < currentMth) or (mth == currentMth and dy < currentDy):
            # if that day and month have already passed in this year,
            # then increment the year by 1
            yr += 1

        if dy > 0 and dy <= self.ptc.DaysInMonthList[mth - 1]:
            sourceTime = (yr, mth, dy, 9, 0, 0, wd, yd, isdst)
        else:
              # Return current time if date string is invalid
            self.invalidFlag = True
            sourceTime       = time.localtime()

        return sourceTime


    def evalRanges(self, datetimeString, sourceTime=None):
        """
        Evaluates the strings with time or date ranges

        @type  datetimeString: string
        @param datetimeString: datetime text to evaluate
        @type  sourceTime:     datetime
        @param sourceTime:     datetime value to use as the base

        @rtype:  tuple
        @return: tuple of the start datetime, end datetime and the invalid flag
        """
        startTime = ''
        endTime   = ''
        startDate = ''
        endDate   = ''
        rangeFlag = 0

        s = string.strip(datetimeString.lower())

        m = self.CRE_TIMERNG1.search(s)
        if m is not None:
            rangeFlag = 1
        else:
            m = self.CRE_TIMERNG2.search(s)
            if m is not None:
                rangeFlag = 2
            else:
                m = self.CRE_TIMERNG3.search(s)
                if m is not None:
                    rangeFlag = 3
                else:
                    m = self.CRE_DATERNG1.search(s)
                    if m is not None:
                        rangeFlag = 4
                    else:
                        m = self.CRE_DATERNG2.search(s)
                        if m is not None:
                            rangeFlag = 5
                        else:
                            m = self.CRE_DATERNG3.search(s)
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

                if flag == True:
                    sourceTime = None
            else:
                parseStr = s

        if rangeFlag == 1:
            # FIXME hardcoded seperator
            m                = re.search('-', parseStr)
            startTime, sflag = self.parse((parseStr[:m.start()]),       sourceTime)
            endTime, eflag   = self.parse((parseStr[(m.start() + 1):]), sourceTime)

            if eflag is False and sflag is False:
                return (startTime, endTime, False)

        elif rangeFlag == 2:
            # FIXME hardcoded seperator
            m                = re.search('-', parseStr)
            startTime, sflag = self.parse((parseStr[:m.start()]), sourceTime)
            endTime, eflag   = self.parse((parseStr[(m.start() + 1):]), sourceTime)

            if eflag is False and sflag is False:
                return (startTime, endTime, False)

        elif rangeFlag == 3:
            # FIXME hardcoded seperator
            m = re.search('-', parseStr)

            # capturing the meridian from the end time
            # FIXME hardcoded meridian
            if self.ptc.usesMeridian:
                ampm = re.search('a', parseStr)

                # appending the meridian to the start time
                if ampm is not None:
                    startTime, sflag = self.parse((parseStr[:m.start()] + self.ptc.meridian[0]), sourceTime)
                else:
                    startTime, sflag = self.parse((parseStr[:m.start()] + self.ptc.meridian[1]), sourceTime)
            else:
                startTime, sflag = self.parse((parseStr[:m.start()]), sourceTime)

            endTime, eflag = self.parse(parseStr[(m.start() + 1):], sourceTime)

            if eflag is False and sflag is False:
                return (startTime, endTime, False)

        elif rangeFlag == 4:
            # FIXME hardcoded seperator
            m                = re.search('-', parseStr)
            startDate, sflag = self.parse((parseStr[:m.start()]),       sourceTime)
            endDate, eflag   = self.parse((parseStr[(m.start() + 1):]), sourceTime)

            if eflag is False and sflag is False:
                return (startDate, endDate, False)

        elif rangeFlag == 5:
            # FIXME hardcoded seperator
            m       = re.search('-', parseStr)
            endDate = parseStr[(m.start() + 1):]

            # capturing the year from the end date
            date    = self.CRE_DATE3.search(endDate)
            endYear = date.group('year')

            # appending the year to the start date if the start date
            # does not have year information and the end date does.
            # eg : "Aug 21 - Sep 4, 2007"
            if endYear is not None:
                startDate = parseStr[:m.start()]
                date      = self.CRE_DATE3.search(startDate)
                startYear = date.group('year')

                if startYear is None:
                    startDate += endYear
            else:
                startDate = parseStr[:m.start()]

            startDate, sflag = self.parse(startDate, sourceTime)
            endDate, eflag   = self.parse(endDate, sourceTime)

            if eflag is False and sflag is False:
                return (startDate, endDate, False)

        elif rangeFlag == 6:
            # FIXME hardcoded seperator
            m = re.search('-', parseStr)

            startDate = parseStr[:m.start()]

            # capturing the month from the start date
            mth = self.CRE_DATE3.search(startDate)
            mth = mth.group('mthname')

            # appending the month name to the end date
            endDate = mth + parseStr[(m.start() + 1):]

            startDate, sflag = self.parse(startDate, sourceTime)
            endDate, eflag   = self.parse(endDate, sourceTime)

            if eflag is False and sflag is False:
                return (startDate, endDate, False)
        else:
            # if range is not found
            sourceTime = time.localtime()

            return (sourceTime, sourceTime, True)


    def _evalModifier(self, modifier, chunk1, chunk2, sourceTime):
        """
        Evaluate the modifier string and following text (passed in
        as chunk1 and chunk2) and if they match any known modifiers
        calculate the delta and apply it to sourceTime

        @type  modifier:   string
        @param modifier:   modifier text to apply to sourceTime
        @type  chunk1:     string
        @param chunk1:     first text chunk that followed modifier (if any)
        @type  chunk2:     string
        @param chunk2:     second text chunk that followed modifier (if any)
        @type  sourceTime: datetime
        @param sourceTime: datetime value to use as the base

        @rtype:  tuple
        @return: tuple of any remaining text and the modified sourceTime
        """
        offset = self.ptc.Modifiers[modifier]

        if sourceTime is not None:
            (yr, mth, dy, hr, mn, sec, wd, yd, isdst) = sourceTime
        else:
            (yr, mth, dy, hr, mn, sec, wd, yd, isdst) = time.localtime()

        # capture the units after the modifier and the remaining string after the unit
        m = self.CRE_REMAINING.search(chunk2)
        if m is not None:
            index  = m.start() + 1
            unit   = chunk2[:m.start()]
            chunk2 = chunk2[index:]
        else:
            unit   = chunk2
            chunk2 = ''

        flag = False

        if unit == 'month' or \
           unit == 'mth':
            if offset == 0:
                dy         = self.ptc.DaysInMonthList[mth - 1]
                sourceTime = (yr, mth, dy, 9, 0, 0, wd, yd, isdst)
            elif offset == 2:
                # if day is the last day of the month, calculate the last day of the next month
                if dy == self.ptc.DaysInMonthList[mth - 1]:
                    dy = self.ptc.DaysInMonthList[mth]

                start      = datetime.datetime(yr, mth, dy, 9, 0, 0)
                target     = self.inc(start, month=1)
                sourceTime = target.timetuple()
            else:
                start      = datetime.datetime(yr, mth, 1, 9, 0, 0)
                target     = self.inc(start, month=offset)
                sourceTime = target.timetuple()

            flag = True

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

            flag = True

        if unit == 'day' or \
            unit == 'dy' or \
            unit == 'd':
            if offset == 0:
                sourceTime = (yr, mth, dy, 17, 0, 0, wd, yd, isdst)
            elif offset == 2:
                start      = datetime.datetime(yr, mth, dy, hr, mn, sec)
                target     = start + datetime.timedelta(days=1)
                sourceTime = target.timetuple()
            else:
                start      = datetime.datetime(yr, mth, dy, 9, 0, 0)
                target     = start + datetime.timedelta(days=offset)
                sourceTime = target.timetuple()

            flag = True

        if unit == 'hour' or \
           unit == 'hr':
            if offset == 0:
                sourceTime = (yr, mth, dy, hr, 0, 0, wd, yd, isdst)
            else:
                start      = datetime.datetime(yr, mth, dy, hr, 0, 0)
                target     = start + datetime.timedelta(hours=offset)
                sourceTime = target.timetuple()

            flag = True

        if unit == 'year' or \
             unit == 'yr' or \
             unit == 'y':
            if offset == 0:
                sourceTime = (yr, 12, 31, hr, mn, sec, wd, yd, isdst)
            elif offset == 2:
                sourceTime = (yr + 1, mth, dy, hr, mn, sec, wd, yd, isdst)
            else:
                sourceTime = (yr + offset, 1, 1, 9, 0, 0, wd, yd, isdst)

            flag = True

        if flag == False:
            m = self.CRE_WEEKDAY.match(unit)
            if m is not None:
                wkdy = m.group()
                wkdy = self.ptc.WeekdayOffsets[wkdy]

                if offset == 0:
                    diff       = wkdy - wd
                    start      = datetime.datetime(yr, mth, dy, 9, 0, 0)
                    target     = start + datetime.timedelta(days=diff)
                    sourceTime = target.timetuple()
                else:
                    diff       = wkdy - wd
                    start      = datetime.datetime(yr, mth, dy, 9, 0, 0)
                    target     = start + datetime.timedelta(days=diff + 7 * offset)
                    sourceTime = target.timetuple()

                flag = True

        if not flag:
            m = self.CRE_TIME.match(unit)
            if m is not None:
                (yr, mth, dy, hr, mn, sec, wd, yd, isdst), self.invalidFlag = self.parse(unit)
                start      = datetime.datetime(yr, mth, dy, hr, mn, sec)
                target     = start + datetime.timedelta(days=offset)
                sourceTime = target.timetuple()

                flag              = True
                self.modifierFlag = False

        # if the word after next is a number, the string is likely
        # to be something like "next 4 hrs" for which we have to
        # combine the units with the rest of the string
        if not flag:
            if offset < 0:
                # if offset is negative, the unit has to be made negative
                unit = '-%s' % unit

            chunk2 = '%s %s' % (unit, chunk2)

        self.modifierFlag = False

        return '%s %s' % (chunk1, chunk2), sourceTime


    def _evalModifier2(self, modifier, chunk1 , chunk2, sourceTime):
        """
        Evaluate the modifier string and following text (passed in
        as chunk1 and chunk2) and if they match any known modifiers
        calculate the delta and apply it to sourceTime

        @type  modifier:   string
        @param modifier:   modifier text to apply to sourceTime
        @type  chunk1:     string
        @param chunk1:     first text chunk that followed modifier (if any)
        @type  chunk2:     string
        @param chunk2:     second text chunk that followed modifier (if any)
        @type  sourceTime: datetime
        @param sourceTime: datetime value to use as the base

        @rtype:  tuple
        @return: tuple of any remaining text and the modified sourceTime
        """
        offset = self.ptc.Modifiers[modifier]
        digit  = r'\d+'

        if sourceTime is not None:
            (yr, mth, dy, hr, mn, sec, wd, yd, isdst) = sourceTime
        else:
            (yr, mth, dy, hr, mn, sec, wd, yd, isdst) = time.localtime()

        self.modifier2Flag = False

        # If the string after the negative modifier starts with
        # digits, then it is likely that the string is similar to
        # " before 3 days" or 'evening prior to 3 days'.
        # In this case, the total time is calculated by subtracting
        # '3 days' from the current date.
        # So, we have to identify the quantity and negate it before
        # parsing the string.
        # This is not required for strings not starting with digits
        # since the string is enough to calculate the sourceTime
        if offset < 0:
            m = re.match(digit, string.strip(chunk2))
            if m is not None:
                qty    = int(m.group()) * -1
                chunk2 = chunk2[m.end():]
                chunk2 = '%d%s' % (qty, chunk2)

        sourceTime, flag = self.parse(chunk2, sourceTime)

        if chunk1 != '':
            if offset < 0:
                m = re.match(digit, string.strip(chunk1))
                if m is not None:
                    qty    = int(m.group()) * -1
                    chunk1 = chunk1[m.end():]
                    chunk1 = '%d%s' % (qty, chunk1)

            sourceTime, flag = self.parse(chunk1, sourceTime)

        return '', sourceTime


    def _evalString(self, datetimeString, sourceTime=None):
        """
        Calculate the datetime based on flags set by the L{parse()} routine

        Examples handled::
            RFC822, W3CDTF formatted dates
            HH:MM[:SS][ am/pm]
            MM/DD/YYYY
            DD MMMM YYYY

        @type  datetimeString: string
        @param datetimeString: text to try and parse as more "traditional" date/time text
        @type  sourceTime:     datetime
        @param sourceTime:     datetime value to use as the base

        @rtype:  datetime
        @return: calculated datetime value or current datetime if not parsed
        """
        s   = string.strip(datetimeString)
        now = time.localtime()

          # Given string date is a RFC822 date
        if sourceTime is None:
            sourceTime = _parse_date_rfc822(s)

          # Given string date is a W3CDTF date
        if sourceTime is None:
            sourceTime = _parse_date_w3dtf(s)

        if sourceTime is None:
            s = s.lower()

          # Given string is in the format HH:MM(:SS)(am/pm)
        if self.meridianFlag:
            if sourceTime is None:
                (yr, mth, dy, hr, mn, sec, wd, yd, isdst) = now
            else:
                (yr, mth, dy, hr, mn, sec, wd, yd, isdst) = sourceTime

            m = self.CRE_TIMEHMS2.search(s)
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
                sourceTime       = now
                self.invalidFlag = True

            self.meridianFlag = False

          # Given string is in the format HH:MM(:SS)
        if self.timeFlag:
            if sourceTime is None:
                (yr, mth, dy, hr, mn, sec, wd, yd, isdst) = now
            else:
                (yr, mth, dy, hr, mn, sec, wd, yd, isdst) = sourceTime

            m = self.CRE_TIMEHMS.search(s)
            if m is not None:
                hr, mn, sec = _extract_time(m)
            if hr == 24:
                hr = 0

            if hr > 24 or mn > 59 or sec > 59:
                # invalid time
                sourceTime       = now
                self.invalidFlag = True
            else:
                sourceTime = (yr, mth, dy, hr, mn, sec, wd, yd, isdst)

            self.timeFlag = False

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
            wkDy  = self.ptc.WeekdayOffsets[s]

            if wkDy > wd:
                qty    = wkDy - wd
                target = start + datetime.timedelta(days=qty)
                wd     = wkDy
            else:
                qty    = 6 - wd + wkDy + 1
                target = start + datetime.timedelta(days=qty)
                wd     = wkDy

            sourceTime      = target.timetuple()
            self.weekdyFlag = False

          # Given string is a natural language time string like lunch, midnight, etc
        if self.timeStrFlag:
            if s in self.ptc.re_values['now']:
                sourceTime = now
            else:
                sources = self.ptc.buildSources(now)

                if s in sources:
                    sourceTime = sources[s]
                else:
                    sourceTime       = now
                    self.invalidFlag = True

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

            m = self.CRE_UNITS.search(s)
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

            m = self.CRE_QUNITS.search(s)
            if m is not None:
                units    = m.group('qunits')
                quantity = s[:m.start('qunits')]

            sourceTime      = self._buildTime(sourceTime, quantity, modifier, units)
            self.qunitsFlag = False

          # Given string does not match anything
        if sourceTime is None:
            sourceTime       = now
            self.invalidFlag = True

        return sourceTime


    def parse(self, datetimeString, sourceTime=None):
        """
        Splits the L{datetimeString} into tokens, finds the regex patters
        that match and then calculates a datetime value from the chunks

        if L{sourceTime} is given then the datetime value will be calcualted
        from that datetime, otherwise from the current datetime.

        @type  datetimeString: string
        @param datetimeString: datetime text to evaluate
        @type  sourceTime:     datetime
        @param sourceTime:     datetime value to use as the base

        @rtype:  tuple
        @return: tuple of any remaining text and the modified sourceTime
        """
        s         = string.strip(datetimeString.lower())
        dateStr   = ''
        parseStr  = ''
        totalTime = sourceTime

        self.invalidFlag = False

        if s == '' :
            if sourceTime is not None:
                return (sourceTime, False)
            else:
                return (time.localtime(), True)

        while len(s) > 0:
            flag   = False
            chunk1 = ''
            chunk2 = ''

            if _debug:
                print 'parse (top of loop): [%s][%s]' % (s, parseStr)

            if parseStr == '':
                # Modifier like next\prev..
                m = self.CRE_MODIFIER.search(s)
                if m is not None:
                    self.modifierFlag = True
                    if (m.group('modifier') != s):
                        # capture remaining string
                        parseStr = m.group('modifier')
                        chunk1   = string.strip(s[:m.start('modifier')])
                        chunk2   = string.strip(s[m.end('modifier'):])
                        flag     = True
                    else:
                        parseStr = s

            if parseStr == '':
                # Modifier like from\after\prior..
                m = self.CRE_MODIFIER2.search(s)
                if m is not None:
                    self.modifier2Flag = True
                    if (m.group('modifier') != s):
                        # capture remaining string
                        parseStr = m.group('modifier')
                        chunk1   = string.strip(s[:m.start('modifier')])
                        chunk2   = string.strip(s[m.end('modifier'):])
                        flag     = True
                    else:
                        parseStr = s

            if parseStr == '':
                # String date format
                m = self.CRE_DATE3.search(s)
                if m is not None:
                    self.dateStrFlag = True
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
                m = self.CRE_DATE.search(s)
                if m is not None:
                    self.dateStdFlag = True
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
                m = self.CRE_DAY.search(s)
                if m is not None:
                    self.dayStrFlag = True
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
                m = self.CRE_UNITS.search(s)
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
                m = self.CRE_QUNITS.search(s)
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
                m = self.CRE_WEEKDAY.search(s)
                if m is not None:
                    self.weekdyFlag = True
                    if (m.group('weekday') != s):
                        # capture remaining string
                        parseStr = m.group()
                        chunk1   = s[:m.start('weekday')]
                        chunk2   = s[m.end('weekday'):]
                        s        = '%s %s' % (chunk1, chunk2)
                        flag     = True
                    else:
                        parseStr = s

            if parseStr == '':
                # Natural language time strings
                m = self.CRE_TIME.search(s)
                if m is not None:
                    self.timeStrFlag = True
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
                m = self.CRE_TIMEHMS2.search(s)
                if m is not None:
                    self.meridianFlag = True
                    if m.group('minutes') is not None:
                        if m.group('seconds') is not None:
                            parseStr = '%s:%s:%s %s' % (m.group('hours'), m.group('minutes'), m.group('seconds'), m.group('meridian'))
                        else:
                            parseStr = '%s:%s %s' % (m.group('hours'), m.group('minutes'), m.group('meridian'))
                    else:
                        parseStr = '%s %s' % (m.group('hours'), m.group('meridian'))

                    chunk1 = s[:m.start('hours')]
                    chunk2 = s[m.end('meridian'):]

                    s    = '%s %s' % (chunk1, chunk2)
                    flag = True

            if parseStr == '':
                # HH:MM(:SS) time strings
                m = self.CRE_TIMEHMS.search(s)
                if m is not None:
                    self.timeFlag = True
                    if m.group('seconds') is not None:
                        parseStr = '%s:%s:%s' % (m.group('hours'), m.group('minutes'), m.group('seconds'))
                        chunk1   = s[:m.start('hours')]
                        chunk2   = s[m.end('seconds'):]
                    else:
                        parseStr = '%s:%s' % (m.group('hours'), m.group('minutes'))
                        chunk1   = s[:m.start('hours')]
                        chunk2   = s[m.end('minutes'):]

                    s    = '%s %s' % (chunk1, chunk2)
                    flag = True

            # if string does not match any regex, empty string to come out of the while loop
            if not flag:
                s = ''

            if _debug:
                print 'parse (bottom) [%s][%s][%s][%s]' % (s, parseStr, chunk1, chunk2)
                print 'invalid %s, weekday %s, dateStd %s, dateStr %s, time %s, timeStr %s, meridian %s' % \
                       (self.invalidFlag, self.weekdyFlag, self.dateStdFlag, self.dateStrFlag, self.timeFlag, self.timeStrFlag, self.meridianFlag)
                print 'dayStr %s, modifier %s, modifier2 %s, units %s, qunits %s' % \
                       (self.dayStrFlag, self.modifierFlag, self.modifier2Flag, self.unitsFlag, self.qunitsFlag)

            # evaluate the matched string
            if parseStr != '':
                if self.modifierFlag == True:
                    t, totalTime = self._evalModifier(parseStr, chunk1, chunk2, totalTime)

                    return self.parse(t, totalTime)

                elif self.modifier2Flag == True:
                    s, totalTime = self._evalModifier2(parseStr, chunk1, chunk2, totalTime)
                else:
                    totalTime = self._evalString(parseStr, totalTime)
                    parseStr  = ''

        # String is not parsed at all
        if totalTime is None or totalTime == sourceTime:
            totalTime        = time.localtime()
            self.invalidFlag = True

        return (totalTime, self.invalidFlag)


    def inc(self, source, month=None, year=None):
        """
        Takes the given date, or current date if none is passed, and
        increments it according to the values passed in by month
        and/or year.

        This routine is needed because the timedelta() routine does
        not allow for month or year increments.

        @type  source: datetime
        @param source: datetime value to increment
        @type  month:  integer
        @param month:  optional number of months to increment
        @type  year:   integer
        @param year:   optional number of years to increment

        @rtype:  datetime
        @return: L{source} incremented by the number of months and/or years
        """
        yr  = source.year
        mth = source.month

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

        d = source.replace(year=yr, month=mth)

        return source + (d - source)

