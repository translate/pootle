# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.dispatch import receiver

from pootle.core.signals import config_updated, update_revisions
from pootle_project.models import Project


@receiver(config_updated, sender=Project)
def config_updated_handler(**kwargs):
    if kwargs["instance"] and kwargs["key"] == "pootle.core.lang_mapping":
        update_revisions.send(
            Project,
            instance=kwargs["instance"],
            keys=["stats"])
