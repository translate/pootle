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
from pootle.core.signals import update_revisions
from pootle_app.models import Directory
from pootle_data.models import StoreData
from pootle_store.models import Store
from pootle_translationproject.models import TranslationProject


@receiver(post_save, sender=StoreData)
def handle_storedata_save(**kwargs):
    update_revisions.send(
        Store,
        instance=kwargs["instance"].store,
        keys=["stats", "checks"])


@receiver(update_revisions, sender=Store)
def handle_store_revision_update(**kwargs):
    revision_updater.get(Store)(
        context=kwargs["instance"]).update(keys=kwargs.get("keys"))


@receiver(post_save, sender=Directory)
def handle_directory_save(**kwargs):
    update_revisions.send(
        Directory,
        instance=(
            kwargs["instance"].parent
            if kwargs.get("created")
            else kwargs["instance"]),
        keys=["stats", "checks"])


@receiver(update_revisions, sender=Directory)
def handle_directory_revision_update(**kwargs):
    updater = revision_updater.get(Directory)
    if kwargs.get("instance"):
        updater(context=kwargs["instance"]).update(
            keys=kwargs.get("keys"))
    else:
        updater(
            object_list=kwargs.get("object_list"),
            paths=kwargs.get("paths")).update(
                keys=kwargs.get("keys"))


@receiver(pre_delete, sender=Directory)
def handle_directory_delete(**kwargs):
    update_revisions.send(
        Directory,
        instance=kwargs["instance"].parent,
        keys=["stats", "checks"])


@receiver(pre_delete, sender=TranslationProject)
def handle_tp_delete(**kwargs):
    update_revisions.send(
        Directory,
        instance=kwargs["instance"].directory,
        keys=["stats", "checks"])
