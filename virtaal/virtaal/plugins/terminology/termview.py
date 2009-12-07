#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Zuza Software Foundation
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
import logging

from virtaal.views import BaseView, rendering
from virtaal.views.placeablesguiinfo import StringElemGUI
from virtaal.views.widgets.selectdialog import SelectDialog


class TerminologyGUIInfo(StringElemGUI):
    """
    GUI info object for terminology placeables. It creates a combo box to
    choose the selected match from.
    """
    # MEMBERS #
    bg = '#eeffee'
    fg = '#006600'

    def __init__(self, elem, textbox, **kwargs):
        assert elem.__class__.__name__ == 'TerminologyPlaceable'
        super(TerminologyGUIInfo, self).__init__(elem, textbox, **kwargs)


    # METHODS #
    def get_insert_widget(self):
        if len(self.elem.translations) > 1:
            return TerminologyCombo(self.elem)
        return None


class TerminologyCombo(gtk.ComboBox):
    """
    A combo box containing translation matches.
    """

    # INITIALIZERS #
    def __init__(self, elem):
        super(TerminologyCombo, self).__init__()
        self.elem = elem
        self.insert_iter = None
        self.selected_string = None
        self.set_name('termcombo')
        # Let's make it as small as possible, since we don't want to see the
        # combo at all.
        self.set_size_request(0, 0)
        self.__init_combo()
        cell_renderers = self.get_cells()
        # Set the font correctly for the target
        if cell_renderers:
            cell_renderers[0].props.font_desc = rendering.get_target_font_description()
        self.menu = self.menu_get_for_attach_widget()[0]
        self.menu.connect('selection-done', self._on_selection_done)

    def __init_combo(self):
        self._model = gtk.ListStore(str)
        for trans in self.elem.translations:
            self._model.append([trans])

        self.set_model(self._model)
        self._renderer = gtk.CellRendererText()
        self.pack_start(self._renderer)
        self.add_attribute(self._renderer, 'text', 0)

        # Force the "appears-as-list" style property to 0
        rc_string = """
            style "not-a-list"
            {
                GtkComboBox::appears-as-list = 0
            }
            class "GtkComboBox" style "not-a-list"
            """
        gtk.rc_parse_string(rc_string)


    # METHODS #
    def inserted(self, insert_iter, anchor):
        self.insert_offset = insert_iter.get_offset()
        self.grab_focus()
        self.popup()

    def insert_selected(self):
        iter = self.get_active_iter()
        if iter:
            self.selected_string = self._model.get_value(iter, 0)

        if self.parent:
            self.parent.grab_focus()

        parent = self.parent
        buffer = parent.get_buffer()
        parent.remove(self)
        if self.insert_offset >= 0:
            iterins  = buffer.get_iter_at_offset(self.insert_offset)
            iternext = buffer.get_iter_at_offset(self.insert_offset + 1)
            if iternext:
                buffer.delete(iterins, iternext)

            iterins  = buffer.get_iter_at_offset(self.insert_offset)
            parent.refresh_cursor_pos = buffer.props.cursor_position
            if self.selected_string:
                buffer.insert(iterins, self.selected_string)


    # EVENT HANDLERS #
    def _on_selection_done(self, menushell):
        self.insert_selected()


class TerminologyView(BaseView):
    """
    Does general GUI setup for the terminology plug-in.
    """

    # INITIALIZERS #
    def __init__(self, controller):
        self.controller = controller
        self._signal_ids = []


    # METHODS #
    def destroy(self):
        for gobj, signal_id in self._signal_ids:
            gobj.disconnect(signal_id)

    def select_backends(self, menuitem):
        selectdlg = SelectDialog(
            title=_('Select Terminology Sources'),
            message=_('Select the sources of terminology suggestions'),
            size=(self.controller.config['backends_dialog_width'], -1),
        )
        selectdlg.set_icon(self.controller.main_controller.view.main_window.get_icon())

        items = []
        plugin_controller = self.controller.plugin_controller
        for plugin_name in plugin_controller._find_plugin_names():
            if plugin_name == 'basetermmodel':
                continue
            try:
                info = plugin_controller.get_plugin_info(plugin_name)
            except Exception, e:
                logging.debug('Problem getting information for plugin %s' % plugin_name)
                continue
            enabled = plugin_name in plugin_controller.plugins
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
