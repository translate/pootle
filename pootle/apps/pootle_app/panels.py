# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle.core.browser import get_table_headings
from pootle.core.views.panels import TablePanel


class ChildrenPanel(TablePanel):
    panel_name = "children"
    table_fields = [
        'name', 'progress', 'total', 'need-translation',
        'suggestions', 'critical', 'last-updated', 'activity']

    @property
    def table(self):
        if self.view.object_children:
            return {
                'id': self.view.view_name,
                'fields': self.table_fields,
                'headings': get_table_headings(self.table_fields),
                'rows': self.view.object_children}

    def get_context_data(self):
        return dict(
            table=self.table,
            can_translate=self.view.can_translate)
