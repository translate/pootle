# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from pootle.core.delegate import data_tool
from pootle.core.signals import update_data
from pootle_store.models import Store
from pootle_translationproject.models import TranslationProject

from .models import StoreData


logger = logging.getLogger(__name__)


@receiver(post_save, sender=StoreData)
def handle_storedata_save(**kwargs):
    tp = kwargs["instance"].store.translation_project
    update_data.send(tp.__class__, instance=tp)


@receiver(update_data, sender=Store)
def handle_store_data_update(**kwargs):
    store = kwargs["instance"]
    data_tool.get(Store)(store).update()


@receiver(update_data, sender=TranslationProject)
def handle_tp_data_update(**kwargs):
    tp = kwargs["instance"]
    data_tool.get(TranslationProject)(tp).update()


@receiver(post_save, sender=Store)
def handle_store_data_create(sender, instance, created, **kwargs):
    if created:
        update_data.send(instance.__class__, instance=instance)


@receiver(post_save, sender=TranslationProject)
def handle_tp_data_create(sender, instance, created, **kwargs):
    if created:
        update_data.send(instance.__class__, instance=instance)
