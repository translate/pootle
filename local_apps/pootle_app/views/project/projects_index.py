#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2009 Zuza Software Foundation
#
# This file is part of Pootle.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

from django.utils.translation import ugettext as _
from django.shortcuts import render_to_response
from django.template import RequestContext

from pootle_app.views import pagelayout
from pootle_profile.models import get_profile
from pootle_app.views.index.index import getprojects
from pootle_app.models.permissions import get_matching_permissions
from pootle_app.views.top_stats import gentopstats
from pootle_app.models import Directory

def view(request):
    request.permissions = get_matching_permissions(get_profile(request.user), Directory.objects.root)
    topstats = gentopstats(lambda query: query)

    templatevars = {
        'projectlink': _('Projects'),
        'projects': getprojects(request),
        'topstats': topstats,
        'instancetitle': pagelayout.get_title(),
        'translationlegend': {'translated': _('Translations are complete'),
                    'fuzzy': _('Translations need to be checked (they are marked fuzzy)'
                    ), 'untranslated': _('Untranslated')},
        }
    return render_to_response('project/projects.html', templatevars, RequestContext(request))

