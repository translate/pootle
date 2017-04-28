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

store_checks_data_crud = crud.get(StoreChecksData)
store_data_crud = crud.get(StoreData)
store_data_tool = data_tool.get(Store)
tp_data_crud = crud.get(TPData)
tp_checks_data_crud = crud.get(TPChecksData)
tp_data_tool = data_tool.get(TranslationProject)
tp_data_updater = data_updater.get(TranslationProject)


@receiver(create, sender=StoreData)
def handle_store_data_obj_create(**kwargs):
    store_data_crud.create(**kwargs)


@receiver(create, sender=TPData)
def handle_tp_data_obj_create(**kwargs):
    tp_data_crud.create(**kwargs)


@receiver(update, sender=StoreData)
def handle_store_data_obj_update(**kwargs):
    tps = set(
        storedata.store.translation_project
        for storedata
        in store_data_crud.update(**kwargs))
    for tp in tps:
        update_data.send(tp.__class__, instance=tp)


@receiver(update, sender=TPData)
def handle_tp_data_obj_update(**kwargs):
    tp_data_crud.update(**kwargs)


@receiver(delete, sender=StoreChecksData)
def handle_store_checks_data_delete(**kwargs):
    store_checks_data_crud.delete(**kwargs)


@receiver(create, sender=StoreChecksData)
def handle_store_checks_data_create(**kwargs):
    store_checks_data_crud.create(**kwargs)


@receiver(update, sender=StoreChecksData)
def handle_store_checks_data_update(**kwargs):
    store_checks_data_crud.update(**kwargs)


@receiver(update, sender=TPChecksData)
def handle_tp_checks_data_update(**kwargs):
    tp_checks_data_crud.update(**kwargs)


@receiver(delete, sender=TPChecksData)
def handle_tp_checks_data_delete(**kwargs):
    tp_checks_data_crud.delete(**kwargs)


@receiver(create, sender=TPChecksData)
def handle_tp_checks_data_create(**kwargs):
    tp_checks_data_crud.create(**kwargs)


@receiver(post_save, sender=StoreData)
def handle_storedata_save(**kwargs):
    tp = kwargs["instance"].store.translation_project
    update_data.send(tp.__class__, instance=tp)


@receiver(update_data, sender=Store)
def handle_store_data_update(**kwargs):
    store = kwargs.get("instance")
    store_data_tool(store).update()


@receiver(update_data, sender=TranslationProject)
def handle_tp_data_update(**kwargs):
    tp = kwargs["instance"]
    if "object_list" in kwargs:
        tp_data_updater(
            tp,
            object_list=kwargs["object_list"]).update()
    else:
        tp_data_tool(tp).update()


@receiver(post_save, sender=Store)
def handle_store_data_create(sender, instance, created, **kwargs):
    if created:
        store_data_tool(instance).update()


@receiver(post_save, sender=TranslationProject)
def handle_tp_data_create(sender, instance, created, **kwargs):
    if created:
        update_data.send(instance.__class__, instance=instance)
