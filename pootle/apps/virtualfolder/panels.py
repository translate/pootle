# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle_app.panels import ChildrenPanel


class VFolderPanel(ChildrenPanel):
    panel_name = "vfolder"
    table_fields = [
        'name', 'progress', 'total', 'need-translation',
        'suggestions', 'critical', 'last-updated', 'activity']

    @property
    def table(self):
        if not self.view.vfolders_data_view:
            return ""
        vfdata = self.view.vfolders_data_view.table_data
        if not vfdata:
            return ""
        return vfdata["children"]
