#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL2
# license. See the LICENSE file for a copy of the license and the AUTHORS file
# for copyright and authorship information.

from django import template
from django.contrib.auth import get_user_model

from pootle_app.models.directory import Directory
from pootle_app.models.permissions import check_user_permission
from pootle_notifications.models import Notice

register = template.Library()


@register.inclusion_tag('notifications/_latest.html', takes_context=True)
def render_latest_news(context, path, num):
    try:
        directory = Directory.objects.get(pootle_path='/%s' % path)
        user = context['user']
        User = get_user_model()
        can_view = check_user_permission(User.get(user), "view", directory)
        if not can_view:
            directory = None
    except Directory.DoesNotExist:
        directory = None

    if directory is None:
        return {'news_items': None}
    news_items = Notice.objects.filter(directory=directory)[:num]
    return {'news_items': news_items}
