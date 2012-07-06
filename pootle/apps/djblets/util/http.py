#
# http.py -- HTTP-related utilities.
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

from djblets.util.dates import http_date


def set_last_modified(response, timestamp):
    """
    Sets the Last-Modified header in a response based on a DateTimeField.
    """
    response['Last-Modified'] = http_date(timestamp)


def get_modified_since(request, last_modified):
    """
    Checks if a Last-Modified timestamp is newer than the requested
    HTTP_IF_MODIFIED_SINCE from the browser. This can be used to bail
    early if no updates have been performed since the last access to the
    page.

    This can take a DateField, datetime, HTTP date-formatted string, or
    a function for the last_modified timestamp. If a function is passed,
    it will only be called if the HTTP_IF_MODIFIED_SINCE header is present.
    """
    if_modified_since = request.META.get('HTTP_IF_MODIFIED_SINCE', None)

    if if_modified_since is not None:
        if callable(last_modified):
            last_modified = last_modified()

        return (if_modified_since == http_date(last_modified))

    return False


def set_etag(response, etag):
    """
    Sets the ETag header in a response.
    """
    response['ETag'] = etag


def etag_if_none_match(request, etag):
    """
    Checks if an ETag matches the If-None-Match header sent by the browser.
    This can be used to bail early if no updates have been performed since
    the last access to the page.
    """
    return etag == request.META.get('If-None-Match', None)


def etag_if_match(request, etag):
    """
    Checks if an ETag matches the If-Match header sent by the browser. This
    is used by PUT requests to to indicate that the update should only happen
    if the specified ETag matches the header.
    """
    return etag == request.META.get('If-Match', None)
