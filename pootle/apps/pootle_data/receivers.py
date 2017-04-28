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

from pootle.core.delegate import crud, data_tool, data_updater
from pootle.core.signals import create, delete, update, update_data
from pootle_store.models import Store
from pootle_translationproject.models import TranslationProject

from .models import StoreChecksData, StoreData, TPChecksData, TPData


logger = logging.getLogger(__name__)


@receiver(create, sender=StoreData)
def handle_store_data_obj_create(**kwargs):
    crud.get(StoreData).create(**kwargs)


@receiver(create, sender=TPData)
def handle_tp_data_obj_create(**kwargs):
    crud.get(TPData).create(**kwargs)


@receiver(update, sender=StoreData)
def handle_store_data_obj_update(**kwargs):
    crud.get(StoreData).update(**kwargs)


@receiver(update, sender=TPData)
def handle_tp_data_obj_update(**kwargs):
    crud.get(TPData).update(**kwargs)


@receiver(delete, sender=StoreChecksData)
def handle_store_checks_data_delete(**kwargs):
    crud.get(StoreChecksData).delete(**kwargs)


@receiver(create, sender=StoreChecksData)
def handle_store_checks_data_create(**kwargs):
    crud.get(StoreChecksData).create(**kwargs)


@receiver(update, sender=StoreChecksData)
def handle_store_checks_data_update(**kwargs):
    crud.get(StoreChecksData).update(**kwargs)


@receiver(update, sender=TPChecksData)
def handle_tp_checks_data_update(**kwargs):
    crud.get(TPChecksData).update(**kwargs)


@receiver(delete, sender=TPChecksData)
def handle_tp_checks_data_delete(**kwargs):
    crud.get(TPChecksData).delete(**kwargs)


@receiver(create, sender=TPChecksData)
def handle_tp_checks_data_create(**kwargs):
    crud.get(TPChecksData).create(**kwargs)


@receiver(post_save, sender=StoreData)
def handle_storedata_save(**kwargs):
    tp = kwargs["instance"].store.translation_project
    update_data.send(tp.__class__, instance=tp)


@receiver(update_data, sender=Store)
def handle_store_data_update(**kwargs):
    store = kwargs.get("instance")
    data_tool.get(Store)(store).update()


@receiver(update_data, sender=TranslationProject)
def handle_tp_data_update(**kwargs):
    tp = kwargs["instance"]
    if "object_list" in kwargs:
        data_updater.get(TranslationProject)(
            tp,
            object_list=kwargs["object_list"]).update()
    else:
        data_tool.get(TranslationProject)(tp).update()


@receiver(post_save, sender=Store)
def handle_store_data_create(sender, instance, created, **kwargs):
    if created:
        data_updater.get(instance.data_tool.__class__)(instance.data_tool).update()


@receiver(post_save, sender=TranslationProject)
def handle_tp_data_create(sender, instance, created, **kwargs):
    if created:
        update_data.send(instance.__class__, instance=instance)
