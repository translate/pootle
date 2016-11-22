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
from pootle_data.models import StoreData
from pootle_store.models import Store


@receiver(post_save, sender=StoreData)
def handle_storedata_save(**kwargs):
    revision_updater.get(Store)(
        context=kwargs["instance"].store).update(keys=["stats", "checks"])


@receiver(post_save, sender=Directory)
def handle_directory_save(**kwargs):
    if kwargs.get("created"):
        return
    revision_updater.get(Directory)(
        context=kwargs["instance"]).update(keys=["stats", "checks"])


@receiver(pre_delete, sender=Directory)
def handle_directory_delete(**kwargs):
    revision_updater.get(Directory)(
        context=kwargs["instance"].parent).update(keys=["stats", "checks"])
