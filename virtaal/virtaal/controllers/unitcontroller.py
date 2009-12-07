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

from gobject import GObject, SIGNAL_RUN_FIRST, TYPE_PYOBJECT

from virtaal.common import GObjectWrapper
from virtaal.views import UnitView

from basecontroller import BaseController


class UnitController(BaseController):
    """Controller for unit-based operations."""

    __gtype_name__ = "UnitController"
    __gsignals__ = {
        'unit-done':           (SIGNAL_RUN_FIRST, None, (TYPE_PYOBJECT, int)),
        'unit-modified':       (SIGNAL_RUN_FIRST, None, (TYPE_PYOBJECT,)),
        'unit-delete-text':    (SIGNAL_RUN_FIRST, None, (TYPE_PYOBJECT, TYPE_PYOBJECT, TYPE_PYOBJECT, int, int, TYPE_PYOBJECT, int)),
        'unit-insert-text':    (SIGNAL_RUN_FIRST, None, (TYPE_PYOBJECT, TYPE_PYOBJECT, int, TYPE_PYOBJECT, int)),
        'unit-paste-start':    (SIGNAL_RUN_FIRST, None, (TYPE_PYOBJECT, TYPE_PYOBJECT, TYPE_PYOBJECT, int)),
    }

    # INITIALIZERS #
    def __init__(self, store_controller):
        GObjectWrapper.__init__(self)

        self.current_unit = None
        self.main_controller = store_controller.main_controller
        self.main_controller.unit_controller = self
        self.store_controller = store_controller
        self.store_controller.unit_controller = self
        self.placeables_controller = None

        self.view = UnitView(self)
        self.view.connect('delete-text', self._unit_delete_text)
        self.view.connect('insert-text', self._unit_insert_text)
        self.view.connect('paste-start', self._unit_paste_start)
        self.view.connect('modified', self._unit_modified)
        self.view.connect('unit-done', self._unit_done)
        self.view.enable_signals()

        self.store_controller.connect('store-loaded', self._on_store_loaded)
        self.main_controller.connect('controller-registered', self._on_controller_registered)

        self._current_unit_modified = False


    # ACCESSORS #
    def get_unit_target(self, target_index):
        return self.view.get_target_n(target_index)

    def set_unit_target(self, target_index, value, cursor_pos=-1):
        self.view.set_target_n(target_index, value, cursor_pos)


    # METHODS #
    def load_unit(self, unit):
        if self.current_unit and self.current_unit is unit:
            return self.view
        self.current_unit = unit
        self.nplurals = self.main_controller.lang_controller.target_lang.nplurals

        if self.placeables_controller:
            self.current_unit.rich_source = self.placeables_controller.apply_parsers(self.current_unit.rich_source)

        self.view.load_unit(unit)
        return self.view

    def _unit_delete_text(self, unitview, deleted, parent, offset, cursor_pos, elem, target_num):
        self.emit('unit-delete-text', self.current_unit, deleted, parent, offset, cursor_pos, elem, target_num)

    def _unit_insert_text(self, unitview, ins_text, offset, elem, target_num):
        self.emit('unit-insert-text', self.current_unit, ins_text, offset, elem, target_num)

    def _unit_paste_start(self, unitview, old_text, offsets, target_num):
        self.emit('unit-paste-start', self.current_unit, old_text, offsets, target_num)

    def _unit_modified(self, *args):
        self.emit('unit-modified', self.current_unit)
        self._current_unit_modified = True

    def _unit_done(self, widget, unit):
        self.emit('unit-done', unit, self._current_unit_modified)
        self._current_unit_modified = False


    # EVENT HANDLERS #
    def _on_controller_registered(self, main_controller, controller):
        if controller is main_controller.lang_controller:
            self.main_controller.lang_controller.connect('source-lang-changed', self._on_language_changed)
            self.main_controller.lang_controller.connect('target-lang-changed', self._on_language_changed)
        elif controller is main_controller.placeables_controller:
            self.placeables_controller = main_controller.placeables_controller
            self.placeables_controller.connect('parsers-changed', self._on_parsers_changed)
            self._on_parsers_changed(self.placeables_controller)

    def _on_language_changed(self, lang_controller, langcode):
        self.nplurals = lang_controller.target_lang.nplurals
        if hasattr(self, 'view'):
            self.view.update_languages()

    def _on_parsers_changed(self, placeables_controller):
        if self.current_unit:
            self.current_unit.rich_source = placeables_controller.apply_parsers(self.current_unit.rich_source)

    def _on_store_loaded(self, store_controller):
        """Call C{_on_language_changed()}.

            If the target language loaded at start-up (from config) is the same
            as that of the first opened file, C{self.view.update_languages()} is
            not called, because the L{LangController}'s C{"target-lang-changed"}
            signal is never emitted, because the language has not really
            changed.

            This event handler ensures that it is loaded. As a side-effect,
            C{self.view.update_languages()} is called twice if language before
            and after a store load is different. But we'll just have to live
            with that."""
        self._on_language_changed(
            self.main_controller.lang_controller,
            self.main_controller.lang_controller.target_lang.code
        )
