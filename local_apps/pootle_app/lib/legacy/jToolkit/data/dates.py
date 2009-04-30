# -*- coding: utf-8 -*-

"""jToolkit.data.dates is a module that handles date parsing and formatting"""

# Copyright 2002, 2003 St James Software
# 
# This file is part of jToolkit.
#
# jToolkit is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# jToolkit is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with jToolkit; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import time
import datetime
import calendar
from pootle_app.lib.legacy.jToolkit import cidict
import re

# pywintypes has an error in time formatting, so we need to be able to detect this type on windows
try:
  import pywintypes
  errortimetype = pywintypes.TimeType
except ImportError:
  errortimetype = None
except AttributeError:
  # TODO: write an error message - this means that pywintypes needs to be patched for __file__ AttributeError
  errortimetype = None

date = datetime.datetime
currentdate = datetime.datetime.now
datetimedelta = datetime.timedelta
def seconds(numseconds):
  return datetime.timedelta(seconds=numseconds)

def days(numdays):
  return datetime.timedelta(days=numdays)

#Returns a unique floating point number for that date
def mktime(date):
  return time.mktime(date.timetuple())

# we have copied _strptime from Python2.3 so that it can be used in earlier versions
if not hasattr(time, 'strptime'):
  def strptime(data_string, format="%a %b %d %H:%M:%S %Y"):
    raise NotImplementedError("You need to upgrade to Python 2.3 to use strptime")
  time.strptime = strptime

class ParseError(ValueError):
    pass

class dateparser:
    """a simulated type which can parse strings into dates given a format"""
    def __init__(self, format):
        """constructs a dateparser object with the given regular expression as a format"""
        self.r = re.compile(format)
        # remember format for error messages...
        self.format = format

    def __call__(self, *args):
        """simulates a constructor call for this dateparser"""
        if len(args) <> 1:
            raise ParseError("dateparser takes exactly 1 argument.")
        return self.parse(args[0])

    def parse(self, formatteddate):
        """uses the regular expression to parse a date and construct a date object"""
        match = self.r.match(formatteddate)
        if match is None:
          raise ParseError("cannot parse formatted date: "+repr(formatteddate)+" with format string: "+repr(self.format))
        g = match.groupdict()
        for key, value in g.items():
          if value is None:
            del g[key]
        now = currentdate().timetuple()
        Y, M, D, h, m, s = [g.get(field,"0") for field in 'Y','M','D','h','m','s']
        # for two-digit years, get closest year
        if len(Y) == 2:
          Y = int(Y)
          currentY = now[0]
          century, offset = currentY // 100, currentY % 100
          if Y - offset >= 50:
            Y = (century-1)*100 + Y
          elif Y - offset <= -50:
            Y = (century+1)*100 + Y
          else:
            Y = century*100 + Y
        Y, M, D, h, m, s = int(Y), int(M), int(D), int(h), int(m), int(s)
        # handle plain times by making them today...
        if Y == M == D == 0:
          Y, M, D = now[:3]
        ampm = g.get("AMPM", "").lower()
        if ampm == '':
          pass
        elif ampm == 'pm':
          if 0 <= h < 12: h += 12
        elif ampm == 'am':
          pass
        else:
          raise ParseError("invalid AM/PM value: "+repr(ampm)+" in date "+repr(formatteddate)+" with format string: "+repr(self.format))
        return date(Y,M,D,h,m,s)

def dbdatestring(obj,dbtype):
    if dbtype == 'oracle':
        return "to_date('"+formatdate(obj, "%Y-%m-%d %H:%M:%S")+"','yyyy-mm-dd hh24:mi:ss')"
    elif dbtype == 'sqlserver':
        return "'"+formatdate(obj, "%Y-%m-%d %H:%M:%S")+"'"
    elif dbtype == 'access':
        return "#"+formatdate(obj, "%Y-%m-%d %H:%M:%S")+"#"
    elif dbtype == 'postgres':
        return "to_timestamp('"+formatdate(obj, "%Y-%m-%d %H:%M:%S")+"','yyyy-mm-dd hh24:mi:ss')"
    elif dbtype == 'mysql':
        return "'"+formatdate(obj, "%Y-%m-%d %H:%M:%S")+"'"
    elif dbtype == 'sqlite':
        return "'"+formatdate(obj, "%Y-%m-%d %H:%M:%S")+"'"
    else:
        raise ValueError, "unknown dbtype %r" % dbtype

# http://www.techonthenet.com/oracle/functions/to_char.htm
oracledateformatsubst = {
  "%a": "DY",     # Locale's abbreviated weekday name
  "%A": "DAY",    # Locale's full weekday name
  "%b": "MON",    # Locale's abbreviated month name
  "%B": "MONTH",  # Locale's full month name
  # "%c": "",       # Locale's appropriate date and time representation
  "%d": "DD",     # Day of the month as a decimal number [01,31]
  "%H": "HH24",   # Hour (24-hour clock) as a decimal number [00,23]
  "%I": "HH",     # Hour (12-hour clock) as a decimal number [01,12]
  "%j": "DDD",    # Day of the year as a decimal number [001,366]
  "%m": "MM",     # Month as a decimal number [01,12]
  "%M": "MI",     # Minute as a decimal number [00,59]
  # "%p": "AM/PM",   # Locale's equivalent of either AM or PM
  "%S": "SS",     # Second as a decimal number [00,61]
  # "%U": "IW",     # Week number of the year (Sunday as the first day of the week) as a decimal number [00,53]. All days in a new year preceding the first Sunday are considered to be in week 0
  # "%w": "D",      # Weekday as a decimal number [0(Sunday),6]
  # "%W": "IW",     # Week number of the year (Monday as the first day of the week) as a decimal number [00,53]. All days in a new year preceding the first Monday are considered to be in week 0
  # "%x": "",       # Locale's appropriate date representation
  # "%X": "",       # Locale's appropriate time representation
  "%y": "YY",       # Year without century as a decimal number [00,99]
  "%Y": "YYYY",     # Year with century as a decimal number
  # "%Z": "",         # Time zone name (no characters if no time zone exists)
  }

# MSDN Office 95 Format documentation
accessdateformatsubst = {
  "%a": "ddd",    # Locale's abbreviated weekday name
  "%A": "dddd",   # Locale's full weekday name
  "%b": "mmm",    # Locale's abbreviated month name
  "%B": "mmmm",   # Locale's full month name
  # "%c": "",       # Locale's appropriate date and time representation
  "%d": "dd",     # Day of the month as a decimal number [01,31]
  "%H": "hh",     # Hour (24-hour clock) as a decimal number [00,23]
  "%I": "hh",     # Hour (12-hour clock) as a decimal number [01,12]  # access will do this if AM/PM is included
  "%j": "y",    # Day of the year as a decimal number [001,366]
  "%m": "mm",     # Month as a decimal number [01,12]
  "%M": "nn",     # Minute as a decimal number [00,59]
  "%p": "AMPM",   # Locale's equivalent of either AM or PM
  "%S": "ss",     # Second as a decimal number [00,61]
  # "%U": "ww",     # Week number of the year (Sunday as the first day of the week) as a decimal number [00,53]. All days in a new year preceding the first Sunday are considered to be in week 0
  # "%w": "w",      # Weekday as a decimal number [0(Sunday),6]
  # "%W": "ww",     # Week number of the year (Monday as the first day of the week) as a decimal number [00,53]. All days in a new year preceding the first Monday are considered to be in week 0
  # "%x": "",       # Locale's appropriate date representation
  # "%X": "",       # Locale's appropriate time representation
  "%y": "yy",       # Year without century as a decimal number [00,99]
  "%Y": "yyyy",     # Year with century as a decimal number
  # "%Z": "",         # Time zone name (no characters if no time zone exists)
  }

# http://www.php-editors.com/postgres_manual/p_functions-formatting.html
postgresdateformatsubst = {
  "%a": "Dy",     # Locale's abbreviated weekday name
  "%A": "Day",    # Locale's full weekday name
  "%b": "Mon",    # Locale's abbreviated month name
  "%B": "Month",  # Locale's full month name
  # "%c": "",       # Locale's appropriate date and time representation
  "%d": "DD",     # Day of the month as a decimal number [01,31]
  "%H": "HH24",   # Hour (24-hour clock) as a decimal number [00,23]
  "%I": "HH",     # Hour (12-hour clock) as a decimal number [01,12]
  "%j": "DDD",    # Day of the year as a decimal number [001,366]
  "%m": "MM",     # Month as a decimal number [01,12]
  "%M": "MI",     # Minute as a decimal number [00,59]
  "%p": "AM",   # Locale's equivalent of either AM or PM
  "%S": "SS",     # Second as a decimal number [00,61]
  # "%U": "IW",     # Week number of the year (Sunday as the first day of the week) as a decimal number [00,53]. All days in a new year preceding the first Sunday are considered to be in week 0
  # "%w": "D",      # Weekday as a decimal number [0(Sunday),6]
  # "%W": "IW",     # Week number of the year (Monday as the first day of the week) as a decimal number [00,53]. All days in a new year preceding the first Monday are considered to be in week 0
  # "%x": "",       # Locale's appropriate date representation
  # "%X": "",       # Locale's appropriate time representation
  "%y": "YY",       # Year without century as a decimal number [00,99]
  "%Y": "YYYY",     # Year with century as a decimal number
  "%Z": "TZ",         # Time zone name (no characters if no time zone exists)
  }

# http://dev.mysql.com/doc/mysql/en/date-and-time-functions.html
# note that this is tricky as the mysql and python formats overlap
# as a result, the conceptual map at the top is replaced with a functional one below...
mysqldateformatsubst = {
  "%a": "%a",     # Locale's abbreviated weekday name
  "%A": "%W",     # Locale's full weekday name
  "%b": "%b",     # Locale's abbreviated month name
  "%B": "%M",     # Locale's full month name
  # "%c": "",     # Locale's appropriate date and time representation
  "%d": "%d",     # Day of the month as a decimal number [01,31]
  "%H": "%H",     # Hour (24-hour clock) as a decimal number [00,23]
  "%I": "%I",     # Hour (12-hour clock) as a decimal number [01,12]
  "%j": "%j",     # Day of the year as a decimal number [001,366]
  "%m": "%m",     # Month as a decimal number [01,12]
  "%M": "%i",     # Minute as a decimal number [00,59]
  "%p": "%p",     # Locale's equivalent of either AM or PM
  "%S": "%S",     # Second as a decimal number [00,61]
  "%U": "%U",     # Week number of the year (Sunday as the first day of the week) as a decimal number [00,53]. All days in a new year preceding the first Sunday are considered to be in week 0
  "%w": "%w",     # Weekday as a decimal number [0(Sunday),6]
  "%W": "%u",     # Week number of the year (Monday as the first day of the week) as a decimal number [00,53]. All days in a new year preceding the first Monday are considered to be in week 0
  # "%x": "",     # Locale's appropriate date representation
  # "%X": "",     # Locale's appropriate time representation
  "%y": "%y",     # Year without century as a decimal number [00,99]
  "%Y": "%Y",     # Year with century as a decimal number
  # "%Z": "",     # Time zone name (no characters if no time zone exists)
  }
# the complex interaction here is:
# Python "%M" -> mysql "%i"
# Python "%W" -> mysql "%u"
# Python "%A" -> mysql "%W"
# Python "%B" -> mysql "%M"
mysqldateformatsubst = cidict.ordereddict([
  ("%M", "%i"),   # Minute as a decimal number [00,59]
  ("%W", "%u"),   # Week number of the year (Monday as the first day of the week) as a decimal number [00,53]. All days in a new year preceding the first Monday are considered to be in week 0
  ("%A", "%W"),   # Locale's full weekday name
  ("%B", "%M"),   # Locale's full month name
  ])

# from http://msdn.microsoft.com/library/default.asp?url=/library/en-us/tsqlref/ts_da-db_2mic.asp
# this is the datepart reference
strx = lambda expr, len: "replace(str(%s, %d), ' ', '0')" % (expr, len)
convertx = lambda num: "convert(varchar, %%s, %d)" % num
lconvertx = lambda num, width: "left(convert(varchar, %%s, %d), %d)" % (num, width)
rconvertx = lambda num, width: "right(convert(varchar, %%s, %d), %d)" % (num, width)
convertxr = lambda num, str1, str2: "replace(convert(varchar, %%s, %d), '%s', '%s')" % (num, str1, str2)
sqldateformatsubst = [
  # combined items that can be done easier using convert
  # we don't have milliseconds so we leave out all of those
  ("%b %d %Y %I:%M%P", convertx(100)), 
  ("%Y-%m-%d %H:%M:%S", convertx(120)), 
  ("%m/%d/%y", convertx(1)), 
  ("%m/%d/%Y", convertx(101)), 
  ("%y.%m.%d", convertx(2)), 
  ("%Y.%m.%d", convertx(102)), 
  ("%d/%m/%y", convertx(3)), 
  ("%d/%m/%Y", convertx(103)), 
  ("%d.%m.%y", convertx(4)), 
  ("%d.%m.%Y", convertx(104)), 
  ("%d-%m-%y", convertx(5)), 
  ("%d-%m-%Y", convertx(105)), 
  ("%d %b %y", convertx(6)), 
  ("%d %b %Y", convertx(106)), 
  ("%b %d, %y", convertx(7)), 
  ("%b %d, %Y", convertx(107)),
  ("%H:%M:%S", convertx(8)),
  ("%m-%d-%y", convertx(10)), 
  ("%m-%d-%Y", convertx(110)), 
  ("%y/%m/%d", convertx(11)), 
  ("%Y/%m/%d", convertx(111)), 
  ("%y%m%d", convertx(12)), 
  ("%Y%m%d", convertx(112)),
  # use space instead of separator char
  ("%m %d %y", convertxr(1, "/", " ")), 
  ("%m %d %Y", convertxr(101, "/", " ")), 
  ("%d %m %y", convertxr(3, "/", " ")), 
  ("%d %m %Y", convertxr(103, "/", " ")), 
  ("%y %m %d", convertxr(11, "/", " ")), 
  ("%Y %m %d", convertxr(111, "/", " ")), 
  # substrings of combined items that are worthwhile shortcuts
  ("%m/%d", lconvertx(1, 5)), 
  ("%d/%y", rconvertx(1, 5)), 
  ("%d/%Y", rconvertx(101, 7)), 
  ("%d/%m", lconvertx(3, 5)), 
  ("%m/%y", rconvertx(3, 5)), 
  ("%m/%Y", rconvertx(103, 7)), 
  ("%y/%m", lconvertx(11, 5)), 
  ("%Y/%m", lconvertx(111, 7)), 
  ("%m-%d", lconvertx(10, 5)), 
  ("%d-%y", rconvertx(10, 5)), 
  ("%d-%Y", rconvertx(110, 7)), 
  ("%d-%m", lconvertx(5, 5)), 
  ("%m-%y", rconvertx(5, 5)), 
  ("%m-%Y", rconvertx(105, 7)), 
  ("%d.%m", lconvertx(4, 5)), 
  ("%m.%y", rconvertx(4, 5)), 
  ("%m.%Y", rconvertx(104, 7)), 
  ("%m.%d", lconvertx(2, 5)), 
  ("%y.%m", rconvertx(2, 5)), 
  ("%Y.%m", rconvertx(102, 7)), 
  ("%m%d", lconvertx(12, 4)), 
  ("%d%y", rconvertx(12, 4)), 
  ("%d%Y", rconvertx(112, 6)), 
  ("%H:%M", lconvertx(8, 5)),
  ("%M:%S", rconvertx(8, 5)),
  # standard items
  ("%a", "left(datename(weekday, %s), 3)"),    # Locale's abbreviated weekday name
  ("%A", "datename(weekday, %s)"),   # Locale's full weekday name
  ("%b", "left(datename(month, %s), 3)"),    # Locale's abbreviated month name
  ("%B", "datename(month, %s)"),   # Locale's full month name
  # ("%c", ""),                    # Locale's appropriate date and time representation
  ("%d", strx("day(%s)", 2)),      # Day of the month as a decimal number [01,31]
  ("%H", strx("datepart(hh, %s)", 2)),      # Hour (24-hour clock) as a decimal number [00,23]
  ("%I", strx("(datepart(hh, %s)+11) %% 12 + 1", 2)),     # Hour (12-hour clock) as a decimal number [01,12]
  ("%j", strx("datepart(dy, %s)", 3)),      # Day of the year as a decimal number [001,366]
  ("%m", strx("month(%s)", 2)),      # Month as a decimal number [01,12]
  ("%M", strx("datepart(mi, %s)", 2)),      # Minute as a decimal number [00,59]
  ("%p", "right(convert(varchar, %s, 100), 2)"),   # Locale's equivalent of either AM or PM
  ("%S", strx("datepart(ss, %s)", 2)),      # Second as a decimal number [00,61]
  # %U - Week number of the year (Sunday as the first day of the week) as a decimal number [00,53].
  # All days in a new year preceding the first Sunday are considered to be in week 0
  ("%U", strx("(datepart(dy, %s) + ((14 - datepart(weekday, %s) - @@datefirst) %% 7)) / 7", 2)),
  ("%w", strx("(datepart(dw, %s)+@@datefirst+6) %% 7", 1)),      # Weekday as a decimal number [0(Sunday),6]
  # %W - Week number of the year (Monday as the first day of the week) as a decimal number [00,53].
  # All days in a new year preceding the first Monday are considered to be in week 0
  ("%W", strx("(datepart(dy, %s) + ((14 - datepart(weekday, %s) - @@datefirst) %% 7)) / 7", 2)),
  # ("%x", ""),       # Locale's appropriate date representation
  # ("%X", ""),       # Locale's appropriate time representation
  ("%y", strx("year(%s) %% 100", 2)),      # Year without century as a decimal number [00,99]
  ("%Y", strx("year(%s)", 4)),    # Year with century as a decimal number
  # ("%Z", ""),         # Time zone name (no characters if no time zone exists)
  ]
del strx, convertx, lconvertx, rconvertx, convertxr
sqldateformatsubst = cidict.ordereddict(sqldateformatsubst)

def sqldateformatsubstfunction(expression, formatstr):
  """tries to create an expression that produces the appropriate date format"""
  result = ""
  outstate = ""
  formatpos = 0
  while formatpos < len(formatstr):
    if formatstr[formatpos] == "%": 
      dateformat = None
      for key in sqldateformatsubst:
        if formatstr[formatpos:formatpos+len(key)] == key:
          dateformat = sqldateformatsubst[key]
          formatpos += len(key)
          break
      if dateformat:
        if dateformat.count("%s") > 1:
          formatted = dateformat % ((expression,) * dateformat.count("%s"))
        else:
          formatted = dateformat % expression
        if outstate == "'":
          result += outstate
          outstate = ""
        if result:
          result += " + "
        result += formatted
        continue
    nextmark = formatstr.find("%", formatpos+1)
    if nextmark == -1:
      nextmark = len(formatstr)
    formatslice = formatstr[formatpos:nextmark]
    if outstate == "'":
      result += formatslice
    else:
      outstate = "'"
      if result: result += " + "
      result += outstate + formatslice
    formatpos = nextmark
  if outstate:
    result += outstate
  return result

class dbdaterepr:
  """class for holding a date and letting it be repr() as a string"""
  def __init__(self,obj,dbtype):
    self.obj = obj
    self.dbtype = dbtype
  def __repr__(self):
    return dbdatestring(self.obj,self.dbtype)
  def dbrepr(self):
    return dbdatestring(self.obj,self.dbtype)
  def strftime(self,*args):
    """allow passthrough to underlying object's strftime method"""
    if hasattr(self.obj, "strftime"):
      return self.obj.strftime(*args)
    else:
      return formatdate(self.obj, *args)

# generally used date formats
dateformats = cidict.cidict({'GENERAL DATE':'%d/%m/%y %H:%M:%S',
               'LONG DATE':   '%d/%m/%y %H:%M:%S',
               'MEDIUM DATE': '%d/%m/%y %H:%M:%S',
               'SHORT DATE':  '%d/%m/%y',
               'SHORT TIME':  '%H:%M:%S'})
# dd/mm/yy or dd/mm/yyyy
stddateparseformat = "(?P<D>\d{1,2})/(?P<M>\d{1,2})/(?P<Y>\d{2,4})"
# hh:mi:ss [am|pm]
stdtimeparseformat = "(?P<h>\d{1,2})(:(?P<m>\d{2})(:(?P<s>\d{2})|)|)([ ]*(?P<AMPM>[aApP][mM])|)"
# dd/mm/yy[yy] hh:mi:ss [am|pm]
stddatetimeparseformat = stddateparseformat + "[ ]+" + stdtimeparseformat
# yyyymmddhhmiss
nosepdateparseformat = "(?P<Y>\d{4})(?P<M>\d{2})(?P<D>\d{2})(?P<h>\d{2})(?P<m>\d{2})(?P<s>\d{2})"
# yyyy-mm-dd hh:mi:ss+TZ
pgdateparseformat = "(?P<Y>\d{4})-(?P<M>\d{2})-(?P<D>\d{2}) (?P<h>\d{2}):(?P<m>\d{2}):(?P<s>\d{2})([+-]\d{2}|)"
# standard parsers
stddateparser = dateparser(stddateparseformat)
stdtimeparser = dateparser(stdtimeparseformat)
stddatetimeparser = dateparser(stddatetimeparseformat)
nosepdateparser = dateparser(nosepdateparseformat)
pgdateparser = dateparser(pgdateparseformat)
dateparsers = cidict.cidict({'GENERAL DATE': stddatetimeparser,
                'LONG DATE':   stddatetimeparser,
                'MEDIUM DATE': stddatetimeparser,
                'SHORT DATE':  stddateparser,
                'SHORT TIME':  stdtimeparser})

def strptime_partial(value, formattype):
  """this will try successive substrings of the formatstring, split at space boundaries, if it doesn't match
  returns both the value and the formattype used to successfully parse it"""
  try:
    return time.strptime(value, formattype), formattype
  except ValueError, error:
    formatparts = formattype.split(" ")
    if len(formatparts) > 1:
      for joinlen in range(1, len(formatparts)):
        for joinstart in range(0, len(formatparts)-joinlen+1):
          subformattype = " ".join(formatparts[joinstart:joinstart+joinlen])
	  try:
            return time.strptime(value, subformattype), subformattype
          except ValueError:
            continue
    raise ParseError(str(error) + " (tried different parts of format string too)")

def parsedate(value, formattype, returnformat=False):
  """parses a date/time string of the given type, returns a datetime object (and the matching format if required)"""
  if not isinstance(value, basestring):
    raise TypeError, "unexpected type in parsedate: %r, %r" % (value, type(value))
  timevalue, formatmatch = strptime_partial(value, formattype)
  timevalue = apply(date, timevalue[:6])
  if returnformat:
    return timevalue, formatmatch
  else:
    return timevalue

def getgranularity(formattype):
  """returns the granularity range available from the given formattype"""
  # TODO: include all the formatting codes, weeks, etc
  year, month, day, hour, minute, second = range(6)
  finestgranularity = year
  widestgranularity = second
  for formatstr in re.findall("%[a-zA-Z]", formattype):
    formatcode = formatstr[1]
    if formatcode in "jyY":
      codegranularity = year
    elif formatcode in "bBm":
      codegranularity = month
    elif formatcode in "aAdj":
      codegranularity = day
    elif formatcode in "HIp":
      codegranularity = hour
    elif formatcode in "M":
      codegranularity = minute
    elif formatcode in "S":
      codegranularity = second
    if codegranularity > finestgranularity:
      finestgranularity = codegranularity
    if codegranularity < widestgranularity:
      widestgranularity = codegranularity
  return finestgranularity, widestgranularity

def replaceunavailableinformation(point, widestgranularity, defaultpoint):
  """replaces unavailable information in the point with values from defaultpoint"""
  year, month, day, hour, minute, second = range(6)
  if widestgranularity > year:
    point = point.replace(year=defaultpoint.year)
  if widestgranularity > month:
    point = point.replace(month=defaultpoint.month)
  if widestgranularity > day:
    point = point.replace(day=defaultpoint.day)
  if widestgranularity > hour:
    point = point.replace(hour=defaultpoint.hour)
  if widestgranularity > minute:
    point = point.replace(minute=defaultpoint.minute)
  if widestgranularity > second:
    point = point.replace(second=defaultpoint.second)
  return point
  
def getperiodend(point, granularity):
  """returns a datetime at the end of the period containing point, of length granularity"""
  year, month, day, hour, minute, second = range(6)
  # TODO: clear up year and month
  if granularity <= year:
    point = point.replace(month=12)
  if granularity <= month:
    monthstart, monthend = calendar.monthrange(point.year, point.month)
    point = point.replace(day=monthend)
  if granularity <= day:
    point = point.replace(hour=23)
  if granularity <= hour:
    point = point.replace(minute=59)
  if granularity <= minute:
    point = point.replace(second=59)
  return point

def formatdate(value, dateformat):
  """formats a date/time object of the given type, returns a string"""
  # pywintypes.TimeType can't handle dates before 1970
  if type(value) == errortimetype:
    value = date(value.year, value.month, value.day, value.hour, value.minute, value.second)
  if hasattr(value,'strftime'):
    if isinstance(dateformat, unicode):
      dateformat = dateformat.encode('utf8')
    return value.strftime(dateformat)
  # handle null values
  elif value is None or value == '':
    return ''
  elif type(value) in (tuple, time.struct_time):
    return time.strftime(dateformat, value)
  elif isinstance(value, (str, unicode)):
    # this can happen if a date type is used for a filter
    return value
  else:
    raise TypeError, "unexpected type in formatdate: %r, %r" % (value, type(value))

def datepart(value):
  """returns the date part of a datetime value"""
  return value.date()

def timepart(value):
  """returns the time part of a datetime value"""
  return value.time()

def WinPyTimeToDate(pytime):
  """Converts a pywintypes.PyTime object into a date object"""
  return date(pytime.year, pytime.month, pytime.day, pytime.hour, pytime.minute, pytime.second)

def converttimezone(datevalue, hourstoshift):
  """shifts a given date value by a number of hourstoshift (positive or negative)"""
  if hourstoshift:
    if datevalue is None:
      return datevalue
    if type(datevalue).__name__ == 'time':
      if hasattr(datevalue, "year"):
        datevalue = WinPyTimeToDate(datevalue)
      else:
        numseconds = time.mktime(datevalue)
        datevalue = dates.date.fromtimestamp(numseconds)
    return datevalue + datetimedelta(hours=hourstoshift)
  else:
    return datevalue

