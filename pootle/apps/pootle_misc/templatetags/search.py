#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django import template

from pootle_misc.forms import make_search_form


register = template.Library()


@register.inclusion_tag('core/search.html', takes_context=True)
def render_search(context, form=None, action=None):
    request = context['request']

    if form is None:
        is_terminology = False
        tp = context.get('translation_project', None)

        if tp is not None:
            is_terminology = tp.project.is_terminology

        form = make_search_form(request=request, terminology=is_terminology)

    if action is None:
        action = request.resource_obj.get_translate_url()

    template_vars = {
        'search_form': form,
        'search_action': action,
    }

    return template_vars
