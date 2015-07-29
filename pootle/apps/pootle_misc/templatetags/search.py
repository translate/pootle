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
def render_search(context):
    request = context['request']

    return {
        'search_form': make_search_form(request=request),
        'search_action': request.resource_obj.get_translate_url(),
    }
