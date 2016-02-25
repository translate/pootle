# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.db.models.signals import pre_save
from django.dispatch import receiver

from pootle_store.models import Store


@receiver(pre_save, sender=Store)
def store_unit_pre_save_handler(sender, instance, **kwargs):
    """If a Store's pootle_path or translation_project change then update the
    pootle_path, project, and language on the Store's Units.
    """

    if instance.pk is None:
        return

    original = Store.objects.get(pk=instance.pk)
    to_update = {}

    if original.pootle_path != instance.pootle_path:
        to_update["pootle_path"] = instance.pootle_path
    if original.translation_project != instance.translation_project:
        to_update.update(
            dict(project_id=instance.translation_project.project_id,
                 language_id=instance.translation_project.language_id))
    if to_update:
        original.units.update(**to_update)
