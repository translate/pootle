# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.db.models.signals import m2m_changed, pre_save
from django.dispatch import receiver

from pootle.core.signals import filetypes_changed
from pootle_project.models import Project

from .models import Format


@receiver(pre_save, sender=Format)
def format_pre_save_handler(**kwargs):
    instance = kwargs["instance"]
    if not instance.title:
        instance.title = instance.name.capitalize()


@receiver(m2m_changed, sender=Project.filetypes.through)
def project_filetypes_changed_handler(**kwargs):
    if kwargs["action"] in ["post_add", "post_remove", "post_clear"]:
        del kwargs["sender"]
        del kwargs["signal"]
        filetypes_changed.send(Project, **kwargs)
