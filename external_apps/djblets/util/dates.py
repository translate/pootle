#
# dates.py -- Date-related utilities.
#
# Copyright (c) 2008  Christian Hammond
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

from datetime import datetime
import time

from django.db.models import DateField


def http_date(timestamp):
    """
    A wrapper around Django's http_date that accepts DateFields and
    datetime objects directly.
    """
    from django.utils.http import http_date

    if isinstance(timestamp, (DateField, datetime)):
        return http_date(time.mktime(timestamp.timetuple()))
    elif isinstance(timestamp, basestring):
        return timestamp
    else:
        return http_date(timestamp)


def get_latest_timestamp(timestamps):
    """
    Returns the latest timestamp in a list of timestamps.
    """
    latest = None

    for timestamp in timestamps:
        if latest is None or timestamp > latest:
            latest = timestamp

    return latest
