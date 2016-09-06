# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.db.models.signals import post_save
from django.dispatch import receiver

from pootle.core.signals import update_data
from pootle_data.models import StoreData
from pootle_store.models import Store

from .models import VirtualFolder


@receiver(post_save, sender=Store)
def handle_store_save(sender, instance, created, **kwargs):
    if not created:
        return
    project_vfolders = instance.translation_project.project.vfolders
    language_vfolders = instance.translation_project.language.vfolders

    # limit to vfolders that could be possibly related
    vfolders = (
        project_vfolders.filter(language__isnull=True)
        | language_vfolders.filter(language__isnull=True)
        | project_vfolders.filter(
            language=instance.translation_project.language)
        | VirtualFolder.objects.filter(
            language__isnull=True,
            project__isnull=True))
    for vf in vfolders:
        vf.path_matcher.add_store_if_matching(instance)
        # todo: remove store if not matching


@receiver(post_save, sender=VirtualFolder)
def handle_vfolder_save(sender, instance, created, **kwargs):
    instance.path_matcher.update_matching_stores()


@receiver(post_save, sender=StoreData)
def handle_storedata_save(**kwargs):
    store = kwargs["instance"].store
    for vf in store.vfolders.all():
        update_data.send_robust(vf.__class__, instance=vf)


@receiver(update_data, sender=VirtualFolder)
def handle_store_data_update(**kwargs):
    vf = kwargs["instance"]
    vf.data_tool.update()
