# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django import template

from pootle.core.views.decorators import check_directory_permission
from pootle_app.models import Directory


register = template.Library()


@register.filter('can_create_project')
def can_create_project(request):
    return check_directory_permission(
        "create_project",
        request,
        Directory.objects.root
    )
