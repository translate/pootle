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

    @property
    def children(self):
        if not self.view.vfolders_data_view:
            return {}
        return self.view.vfolders_data_view.table_items

    @property
    def vfdata(self):
        vfdata = self.view.vfolders_data_view
        if not self.view.has_vfolders:
            return vfdata
        return vfdata

    @property
    def table(self):
        return (
            self.vfdata.table_data["children"]
            if self.vfdata and self.vfdata.table_data
            else "")
