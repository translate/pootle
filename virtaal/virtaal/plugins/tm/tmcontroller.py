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

import gobject
import logging
import os.path
from translate.lang.data import forceunicode

from virtaal.common import GObjectWrapper, pan_app
from virtaal.controllers import BaseController, PluginController

import models
from models.basetmmodel import BaseTMModel
from tmview import TMView


class TMController(BaseController):
    """The logic-filled glue between the TM view and -model."""

    __gtype_name__ = 'TMController'
    __gsignals__ = {
        'start-query': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_STRING,))
    }

    QUERY_DELAY = 300
    """The delay after a unit is selected (C{Cursor}'s "cursor-changed" event)
        before the TM is queried."""

    # INITIALIZERS #
    def __init__(self, main_controller, config={}):
        GObjectWrapper.__init__(self)

        self.config = config
        self.main_controller = main_controller
        self.disabled_model_names = ['basetmmodel'] + self.config.get('disabled_models', [])
        self.max_matches = self.config.get('max_matches', 5)
        self.min_quality = self.config.get('min_quality', 75)

        self._signal_ids = {}
        self.view = TMView(self, self.max_matches)
        self._load_models()

        self._connect_plugin()

    def _connect_plugin(self):
        self._store_loaded_id = self.main_controller.store_controller.connect('store-loaded', self._on_store_loaded)
        if self.main_controller.store_controller.get_store() is not None:
            self._on_store_loaded(self.main_controller.store_controller)
            self.view._should_show_tmwindow = True

        if self.main_controller.mode_controller is not None:
            self._mode_selected_id = self.main_controller.mode_controller.connect('mode-selected', self._on_mode_selected)

    def _load_models(self):
        self.plugin_controller = PluginController(self)
        self.plugin_controller.PLUGIN_CLASSNAME = 'TMModel'
        self.plugin_controller.PLUGIN_CLASS_INFO_ATTRIBS = ['display_name', 'description']
        new_dirs = []
        for dir in self.plugin_controller.PLUGIN_DIRS:
           new_dirs.append(os.path.join(dir, 'tm', 'models'))
        self.plugin_controller.PLUGIN_DIRS = new_dirs

        self.plugin_controller.PLUGIN_INTERFACE = BaseTMModel
        self.plugin_controller.PLUGIN_MODULES = ['virtaal_plugins.tm.models', 'virtaal.plugins.tm.models']
        self.plugin_controller.get_disabled_plugins = lambda *args: self.disabled_model_names

        self._model_signal_ids = {}
        def on_plugin_enabled(plugin_ctrlr, plugin):
            self._model_signal_ids[plugin] = plugin.connect('match-found', self.accept_response)
        def on_plugin_disabled(plugin_ctrlr, plugin):
            plugin.disconnect(self._model_signal_ids[plugin])
        self._signal_ids['plugin-enabled']  = self.plugin_controller.connect('plugin-enabled',  on_plugin_enabled)
        self._signal_ids['plugin-disabled'] = self.plugin_controller.connect('plugin-disabled', on_plugin_disabled)

        self.plugin_controller.load_plugins()


    # METHODS #
    def accept_response(self, tmmodel, query_str, matches):
        """Accept a query-response from the model.
            (This method is used as Model-Controller communications)"""
        if query_str != self.current_query or not matches:
            return
        # Perform some sanity checks on matches first
        for match in matches:
            if not isinstance(match.get('quality', 0), int):
                match['quality'] = int(match['quality'])
            if 'tmsource' not in match or match['tmsource'] is None:
                match['tmsource'] = tmmodel.display_name
            match['query_str'] = query_str

        curr_targets = [m['target'] for m in self.matches]
        anything_new = False
        for match in matches:
            if match['target'] not in curr_targets:
                # Let's insert at the end to prioritise existing matches over
                # new ones. We rely on the guarantee of sort stability. This
                # way an existing 100% will be above a new 100%.
                self.matches.append(match)
                anything_new = True
            else:
                prevmatch = [m for m in self.matches if m['target'] == match['target']][0]
                if 'quality' not in prevmatch or not prevmatch['quality']:
                    self.matches.remove(prevmatch)
                    self.matches.append(match)
                    anything_new = True
        if not anything_new:
            return
        self.matches.sort(key=lambda x: 'quality' in x and x['quality'] or 0, reverse=True)
        self.matches = self.matches[:self.max_matches]

        # Only call display_matches if necessary:
        if self.matches:
            self.view.display_matches(self.matches)

    def destroy(self):
        # Destroy TMView
        self.view.hide()
        self.view.destroy()

        # Disconnect signals
        self.main_controller.store_controller.disconnect(self._store_loaded_id)
        if getattr(self, '_cursor_changed_id', None):
            self.main_controller.store_controller.cursor.disconnect(self._cursor_changed_id)
        if getattr(self, '_mode_selected_id', None):
            self.main_controller.mode_controller.disconnect(self._mode_selected_id)
        if getattr(self, '_target_focused_id', None):
            self.main_controller.unit_controller.view.disconnect(self._target_focused_id)

        self.plugin_controller.shutdown()

    def select_match(self, match_data):
        """Handle a match-selection event.
            (This method is used as View-Controller communications)"""
        unit_controller = self.main_controller.unit_controller
        target_n = unit_controller.view.focused_target_n
        old_text = unit_controller.view.get_target_n(target_n)
        textbox =  unit_controller.view.targets[target_n]
        self.main_controller.undo_controller.push_current_text(textbox)
        unit_controller.set_unit_target(target_n, forceunicode(match_data['target']))

    def send_tm_query(self, unit=None):
        """Send a new query to the TM engine.
            (This method is used as Controller-Model communications)"""
        if unit is not None:
            self.unit = unit

        self.current_query = self.unit.source
        self.matches = []
        self.view.clear()
        self.emit('start-query', self.current_query)

    def start_query(self):
        """Start a TM query after C{self.QUERY_DELAY} milliseconds."""
        if not hasattr(self, 'storecursor'):
            return False

        if not hasattr(self, 'unit'):
            self.unit = self.storecursor.deref()

        self.unit_view = self.main_controller.unit_controller.view
        if getattr(self, '_target_focused_id', None) and getattr(self, 'unit_view', None):
            self.unit_view.disconnect(self._target_focused_id)
        self._target_focused_id = self.unit_view.connect('target-focused', self._on_target_focused)
        self.view.hide()

        def start_query():
            self.send_tm_query()
            return False
        if getattr(self, '_delay_id', 0):
            gobject.source_remove(self._delay_id)
        self._delay_id = gobject.timeout_add(self.QUERY_DELAY, start_query)


    # EVENT HANDLERS #
    def _on_cursor_changed(self, cursor):
        self.storecursor = cursor
        self.unit = cursor.deref()

        if self.view.active and self.unit.istranslated():
            self.view.mnu_suggestions.set_active(False)
        elif not self.view.active and not self.unit.istranslated():
            self.view.mnu_suggestions.set_active(True)

        return self.start_query()

    def _on_mode_selected(self, modecontroller, mode):
        self.view.update_geometry()

    def _on_store_loaded(self, storecontroller):
        """Disconnect from the previous store's cursor and connect to the new one."""
        if getattr(self, '_cursor_changed_id', None):
            self.storecursor.disconnect(self._cursor_changed_id)
        self.storecursor = storecontroller.cursor
        self._cursor_changed_id = self.storecursor.connect('cursor-changed', self._on_cursor_changed)

        def handle_first_unit():
            self._on_cursor_changed(self.storecursor)
            return False
        gobject.idle_add(handle_first_unit)

    def _on_target_focused(self, unitcontroller, target_n):
        #logging.debug('target_n: %d' % (target_n))
        self.view.update_geometry()
