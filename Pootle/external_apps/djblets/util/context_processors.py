#
# djblets/util/context_processors.py
#
# Copyright (c) 2007-2009  Christian Hammond
# Copyright (c) 2007-2009  David Trowbridge
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

import os
from datetime import datetime

from django.conf import settings

def settingsVars(request):
    return {'settings': settings}


def siteRoot(request):
    """
    Exposes a SITE_ROOT variable in templates. This assumes that the
    project has been configured with a SITE_ROOT settings variable and
    proper support for basing the installation in a subdirectory.
    """
    return {'SITE_ROOT': settings.SITE_ROOT}


def mediaSerial(request):
    """
    Exposes a media serial number that can be appended to a media filename
    in order to make a URL that can be cached forever without fear of change.
    The next time the file is updated and the server is restarted, a new
    path will be accessed and cached.

    This returns the value of settings.MEDIA_SERIAL, which must either be
    set manually or ideally should be set to the value of
    djblets.util.misc.generate_media_serial().
    """
    return {'MEDIA_SERIAL': getattr(settings, "MEDIA_SERIAL", "")}


def ajaxSerial(request):
    """
    Exposes a serial number that can be appended to filenames involving
    dynamic loads of URLs in order to make a URL that can be cached forever
    without fear of change.

    This returns the value of settings.AJAX_SERIAL, which must either be
    set manually or ideally should be set to the value of
    djblets.util.misc.generate_ajax_serial().
    """
    return {'AJAX_SERIAL': getattr(settings, "AJAX_SERIAL", "")}
