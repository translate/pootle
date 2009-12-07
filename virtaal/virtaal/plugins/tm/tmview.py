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
import gobject
import logging
from gtk import gdk

from virtaal.common import GObjectWrapper
from virtaal.views import BaseView
from virtaal.views.widgets.selectdialog import SelectDialog

from tmwidgets import *


class TMView(BaseView, GObjectWrapper):
    """The fake drop-down menu in which the TM matches are displayed."""

    __gtype_name__ = 'TMView'
    __gsignals__ = {
        'tm-match-selected': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,)),
    }

    # INITIALIZERS #
    def __init__(self, controller, max_matches):
        GObjectWrapper.__init__(self)

        self.controller = controller
        self.isvisible = False
        self.max_matches = max_matches
        self._may_show_tmwindow = False
        self._should_show_tmwindow = False
        self._signal_ids = []

        self.tmwindow = TMWindow(self)
        main_window = self.controller.main_controller.view.main_window

        self._signal_ids.append((
            self.tmwindow.treeview,
            self.tmwindow.treeview.connect('row-activated', self._on_row_activated)
        ))
        self._signal_ids.append((
            controller.main_controller.store_controller.view.parent_widget.get_vscrollbar(),
            controller.main_controller.store_controller.view.parent_widget.get_vscrollbar().connect('value-changed', self._on_store_view_scroll)
        ))
        self._signal_ids.append((
            main_window,
            main_window.connect('focus-in-event', self._on_focus_in_mainwindow)
        ))
        self._signal_ids.append((
            main_window,
            main_window.connect('focus-out-event', self._on_focus_out_mainwindow)
        ))

        self._setup_key_bindings()
        self._setup_menu_items()

    def _setup_key_bindings(self):
        """Setup Gtk+ key bindings (accelerators)."""

        gtk.accel_map_add_entry("<Virtaal>/TM/Hide TM", gtk.keysyms.Escape, 0)

        self.accel_group = gtk.AccelGroup()
        self.accel_group.connect_by_path("<Virtaal>/TM/Hide TM", self._on_hide_tm)

        # Connect Ctrl+n (1 <= n <= 9) to select match n.
        for i in range(1, 10):
            numstr = str(i)
            numkey = gtk.keysyms._0 + i
            gtk.accel_map_add_entry("<Virtaal>/TM/Select match " + numstr, numkey, gdk.CONTROL_MASK)
            self.accel_group.connect_by_path("<Virtaal>/TM/Select match " + numstr, self._on_select_match)

        mainview = self.controller.main_controller.view
        mainview.add_accel_group(self.accel_group)

    def _setup_menu_items(self):
        mainview = self.controller.main_controller.view
        menubar = mainview.menubar
        self.mnui_view = mainview.gui.get_widget('menuitem_view')
        self.menu = self.mnui_view.get_submenu()

        self.mnu_suggestions = gtk.CheckMenuItem(label=_('Translation _Suggestions'))
        self.mnu_suggestions.show()
        self.menu.append(self.mnu_suggestions)

        gtk.accel_map_add_entry("<Virtaal>/TM/Toggle Show TM", gtk.keysyms.F9, 0)
        accel_group = self.menu.get_accel_group()
        if accel_group is None:
            accel_group = self.accel_group
            self.menu.set_accel_group(self.accel_group)
        self.mnu_suggestions.set_accel_path("<Virtaal>/TM/Toggle Show TM")
        self.menu.set_accel_group(accel_group)

        self.mnu_suggestions.connect('toggled', self._on_toggle_show_tm)
        self.mnu_suggestions.set_active(True)


    # ACCESSORS #
    def _get_active(self):
        return self.mnu_suggestions.get_active()
    active = property(_get_active)


    # METHODS #
    def clear(self):
        """Clear the TM matches."""
        self.tmwindow.liststore.clear()
        self.hide()

    def destroy(self):
        for gobj, signal_id in self._signal_ids:
            gobj.disconnect(signal_id)

        self.menu.remove(self.mnu_suggestions)

    def display_matches(self, matches):
        """Add the list of TM matches to those available and show the TM window."""
        liststore = self.tmwindow.liststore
        liststore.clear()
        for match in matches:
            tooltip = ''
            if len(liststore) <= 9:
                tooltip = _('Ctrl+%(number_key)d') % {"number_key": len(liststore)+1}
            liststore.append([match, tooltip])

        if len(liststore) > 0:
            self.show()
            self.update_geometry()

    def get_target_width(self):
        if not hasattr(self.controller, 'unit_view'):
            return -1
        n = self.controller.unit_view.focused_target_n
        textview = self.controller.unit_view.targets[n]
        return textview.get_allocation().width

    def hide(self):
        """Hide the TM window."""
        self.tmwindow.hide()
        self.isvisible = False

    def select_backends(self, menuitem):
        selectdlg = SelectDialog(
            #l10n: The 'sources' here refer to different translation memory plugins,
            #such as local tm, open-tran.eu, the current file, etc.
            title=_('Select sources of Translation Memory'),
            message=_('Select the sources that should be queried for translation memory')
        )
        selectdlg.set_icon(self.controller.main_controller.view.main_window.get_icon())

        items = []
        plugin_controller = self.controller.plugin_controller
        for plugin_name in plugin_controller._find_plugin_names():
            if plugin_name == 'basetmmodel':
                continue
            try:
                info = plugin_controller.get_plugin_info(plugin_name)
            except Exception, e:
                logging.debug('Problem getting information for plugin %s' % plugin_name)
                continue
            enabled = plugin_name in plugin_controller.plugins
            item = {'name': plugin_name}
            config = enabled and plugin_controller.plugins[plugin_name] or None
            items.append({
                'name': info['display_name'],
                'desc': info['description'],
                'data': {'internal_name': plugin_name},
                'enabled': enabled,
                'config': config,
            })

        def item_enabled(dlg, item):
            internal_name = item['data']['internal_name']
            plugin_controller.enable_plugin(internal_name)
            if internal_name in self.controller.config['disabled_models']:
                self.controller.config['disabled_models'].remove(internal_name)

        def item_disabled(dlg, item):
            internal_name = item['data']['internal_name']
            plugin_controller.disable_plugin(internal_name)
            if internal_name not in self.controller.config['disabled_models']:
                self.controller.config['disabled_models'].append(internal_name)

        selectdlg.connect('item-enabled',  item_enabled)
        selectdlg.connect('item-disabled', item_disabled)
        selectdlg.run(items=items)

    def select_match(self, match_data):
        """Select the match data as accepted by the user."""
        self.controller.select_match(match_data)

    def select_match_index(self, index):
        """Select the TM match with the given index (first match is 1).
            This method causes a row in the TM window's C{gtk.TreeView} to be
            selected and activated. This runs this class's C{_on_select_match()}
            method which runs C{select_match()}."""
        if index < 0 or not self.isvisible:
            return

        logging.debug('Selecting index %d' % (index))
        liststore = self.tmwindow.liststore
        itr = liststore.get_iter_first()

        i=1
        while itr and i < index and liststore.iter_is_valid(itr):
            itr = liststore.iter_next(itr)
            i += 1

        if not itr or not liststore.iter_is_valid(itr):
            return

        path = liststore.get_path(itr)
        self.tmwindow.treeview.get_selection().select_iter(itr)
        self.tmwindow.treeview.row_activated(path, self.tmwindow.tvc_match)

    def show(self, force=False):
        """Show the TM window."""
        if not self.active or (self.isvisible and not force) or not self._may_show_tmwindow:
            return # This window is already visible
        self.tmwindow.show_all()
        self.isvisible = True
        self._should_show_tmwindow = False

    def update_geometry(self):
        """Update the TM window's position and size."""
        def update():
            selected = self._get_selected_unit_view()
            self.tmwindow.update_geometry(selected)
        gobject.idle_add(update)

    def _get_selected_unit_view(self):
        n = self.controller.main_controller.unit_controller.view.focused_target_n
        if n is None:
            n = 0
        return self.controller.main_controller.unit_controller.view.targets[n]


    # EVENT HANDLERS #
    def _on_focus_in_mainwindow(self, widget, event):
        self._may_show_tmwindow = True
        if not self._should_show_tmwindow or self.isvisible:
            return
        self.show()

        selected = self._get_selected_unit_view()
        self.tmwindow.update_geometry(selected)

    def _on_focus_out_mainwindow(self, widget, event):
        self._may_show_tmwindow = False
        if not self.isvisible:
            return
        self.hide()
        self._should_show_tmwindow = True

    def _on_hide_tm(self, accel_group, acceleratable, keyval, modifier):
        self.hide()

    def _on_row_activated(self, treeview, path, column):
        """Called when a TM match is selected in the TM window."""
        liststore = treeview.get_model()
        assert liststore is self.tmwindow.liststore
        itr = liststore.get_iter(path)
        match_data = liststore.get_value(itr, 0)

        self.select_match(match_data)

    def _on_select_match(self, accel_group, acceleratable, keyval, modifier):
        self.select_match_index(int(keyval - gtk.keysyms._0))

    def _on_store_view_scroll(self, *args):
        if self.isvisible:
            self.hide()

    def _on_toggle_show_tm(self, *args):
        if not self.active and self.isvisible:
            self.hide()
        elif self.active and not self.isvisible:
            self.controller.start_query()
