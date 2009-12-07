#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008 Zuza Software Foundation
#
# This file is part of Virtaal.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

import gtk

from baseview import BaseView
from widgets.storeviewwidgets import *


# XXX: ASSUMPTION: The model to display is self.controller.store
# TODO: Add event handler for store controller's cursor-creation event, so that
#       the store view can connect to the new cursor's "cursor-changed" event
#       (which is currently done in load_store())
class StoreView(BaseView):
    """The view of the store and interface to store-level actions."""

    # INITIALIZERS #
    def __init__(self, controller):
        self.controller = controller
        # XXX: While I can't think of a better way to do this, the following line would have to do :/
        self.parent_widget = self.controller.main_controller.view.gui.get_widget('scrolledwindow1')

        self._init_treeview()
        self._add_accelerator_bindings()
        self.load_store(self.controller.store)

        self.controller.main_controller.view.main_window.connect('configure-event', self._treeview.on_configure_event)

    def _init_treeview(self):
        self._treeview = StoreTreeView(self)

    def _add_accelerator_bindings(self):
        gtk.accel_map_add_entry("<Virtaal>/Navigation/Up", gtk.accelerator_parse("Up")[0], gdk.CONTROL_MASK)
        gtk.accel_map_add_entry("<Virtaal>/Navigation/Down", gtk.accelerator_parse("Down")[0], gdk.CONTROL_MASK)
        gtk.accel_map_add_entry("<Virtaal>/Navigation/PgUp", gtk.accelerator_parse("Page_Up")[0], gdk.CONTROL_MASK)
        gtk.accel_map_add_entry("<Virtaal>/Navigation/PgDown", gtk.accelerator_parse("Page_Down")[0], gdk.CONTROL_MASK)

        self.accel_group = gtk.AccelGroup()
        self.accel_group.connect_by_path("<Virtaal>/Navigation/Up", self._treeview._move_up)
        self.accel_group.connect_by_path("<Virtaal>/Navigation/Down", self._treeview._move_down)
        self.accel_group.connect_by_path("<Virtaal>/Navigation/PgUp", self._treeview._move_pgup)
        self.accel_group.connect_by_path("<Virtaal>/Navigation/PgDown", self._treeview._move_pgdown)

        mainview = self.controller.main_controller.view
        mainview.add_accel_group(self.accel_group)
        mainview.gui.get_widget('menu_navigation').set_accel_group(self.accel_group)
        self.mnu_up = mainview.gui.get_widget('mnu_up')
        self.mnu_down = mainview.gui.get_widget('mnu_down')
        self.mnu_pageup = mainview.gui.get_widget('mnu_pageup')
        self.mnu_pagedown = mainview.gui.get_widget('mnu_pagedown')
        self.mnu_up.set_accel_path('<Virtaal>/Navigation/Up')
        self.mnu_down.set_accel_path('<Virtaal>/Navigation/Down')
        self.mnu_pageup.set_accel_path('<Virtaal>/Navigation/PgUp')
        self.mnu_pagedown.set_accel_path('<Virtaal>/Navigation/PgDown')

        self._set_menu_items_sensitive(False)


    # ACCESSORS #
    def _get_cursor(self):
        return self.controller.cursor
    cursor = property(_get_cursor)

    def get_store(self):
        return self.store

    def get_unit_celleditor(self, unit):
        return self.controller.get_unit_celleditor(unit)


    # METHODS #
    def load_store(self, store):
        self.store = store
        if store:
            self._treeview.set_model(store)
            self._set_menu_items_sensitive(True)
            self.cursor.connect('cursor-changed', self._on_cursor_change)

    def show(self):
        child = self.parent_widget.get_child()
        if child is not self._treeview:
            self.parent_widget.remove(child)
            child.destroy()
            self.parent_widget.add(self._treeview)
        self._treeview.show()
        self._treeview.select_index(0)

        if self._treeview.get_model():
            selection = self._treeview.get_selection()
            selection.select_iter(self._treeview.get_model().get_iter_first())

    def _set_menu_items_sensitive(self, sensitive=True):
        for widget in (self.mnu_up, self.mnu_down, self.mnu_pageup, self.mnu_pagedown):
            widget.set_sensitive(sensitive)


    # EVENT HANDLERS #
    def _on_cursor_change(self, cursor):
        self._treeview.select_index(cursor.index)
