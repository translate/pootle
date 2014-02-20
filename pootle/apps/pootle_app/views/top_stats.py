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

from django.contrib.auth.models import User
from django.conf import settings
from django.core.cache import cache
from django.utils.encoding import iri_to_uri

from pootle_misc.aggregate import group_by_sort


def gentopstats_root():
    """
    Generate the top contributor stats to be displayed for an entire
    Pootle installation.
    """
    key = "/:gentopstats"
    result = cache.get(key)
    if result is None:
        top_sugg   = group_by_sort(User.objects.exclude(pootleprofile__suggester=None),
                                   'pootleprofile__suggester', ['username'])[:settings.TOPSTAT_SIZE]
        top_review = group_by_sort(User.objects.exclude(pootleprofile__reviewer=None),
                                   'pootleprofile__reviewer', ['username'])[:settings.TOPSTAT_SIZE]
        top_sub    = group_by_sort(User.objects.exclude(pootleprofile__submission=None),
                                   'pootleprofile__submission', ['username'])[:settings.TOPSTAT_SIZE]
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
        top_sugg   = group_by_sort(User.objects.filter(pootleprofile__suggester__translation_project__language=language),
                                   'pootleprofile__suggester', ['username'])[:settings.TOPSTAT_SIZE]
        top_review = group_by_sort(User.objects.filter(pootleprofile__reviewer__translation_project__language=language),
                                   'pootleprofile__reviewer', ['username'])[:settings.TOPSTAT_SIZE]
        top_sub    = group_by_sort(User.objects.filter(pootleprofile__submission__translation_project__language=language),
                                   'pootleprofile__submission', ['username'])[:settings.TOPSTAT_SIZE]

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
        top_sugg   = group_by_sort(User.objects.filter(pootleprofile__suggester__translation_project__project=project),
                                   'pootleprofile__suggester', ['username'])[:settings.TOPSTAT_SIZE]
        top_review = group_by_sort(User.objects.filter(pootleprofile__reviewer__translation_project__project=project),
                                   'pootleprofile__reviewer', ['username'])[:settings.TOPSTAT_SIZE]
        top_sub    = group_by_sort(User.objects.filter(pootleprofile__submission__translation_project__project=project),
                                   'pootleprofile__submission', ['username'])[:settings.TOPSTAT_SIZE]

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
        top_sugg   = group_by_sort(User.objects.filter(pootleprofile__suggester__translation_project=translation_project),
                                   'pootleprofile__suggester', ['username'])[:settings.TOPSTAT_SIZE]
        top_review = group_by_sort(User.objects.filter(pootleprofile__reviewer__translation_project=translation_project),
                                   'pootleprofile__reviewer', ['username'])[:settings.TOPSTAT_SIZE]
        top_sub    = group_by_sort(User.objects.filter(pootleprofile__submission__translation_project=translation_project),
                                   'pootleprofile__submission', ['username'])[:settings.TOPSTAT_SIZE]

        result = map(None, top_sugg, top_review, top_sub)
        cache.set(key, result, settings.CACHE_MIDDLEWARE_SECONDS)
    return result
