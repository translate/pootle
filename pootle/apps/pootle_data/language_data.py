# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from .utils import RelatedTPsDataTool


class LanguageDataTool(RelatedTPsDataTool):
    """Retrieves aggregate stats for a Language"""

    cache_key_name = "language"

    def filter_data(self, qs):
        return qs.filter(tp__language=self.context)
