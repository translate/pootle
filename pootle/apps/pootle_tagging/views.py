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

from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.template import loader, RequestContext
from django.views.decorators.http import require_POST

from pootle.core.decorators import permission_required
from pootle_misc.util import ajax_required, jsonify

from .decorators import get_goal, require_goal
from .forms import GoalForm


@require_POST
@ajax_required
@get_goal
@require_goal
@permission_required('administrate')
def ajax_edit_goal(request, goal):
    """Edit a goal through a form using AJAX."""

    form = GoalForm(request.POST, instance=goal)
    response = {}
    rcode = 400

    if form.is_valid():
        form.save()
        rcode = 200

        if goal.description:
            response["description"] = goal.description
        else:
            response["description"] = (u'<p class="placeholder muted">%s</p>' %
                                       _(u"No description yet."))
    context = {
        'form': form,
        'form_action': reverse('pootle-tagging-ajax-edit-goal',
                               args=[goal.slug]),
    }
    t = loader.get_template('admin/general_settings_form.html')
    c = RequestContext(request, context)
    response['form'] = t.render(c)

    return HttpResponse(jsonify(response), status=rcode,
                        mimetype="application/json")
