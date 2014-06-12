#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Zuza Software Foundation
# Copyright 2013 Evernote Corporation
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

from pootle_app.models.directory import Directory
from pootle_app.models.permissions import check_user_permission
from pootle_notifications.models import Notice

register = template.Library()


@register.inclusion_tag('notifications/_latest.html', takes_context=True)
def render_latest_news(context, path, num):
    try:
        directory = Directory.objects.get(pootle_path='/%s' % path)
        user = context['user']
        can_view = check_user_permission(user, "view", directory)
        if not can_view:
            directory = None
    except Directory.DoesNotExist:
        directory = None

    if directory is None:
        return {'news_items': None}
    news_items = Notice.objects.filter(directory=directory)[:num]
    return {'news_items': news_items}
