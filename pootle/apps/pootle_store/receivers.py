# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.dispatch import receiver

from pootle.core.mixins import CachedMethods
from pootle.core.signals import clear_cache
from pootle_store.models import Store


@receiver(clear_cache, sender=Store)
def clear_cache_handler(**kwargs):
    kwargs["instance"].mark_dirty(CachedMethods.MTIME)
    kwargs["instance"].update_dirty_cache()
