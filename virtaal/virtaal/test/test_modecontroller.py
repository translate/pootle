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

from test_scaffolding import TestScaffolding


class TestModeController(TestScaffolding):
    def test_get_mode_by_display_name(self):
        default_mode_display_name = self.mode_controller.modenames['Default']
        default_mode = self.mode_controller.get_mode_by_display_name(default_mode_display_name)
        assert default_mode == self.mode_controller.modes[self.mode_controller.default_mode_name]

    def test_select_mode(self):
        for name, mode in self.mode_controller.modes.items():
            self.mode_controller.select_mode(mode)
            assert self.mode_controller.current_mode is mode

    def test_select_mode(self):
        for name, mode in self.mode_controller.modes.items():
            self.mode_controller.select_mode_by_name(name)
            assert self.mode_controller.current_mode is mode
