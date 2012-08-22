#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2012 Zuza Software Foundation
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

from django import template

from pootle_misc.baseurl import l
from pootle_misc.forms import make_search_form


register = template.Library()


@register.inclusion_tag('search.html', takes_context=True)
def render_search(context, form=None, action=None):
    translation_project = context['translation_project']

    if form is None:
        is_terminology = translation_project.project.is_terminology
        form = make_search_form(terminology=is_terminology)

    if action is None:
        action = l('translate.html')

    template_vars = {
        'search_form': form,
        'search_action': action,
    }

    return template_vars
