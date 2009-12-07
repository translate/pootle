#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2009 Zuza Software Foundation
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

from virtaal.common import GObjectWrapper, pan_app
from virtaal.views import PreferencesView

from basecontroller import BaseController


class PreferencesController(BaseController):
    """Controller for driving the preferences GUI."""

    __gtype_name__ = 'PreferencesController'

    # INITIALIZERS #
    def __init__(self, main_controller):
        GObjectWrapper.__init__(self)

        self.main_controller = main_controller
        self.placeables_controller = main_controller.placeables_controller
        self.plugin_controller = main_controller.plugin_controller
        self.view = PreferencesView(self)
        self.view.connect('prefs-done', self._on_prefs_done)


    # METHODS #
    def set_placeable_enabled(self, parser, enabled):
        """Enable or disable a placeable with the given parser function."""
        if enabled:
            self.placeables_controller.add_parsers(parser)
        else:
            self.placeables_controller.remove_parsers(parser)
        self.update_config_placeables_state(parser=parser, disabled=not enabled)

    def set_plugin_enabled(self, plugin_name, enabled):
        """Enabled or disable a plug-in with the given name."""
        if enabled:
            self.plugin_controller.enable_plugin(plugin_name)
        else:
            self.plugin_controller.disable_plugin(plugin_name)
        self.update_config_plugin_state(plugin_name=plugin_name, disabled=not enabled)

    def update_config_placeables_state(self, parser, disabled):
        """Make sure that the placeable with the given name is enabled/disabled
            in the main configuration file."""
        classname = parser.im_self.__name__
        pan_app.settings.placeable_state[classname.lower()] = disabled and 'disabled' or 'enabled'

    def update_config_plugin_state(self, plugin_name, disabled):
        """Make sure that the plug-in with the given name is enabled/disabled
            in the main configuration file."""
        # A plug-in is considered "enabled" as long as
        # pan_app.settings.plugin_state[plugin_name].lower() != 'disabled',
        # even if not pan_app.settings.plugin_state.has_key(plugin_name).
        # This method is put here in stead of in PluginController, because it
        # is not safe to assume that the plug-ins being managed my any given
        # PluginController instance is enabled/disabled via the main virtaal.ini's
        # "[plugin_state]" section.
        pan_app.settings.plugin_state[plugin_name] = disabled and 'disabled' or 'enabled'

    def update_prefs_gui_data(self):
        self._update_font_gui_data()
        self._update_placeables_gui_data()
        self._update_plugin_gui_data()
        self._update_user_gui_data()

    def _update_font_gui_data(self):
        self.view.font_data = {
            'source': pan_app.settings.language['sourcefont'],
            'target': pan_app.settings.language['targetfont'],
        }

    def _update_placeables_gui_data(self):
        items = []
        allparsers = self.placeables_controller.parser_info.items()
        allparsers.sort(key=lambda x: x[1][0])
        for parser, (name, desc) in allparsers:
            items.append({
                'name': name,
                'desc': desc,
                'enabled': parser in self.placeables_controller.parsers,
                'data': parser
            })
        self.view.placeables_data = items

    def _update_plugin_gui_data(self):
        plugin_items = []
        for found_plugin in self.plugin_controller._find_plugin_names():
            if found_plugin in self.plugin_controller.plugins:
                plugin = self.plugin_controller.plugins[found_plugin]
                plugin_items.append({
                    'name': plugin.display_name,
                    'desc': plugin.description,
                    'enabled': True,
                    'data': {'internal_name': found_plugin},
                    'config': plugin.configure_func
                })
            else:
                try:
                    info = self.plugin_controller.get_plugin_info(found_plugin)
                except Exception, e:
                    logging.debug('Problem getting information for plugin %s' % found_plugin)
                    continue

                plugin_items.append({
                    'name': info['display_name'],
                    'desc': info['description'],
                    'enabled': False,
                    'data': {'internal_name': found_plugin},
                    'config': None
                })
        # XXX: Note that we ignore plugin_controller.get_disabled_plugins(),
        # because we need to know which plug-ins are currently enabled/disabled
        # (not dependant on config).

        self.view.plugin_data = plugin_items

    def _update_user_gui_data(self):
        self.view.user_data = {
            'name':  pan_app.settings.translator['name'],
            'email': pan_app.settings.translator['email'],
            'team':  pan_app.settings.translator['team'],
        }


    # EVENT HANDLERS #
    def _on_prefs_done(self, view):
        # Update pan_app.settings with data from view
        font_data = view.font_data
        pan_app.settings.language['sourcefont'] = font_data['source']
        pan_app.settings.language['targetfont'] = font_data['target']
        # Reload unit to reload fonts
        self.main_controller.unit_controller.view.update_languages()

        user_data = view.user_data
        for key in ('name', 'email', 'team'):
            pan_app.settings.translator[key] = user_data[key]
