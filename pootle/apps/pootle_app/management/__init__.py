# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import pre_delete, post_delete
from django.dispatch import receiver


permission_queryset = None


@receiver(pre_delete, sender=ContentType)
def fix_permission_content_type_pre(**kwargs):
    instance = kwargs["instance"]
    if instance.name == 'pootle' and instance.model == "":
        logging.debug("Fixing permissions content types")
        global permission_queryset
        permission_queryset = [permission for permission in
                               Permission.objects.filter(
                                   content_type=instance)]


@receiver(post_delete, sender=ContentType)
def fix_permission_content_type_post(**kwargs_):
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
