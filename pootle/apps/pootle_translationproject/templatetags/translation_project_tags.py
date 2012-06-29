#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2010-2012 Zuza Software Foundation
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
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from pootle_translationproject.forms import make_search_form
from pootle_misc.baseurl import l

register = template.Library()

@register.inclusion_tag('translation_project/search.html', takes_context=True)
def render_search(context, form=None, action=None):
    translation_project = context['translation_project']
    if form is None:
        is_terminology =  translation_project.project.is_terminology
        form = make_search_form(terminology=is_terminology)
    if action is None:
        action = l('translate.html')

    template_vars = {
        'search_form': form,
        'search_action': action,
        'advanced_search_title': _('Advanced search'),
        }
    return template_vars


@register.filter
def trail(directory, separator='/'):
    """Outputs an HTML-formatted directory trail.

    :param directory: A :cls:`pootle_app.models.Directory` object.
                      The trail will be built based on this directory.
    :param separator: A string that will be used to join the trail.
    """
    trail_list = []
    dir_trail = directory.trail()
    sep = u' %s ' % separator

    for i, trail_dir in enumerate(dir_trail):
        if i != (len(dir_trail) - 1):
            tr = u'<span><a href="%(url)s">%(dir_name)s</a></span>' % {
                'url': trail_dir.get_absolute_url(),
                'dir_name': trail_dir.name,
            }
        else:
            tr = u'<span class="dir-trail-last">%(dir_name)s</span>' % {
                'dir_name': trail_dir.name,
            }
        trail_list.append(tr)

    return mark_safe(sep.join(trail_list))
