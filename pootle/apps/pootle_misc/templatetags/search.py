#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django import template
from django.utils.translation import ugettext as _

from pootle_misc.forms import make_search_form


register = template.Library()


@register.inclusion_tag('core/search.html', takes_context=True)
def render_search(context):
    search_form = make_search_form(request=context['request'])
    if context["page"] != "translate" and not context["can_translate_stats"]:
        search_form.fields["search"].widget.attrs["readonly"] = "readonly"
        search_form.fields["search"].widget.attrs["disabled"] = True
        search_form.fields["search"].widget.attrs["title"] = ""
        search_form.fields["search"].widget.attrs[
            "placeholder"] = _("Search unavailable")
        search_form.fields[
            "search"].widget.attrs["class"] = "search-widget-disabled"

    return {
        'search_form': search_form,
        'search_action': context["object"].get_translate_url()}
