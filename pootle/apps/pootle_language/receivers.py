# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from pootle.core.delegate import revision_updater

from .models import Language


@receiver(post_save, sender=Language)
def lang_created_handler(**kwargs):
    if not kwargs.get("created"):
        return
    instance = kwargs["instance"]
    revision_context = instance.directory.parent
    updater = revision_updater.get(revision_context.__class__)
    updater(revision_context).update(["languages"])


@receiver(pre_delete, sender=Language)
def lang_delete_handler(**kwargs):
    instance = kwargs["instance"]
    revision_context = instance.directory.parent
    updater = revision_updater.get(revision_context.__class__)
    updater(revision_context).update(["languages"])
