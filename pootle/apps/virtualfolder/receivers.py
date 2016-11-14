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
from pootle_app.models import Directory
from pootle_store.models import Store

from .delegate import vfolder_finder
from .models import VirtualFolder


@receiver(post_save, sender=Store)
def handle_store_save(sender, instance, created, **kwargs):
    if not created:
        return
    vfolder_finder.get(
        instance.__class__)(instance).add_to_vfolders()


@receiver(post_save, sender=VirtualFolder)
def handle_vfolder_save(sender, instance, created, **kwargs):
    instance.path_matcher.update_stores()


@receiver(pre_delete, sender=VirtualFolder)
def handle_vfolder_delete(sender, instance, **kwargs):
    dirs = set(instance.stores.values_list("parent", flat=True))
    for store in instance.stores.all():
        instance.stores.remove(store)
        if store.priority == instance.priority:
            store.set_priority()
    updater = revision_updater.get(Directory)(
        object_list=Directory.objects.filter(pk__in=dirs))
    updater.update(keys=["stats"])
