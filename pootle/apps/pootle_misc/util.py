# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from datetime import datetime, timedelta
from functools import wraps
from importlib import import_module

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponseBadRequest
from django.utils import timezone


def import_func(path):
    i = path.rfind('.')
    module, attr = path[:i], path[i+1:]
    try:
        mod = import_module(module)
    except ImportError as e:
        raise ImproperlyConfigured('Error importing module %s: "%s"'
                                   % (module, e))
    try:
        func = getattr(mod, attr)
    except AttributeError:
        raise ImproperlyConfigured(
            'Module "%s" does not define a "%s" callable function'
            % (module, attr))

    return func


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


def get_max_month_datetime(dt):
    next_month = dt.replace(day=1) + timedelta(days=31)
    if settings.USE_TZ:
        tz = timezone.get_default_timezone()
        next_month = timezone.localtime(next_month, tz)

    return next_month.replace(day=1, hour=0, minute=0, second=0) - \
        timedelta(microseconds=1)


def get_date_interval(month):
    from pootle.core.utils.timezone import make_aware

    now = start = end = timezone.now()
    default_month = start.strftime('%Y-%m')

    if month is None:
        month = default_month

    try:
        month_datetime = datetime.strptime(month, '%Y-%m')
    except ValueError:
        month_datetime = datetime.strptime(default_month, '%Y-%m')

    start = make_aware(month_datetime)

    if start < now:
        if start.month != now.month or start.year != now.year:
            end = get_max_month_datetime(start)
    else:
        end = start

    start = start.replace(hour=0, minute=0, second=0)
    end = end.replace(hour=23, minute=59, second=59, microsecond=999999)

    return [start, end]


def cmp_by_last_activity(x, y):
    val_x = 0
    val_y = 0
    if 'stats' in x and 'last_submission' in x['stats']:
        val_x = x['stats']['last_submission']['mtime']
    if 'stats' in y and 'last_submission' in y['stats']:
        val_y = y['stats']['last_submission']['mtime']
    return cmp(val_y, val_x)
