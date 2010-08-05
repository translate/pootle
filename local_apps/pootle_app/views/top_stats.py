#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Zuza Software Foundation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Pootle is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Pootle; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from django.utils.translation import ugettext as _
from django.contrib.auth.models import User
from django.conf import settings

from pootle_misc.aggregate import group_by_sort

def gentopstats_root():
    """
    Generate the top contributor stats to be displayed for an entire
    Pootle installation.
    """
    top_sugg   = group_by_sort(User.objects.exclude(pootleprofile__suggester=None),
                               'pootleprofile__suggester', ['username'])[:settings.TOPSTAT_SIZE]
    top_review = group_by_sort(User.objects.exclude(pootleprofile__reviewer=None),
                               'pootleprofile__reviewer', ['username'])[:settings.TOPSTAT_SIZE]
    top_sub    = group_by_sort(User.objects.exclude(pootleprofile__submission=None),
                               'pootleprofile__submission', ['username'])[:settings.TOPSTAT_SIZE]

    return [
        {'data': top_sugg, 'headerlabel': _('Suggestions')},
        {'data': top_review, 'headerlabel': _('Reviews')},
        {'data': top_sub, 'headerlabel': _('Submissions')} ]

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
    top_sugg   = group_by_sort(User.objects.filter(pootleprofile__suggester__translation_project__language=language),
                               'pootleprofile__suggester', ['username'])[:settings.TOPSTAT_SIZE]
    top_review = group_by_sort(User.objects.filter(pootleprofile__reviewer__translation_project__language=language),
                               'pootleprofile__reviewer', ['username'])[:settings.TOPSTAT_SIZE]
    top_sub    = group_by_sort(User.objects.filter(pootleprofile__submission__translation_project__language=language),
                               'pootleprofile__submission', ['username'])[:settings.TOPSTAT_SIZE]

    return [
        {'data': top_sugg, 'headerlabel': _('Suggestions')},
        {'data': top_review, 'headerlabel': _('Reviews')},
        {'data': top_sub, 'headerlabel': _('Submissions')} ]

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
    top_sugg   = group_by_sort(User.objects.filter(pootleprofile__suggester__translation_project__project=project),
                               'pootleprofile__suggester', ['username'])[:settings.TOPSTAT_SIZE]
    top_review = group_by_sort(User.objects.filter(pootleprofile__reviewer__translation_project__project=project),
                               'pootleprofile__reviewer', ['username'])[:settings.TOPSTAT_SIZE]
    top_sub    = group_by_sort(User.objects.filter(pootleprofile__submission__translation_project__project=project),
                               'pootleprofile__submission', ['username'])[:settings.TOPSTAT_SIZE]

    return [
        {'data': top_sugg, 'headerlabel': _('Suggestions')},
        {'data': top_review, 'headerlabel': _('Reviews')},
        {'data': top_sub, 'headerlabel': _('Submissions')} ]

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
    top_sugg   = group_by_sort(User.objects.filter(pootleprofile__suggester__translation_project=translation_project),
                               'pootleprofile__suggester', ['username'])[:settings.TOPSTAT_SIZE]
    top_review = group_by_sort(User.objects.filter(pootleprofile__reviewer__translation_project=translation_project),
                               'pootleprofile__reviewer', ['username'])[:settings.TOPSTAT_SIZE]
    top_sub    = group_by_sort(User.objects.filter(pootleprofile__submission__translation_project=translation_project),
                               'pootleprofile__submission', ['username'])[:settings.TOPSTAT_SIZE]

    return [
        {'data': top_sugg, 'headerlabel': _('Suggestions')},
        {'data': top_review, 'headerlabel': _('Reviews')},
        {'data': top_sub, 'headerlabel': _('Submissions')} ]

