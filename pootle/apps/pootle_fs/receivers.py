# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.dispatch import receiver

from pootle.core.exceptions import NotConfiguredError
from pootle.core.signals import filetypes_changed
from pootle_project.models import Project

from .utils import FSPlugin


@receiver(filetypes_changed, sender=Project)
def handle_project_filetypes_changed(**kwargs):
    project = kwargs["instance"]

    if project.treestyle == "pootle_fs":
        try:
            FSPlugin(project).expire_sync_cache()
        except NotConfiguredError:
            pass
