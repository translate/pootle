#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009, 2013 Zuza Software Foundation
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

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db.models import Count
from django.utils.encoding import iri_to_uri

from pootle_misc.aggregate import group_by_sort


User = get_user_model()


def group_by_sort(queryset, column, fields):
    queryset = queryset.annotate(count=Count(column)).order_by('-count')
    queryset = queryset.values('count', *fields)
    return queryset


def gentopstats_root():
    """
    Generate the top contributor stats to be displayed for an entire
    Pootle installation.
    """
    key = "/:gentopstats"
    result = cache.get(key)
    if result is None:
        top_sugg   = group_by_sort(User.objects.exclude(suggestions=None),
                                   "suggestions", ["username"])[:settings.TOPSTAT_SIZE]
        top_review = group_by_sort(User.objects.exclude(reviewer=None),
                                   "reviewer", ["username"])[:settings.TOPSTAT_SIZE]
        top_sub    = group_by_sort(User.objects.exclude(submission=None),
                                   "submission", ["username"])[:settings.TOPSTAT_SIZE]
        result = map(None, top_sugg, top_review, top_sub)
        cache.set(key, result, settings.POOTLE_TOP_STATS_CACHE_TIMEOUT)
    return result


def gentopstats_language(language):
    """Generate the top contributor stats to be displayed
    for an entire Pootle installation, a language or a project.
    The output of this function looks something like this:
      {'data':        [],
       'headerlabel': u'Suggestions'},
      {'data':        [],
       'headerlabel': u'Reviews'},
      {'data':        [],
       'headerlabel': u'Submissions'}]
    """
    key = iri_to_uri("%s:gentopstats" % language.pootle_path)
    result = cache.get(key)
    if result is None:
        top_sugg   = group_by_sort(User.objects.filter(suggestions__translation_project__language=language),
                                   'suggestions', ['username'])[:settings.TOPSTAT_SIZE]
        top_review = group_by_sort(User.objects.filter(reviewer__translation_project__language=language),
                                   'reviewer', ['username'])[:settings.TOPSTAT_SIZE]
        top_sub    = group_by_sort(User.objects.filter(submission__translation_project__language=language),
                                   'submission', ['username'])[:settings.TOPSTAT_SIZE]

        result = map(None, top_sugg, top_review, top_sub)
        cache.set(key, result, settings.POOTLE_TOP_STATS_CACHE_TIMEOUT)
    return result


def gentopstats_project(project):
    """Generate the top contributor stats to be displayed
    for an entire Pootle installation, a language or a project.
    The output of this function looks something like this:
      {'data':        [],
       'headerlabel': u'Suggestions'},
      {'data':        [],
       'headerlabel': u'Reviews'},
      {'data':        [],
       'headerlabel': u'Submissions'}]
    """
    key = iri_to_uri("%s:gentopstats" % project.pootle_path)
    result = cache.get(key)
    if result is None:
        top_sugg   = group_by_sort(User.objects.filter(suggestions__translation_project__project=project),
                                   "suggestions", ["username"])[:settings.TOPSTAT_SIZE]
        top_review = group_by_sort(User.objects.filter(reviewer__translation_project__project=project),
                                   "reviewer", ["username"])[:settings.TOPSTAT_SIZE]
        top_sub    = group_by_sort(User.objects.filter(submission__translation_project__project=project),
                                   "submission", ["username"])[:settings.TOPSTAT_SIZE]

        result = map(None, top_sugg, top_review, top_sub)
        cache.set(key, result, settings.POOTLE_TOP_STATS_CACHE_TIMEOUT)
    return result


def gentopstats_translation_project(translation_project):
    """Generate the top contributor stats to be displayed
    for an entire Pootle installation, a language or a project.
    The output of this function looks something like this:
      {'data':        [],
       'headerlabel': u'Suggestions'},
      {'data':        [],
       'headerlabel': u'Reviews'},
      {'data':        [],
       'headerlabel': u'Submissions'}]
    """
    key = iri_to_uri("%s:gentopstats" % translation_project.pootle_path)
    result = cache.get(key)
    if result is None:
        top_sugg   = group_by_sort(User.objects.filter(suggestions__translation_project=translation_project),
                                   "suggestions", ["username"])[:settings.TOPSTAT_SIZE]
        top_review = group_by_sort(User.objects.filter(reviewer__translation_project=translation_project),
                                   "reviewer", ["username"])[:settings.TOPSTAT_SIZE]
        top_sub    = group_by_sort(User.objects.filter(submission__translation_project=translation_project),
                                   "submission", ["username"])[:settings.TOPSTAT_SIZE]

        result = map(None, top_sugg, top_review, top_sub)
        cache.set(key, result, settings.CACHE_MIDDLEWARE_SECONDS)
    return result
