# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.utils.functional import cached_property

from pootle.core.views.display import StatsDisplay


class VFolderStatsDisplay(StatsDisplay):

    @cached_property
    def stats(self):
        stats = self.stat_data
        for k, item in stats.items():
            item["incomplete"] = item["total"] - item["translated"]
            item["untranslated"] = item["total"] - item["translated"]
            self.localize_stats(item)
        return stats
