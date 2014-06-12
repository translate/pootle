#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2010,2012 Zuza Software Foundation
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

from django.contrib.syndication.views import Feed
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from pootle_app.models import Directory
from pootle_app.models.permissions import (check_permission,
                                           get_matching_permissions)
from pootle_notifications.models import Notice
from pootle_notifications.views import directory_to_title


class NoticeFeed(Feed):
    title_template = "notifications/notice_title.html"
    description_template = "notifications/notice_body.html"

    def get_object(self, request, path):
        pootle_path = '/%s' % path
        directory = get_object_or_404(Directory, pootle_path=pootle_path)

        request.permissions = get_matching_permissions(request.user, directory)
        if not check_permission('view', request):
            raise PermissionDenied

        self.directory = directory
        self.link = directory.get_absolute_url()
        self.recusrive = request.GET.get('all', False)

        return self.directory

    def title(self, directory):
        return directory_to_title(directory)

    def items(self, directory):
        if self.recusrive:
            return Notice.objects.filter(
                    directory__pootle_path__startswith=directory.pootle_path
                ).select_related('directory')[:30]
        else:
            return Notice.objects.filter(directory=directory) \
                                 .select_related('directory')[:30]

    def item_pubdate(self, item):
        return item.added
