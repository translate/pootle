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

import logging
import gtk

from virtaal.views import BaseView
from virtaal.views.widgets.selectdialog import SelectDialog


class LookupView(BaseView):
    """
    Makes look-up models accessible via the source- and target text views'
    context menu.
    """

    # INITIALIZERS #
    def __init__(self, controller):
        self.controller = controller
        self.lang_controller = controller.main_controller.lang_controller

        self._connect_to_unitview(controller.main_controller.unit_controller.view)

    def _connect_to_unitview(self, unitview):
        self._textbox_ids = []
        for textbox in unitview.sources + unitview.targets:
            self._textbox_ids.append((
                textbox,
                textbox.connect('populate-popup', self._on_populate_popup)
            ))


    # METHODS #
    def destroy(self):
        for textbox, id in self._textbox_ids:
            textbox.disconnect(id)

    def select_backends(self, parent):
        selectdlg = SelectDialog(
            #l10n: The 'services' here refer to different look-up plugins,
            #such as web look-up, etc.
            title=_('Select Look-up Services'),
            message=_('Select the services that should be used to perform look-ups'),
            size=(self.controller.config['backends_dialog_width'], -1)
        )
        if isinstance(parent, gtk.Window):
            selectdlg.set_transient_for(parent)
            selectdlg.set_icon(parent.get_icon())

        items = []
        plugin_controller = self.controller.plugin_controller
        for plugin_name in plugin_controller._find_plugin_names():
            if plugin_name == 'baselookupmodel':
                continue
            try:
                info = plugin_controller.get_plugin_info(plugin_name)
            except Exception, e:
                logging.debug('Problem getting information for plugin %s' % plugin_name)
                continue
            enabled = plugin_name in plugin_controller.plugins
            item = {'name': plugin_name}
            config = None
            if hasattr(plugin_controller.plugins[plugin_name], 'configure_func'):
                config = plugin_controller.plugins[plugin_name].configure_func

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


    # SIGNAL HANDLERS #
    def _on_lookup_selected(self, menuitem, plugin, query, query_is_source):
        plugin.lookup(query, query_is_source, srclang, tgtlang)

    def _on_populate_popup(self, textbox, menu):
        buf = textbox.buffer
        if not buf.get_has_selection():
            return

        selection = buf.get_text(*buf.get_selection_bounds())
        role      = textbox.role
        srclang   = self.lang_controller.source_lang.code
        tgtlang   = self.lang_controller.target_lang.code

        lookup_menu = gtk.Menu()
        menu_item = gtk.MenuItem(_('Look-up "%(selection)s"') % {'selection': selection})

        plugins = self.controller.plugin_controller.plugins
        menu_items = []
        names = plugins.keys()
        names.sort()
        for name in names:
            menu_items.extend(
                plugins[name].create_menu_items(selection, role, srclang, tgtlang)
            )
        if not menu_items:
            return

        for i in menu_items:
            lookup_menu.append(i)

        sep = gtk.SeparatorMenuItem()
        sep.show()
        menu.append(sep)
        menu_item.set_submenu(lookup_menu)
        menu_item.show_all()
        menu.append(menu_item)
