# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django import template


register = template.Library()


@register.inclusion_tag('translation_projects/terminology/_term_edit.html',
                        takes_context=True)
def render_term_edit(context, form):
    template_vars = {
        'unit': form.instance,
        'form': form,
        'language': context['language'],
        'source_language': context['source_language'],
    }
    return template_vars
