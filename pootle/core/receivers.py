# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.db.models.signals import pre_save
from django.dispatch import receiver

from pootle.core.site import pootle_site
from pootle_language.models import Language
from pootle_project.models import Project


@receiver(pre_save, sender=Language)
def language_cache_expiry_pre_save_handler(sender, instance, **kwargs):
    """Expire pootle.core.site.pootle_site Languages
    """
    # import pdb; pdb.set_trace()
    if "languages" in pootle_site.__dict__:
        del pootle_site.__dict__["languages"]


@receiver(pre_save, sender=Project)
def project_cache_expiry_pre_save_handler(sender, instance, **kwargs):
    """Expire pootle.core.site.pootle_site Projects
    """
    if "projects" in pootle_site.__dict__:
        del pootle_site.__dict__["projects"]
