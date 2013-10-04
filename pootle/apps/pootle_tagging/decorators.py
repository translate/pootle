#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Zuza Software Foundation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# Pootle is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# Pootle; if not, see <http://www.gnu.org/licenses/>.

import logging
from functools import wraps

from django.conf import settings
from django.core.cache import cache
from django.http import Http404
from django.utils.encoding import iri_to_uri


def get_goal(func):
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        # Putting the next import at the top of the file causes circular import
        # issues.
        from .models import Goal

        goal_slug = kwargs.pop('goal_slug', '')

        if goal_slug:
            try:
                goal = Goal.objects.get(slug=goal_slug)
            except Goal.DoesNotExist:
                pass
            else:
                kwargs['goal'] = goal

        return func(request, *args, **kwargs)

    return wrapper


def require_goal(func):
    @wraps(func)
    def wrapper(request, *args, **kwargs):

        goal = kwargs.pop('goal', '')

        if goal:
            return func(request, goal, *args, **kwargs)
        else:
            raise Http404

    return wrapper


def get_from_cache_for_path(func, timeout=settings.OBJECT_CACHE_TIMEOUT):
    @wraps(func)
    def wrapper(instance, pootle_path, *args, **kwargs):
        key = iri_to_uri(":".join([instance.pootle_path, pootle_path,
                                   func.__name__]))
        result = cache.get(key)
        if result is None:
            logging.debug(u"cache miss for %s", key)
            result = func(instance, pootle_path, *args, **kwargs)
            cache.set(key, result, timeout)
        return result
    return wrapper
