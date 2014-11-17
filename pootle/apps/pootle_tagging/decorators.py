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

from functools import wraps

from django.core.urlresolvers import resolve, reverse
from django.http import Http404
from django.shortcuts import redirect


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
                url_match = resolve(request.path)

                if (not url_match.url_name == 'pootle-xhr-edit-goal' and
                    not goal.get_stores_for_path(request.pootle_path)):
                    # If this is not an AJAX request to edit the goal, and the
                    # resource object doesn't belong to the goal, then redirect
                    # to the translation project root for the goal.
                    language = request.ctx_obj.language.code
                    project = request.ctx_obj.project.code
                    url = reverse('pootle-tp-goal-drill-down',
                                  args=[language, project, goal.slug, '', ''])
                    return redirect(url)

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
