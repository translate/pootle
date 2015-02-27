#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL2
# license. See the LICENSE file for a copy of the license and the AUTHORS file
# for copyright and authorship information.

import json

from functools import wraps
from importlib import import_module

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponseBadRequest
from django.utils import timezone
from django.utils.encoding import force_unicode
from django.utils.functional import Promise

# Timezone aware minimum for datetime (if appropriate) (bug 2567)
from datetime import datetime, timedelta
datetime_min = datetime.min
if settings.USE_TZ:
    datetime_min = timezone.make_aware(datetime_min, timezone.utc)

from pootle.core.markup import Markup
from pootle.core.utils.timezone import make_aware


def import_func(path):
    i = path.rfind('.')
    module, attr = path[:i], path[i+1:]
    try:
        mod = import_module(module)
    except ImportError, e:
        raise ImproperlyConfigured('Error importing module %s: "%s"'
                                   % (module, e))
    try:
        func = getattr(mod, attr)
    except AttributeError:
        raise ImproperlyConfigured(
            'Module "%s" does not define a "%s" callable function'
            % (module, attr))

    return func


def dictsum(x, y):
    return dict((n, x.get(n, 0)+y.get(n, 0)) for n in set(x) | set(y))


class PootleJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for Pootle.

    This is mostly implemented to avoid calling `force_unicode` all the time on
    certain types of objects.
    https://docs.djangoproject.com/en/1.4/topics/serialization/#id2
    """
    def default(self, obj):
        if (isinstance(obj, Promise) or isinstance(obj, Markup) or
            isinstance(obj, datetime)):
            return force_unicode(obj)

        return super(PootleJSONEncoder, self).default(obj)


def jsonify(obj):
    """Serialize Python `obj` object into a JSON string."""
    if settings.DEBUG:
        indent = 4
    else:
        indent = None

    return json.dumps(obj, indent=indent, cls=PootleJSONEncoder)


def ajax_required(f):
    """Check that the request is an AJAX request.

    Use it in your views:

    @ajax_required
    def my_view(request):
        ....

    Taken from:
    http://djangosnippets.org/snippets/771/
    """
    @wraps(f)
    def wrapper(request, *args, **kwargs):
        if not settings.DEBUG and not request.is_ajax():
            return HttpResponseBadRequest("This must be an AJAX request.")
        return f(request, *args, **kwargs)

    return wrapper


def to_int(value):
    """Converts `value` to `int` and returns `None` if the conversion is
    not possible.
    """
    try:
        return int(value)
    except ValueError:
        return None


def get_max_month_datetime(dt):
    next_month = dt.replace(day=1) + timedelta(days=31)
    if settings.USE_TZ:
        tz = timezone.get_default_timezone()
        next_month = timezone.localtime(next_month, tz)

    return next_month.replace(day=1, hour=0, minute=0, second=0) - \
        timedelta(microseconds=1)


def get_date_interval(month):
    now = start = end = timezone.now()
    if month is None:
        month = start.strftime('%Y-%m')

    start = make_aware(datetime.strptime(month, '%Y-%m'))

    if start < now:
        if start.month != now.month or start.year != now.year:
            end = get_max_month_datetime(start)
    else:
        end = start

    start = start.replace(hour=0, minute=0, second=0)
    end = end.replace(hour=23, minute=59, second=59, microsecond=999999)

    return [start, end]
