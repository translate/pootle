#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2013 Zuza Software Foundation
# Copyright 2013 Evernote Corporation
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

import logging

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import pre_delete, post_delete


################################ Signal handlers ##############################

permission_queryset = None


def fix_permission_content_type_pre(sender, instance, **kwargs):
    if instance.name == 'pootle' and instance.model == "":
        logging.debug("Fixing permissions content types")
        global permission_queryset
        permission_queryset = [permission for permission in \
                               Permission.objects.filter(content_type=instance)]
pre_delete.connect(fix_permission_content_type_pre, sender=ContentType)


def fix_permission_content_type_post(sender, instance, **kwargs):
    global permission_queryset
    if permission_queryset is not None:
        dir_content_type = ContentType.objects.get(app_label='pootle_app',
                                                   model='directory')
        dir_content_type.name = 'pootle'
        dir_content_type.save()
        for permission in permission_queryset:
            permission.content_type = dir_content_type
            permission.save()
        permission_queryset = None
post_delete.connect(fix_permission_content_type_post, sender=ContentType)
