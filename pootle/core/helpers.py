#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Evernote Corporation
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
from django.utils.translation import ugettext as _

from pootle_app.models.permissions import check_permission
from pootle_misc.checks import check_names
from pootle_misc.forms import make_search_form


def get_filter_name(GET):
    """Get current filter's human-readable name.

    :param GET: A copy of ``request.GET``.
    :return: Two-tuple with the filter name, and a list of extra arguments
        passed to the current filter.
    """
    filter = extra = None

    if 'filter' in GET:
        filter = GET['filter']

        if filter.startswith('user-'):
            extra = [GET.get('user', _('User missing'))]
        elif filter == 'checks' and 'checks' in GET:
            extra = map(lambda check: check_names.get(check, check),
                        GET['checks'].split(','))
    elif 'search' in GET:
        filter = 'search'

        extra = [GET['search']]
        if 'sfields' in GET:
            extra.extend(GET['sfields'].split(','))

    filter_name = {
        'all': _('All'),
        'translated': _('Translated'),
        'untranslated': _('Untranslated'),
        'fuzzy': _('Needs work'),
        'incomplete': _('Incomplete'),
        # Translators: This is the name of a filter
        'search': _('Search'),
        'checks': _('Checks'),
        'user-submissions': _('Submissions'),
        'user-submissions-overwritten': _('Overwritten submissions'),
    }.get(filter)

    return (filter_name, extra)


def get_translation_context(request, is_terminology=False):
    """Return a common context for translation views.

    :param request: a :cls:`django.http.HttpRequest` object.
    :param is_terminology: boolean indicating if the translation context
        is relevant to a terminology project.
    """
    return {
        'cantranslate': check_permission("translate", request),
        'cansuggest': check_permission("suggest", request),
        'canreview': check_permission("review", request),
        'profile': request.profile,

        'pootle_path': request.pootle_path,
        'ctx_path': request.ctx_path,
        'resource_path': request.resource_path,

        'search_form': make_search_form(request=request,
                                        terminology=is_terminology),

        'MT_BACKENDS': settings.MT_BACKENDS,
        'LOOKUP_BACKENDS': settings.LOOKUP_BACKENDS,
        'AMAGAMA_URL': settings.AMAGAMA_URL,
    }
