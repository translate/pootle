# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle.core.paths import Paths
from pootle_store.models import Store

from .apps import PootleProjectConfig


class ProjectPaths(Paths):
    ns = "pootle.project"
    sw_version = PootleProjectConfig.version

    @property
    def store_qs(self):
        return Store.objects.filter(
            translation_project__project_id=self.context.id)
