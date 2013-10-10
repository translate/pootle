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

from django import template
from django.utils.safestring import mark_safe

from ..models import Goal


register = template.Library()


@register.filter
def goal_trail(path_obj, goal=None):
    """Outputs an HTML-formatted directory/store trail on goal drilldown.

    :param path_obj: A :cls:`pootle_app.models.Directory` or
                     :cls:`pootle_store.models.Store` object.
                     In case `path_obj` is a store, it will be built based on
                     its parent directory.
    :param goal_slug: A :cls:`pootle_tagging.models.Goal` object.
    """
    trail_list = []
    sep = u' / '

    if goal is None:
        return mark_safe(sep.join(trail_list))

    is_store = not path_obj.is_dir
    directory = is_store and path_obj.parent or path_obj
    dir_trail = directory.trail()

    for i, trail_dir in enumerate(dir_trail):
        if is_store or i != (len(dir_trail) - 1):
            tr = u'<span><a href="%(url)s">%(dir_name)s</a></span>' % {
                'url': goal.get_drill_down_url_for_path(trail_dir.pootle_path),
                'dir_name': trail_dir.name,
            }
        else:
            tr = u'<span>%(dir_name)s</span>' % {
                'dir_name': trail_dir.name,
            }
        trail_list.append(tr)

    if is_store:
        tr = u'<span>%(file_name)s</span>' % {
            'file_name': path_obj.name,
        }
        trail_list.append(tr)

    return mark_safe(sep.join(trail_list))
