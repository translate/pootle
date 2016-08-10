# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django import template

from pootle.i18n.gettext import ugettext as _
from pootle_misc.forms import make_search_form


register = template.Library()


@register.inclusion_tag('core/search.html', takes_context=True)
def render_search(context):
    search_form = make_search_form(request=context['request'])
    is_disabled = (context["page"] != "translate" and
                   not context["can_translate_stats"])
    if is_disabled:
        search_form.fields["search"].widget.attrs.update({
            'readonly': 'readonly',
            'disabled': True,
            'title': '',
            'placeholder': _("Search unavailable"),
        })

    return {
        'search_form': search_form,
        'search_action': context["object"].get_translate_url(),
        'is_disabled': is_disabled,
    }
