# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Unit


@receiver(post_save, sender=Unit)
def unit_postsave_handler(**kwargs):
    """Update the revision of the store when unit changes
    """
    instance = kwargs["instance"]
    if instance.revision > instance.store.revision:
        instance.store.revision = instance.revision
        instance.store.save()
