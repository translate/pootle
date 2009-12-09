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

from selectdialog import SelectDialog


class TestSelectDialog(object):
    """
    Test runner for SelectDialog.
    """

    def __init__(self):
        self.items = (
            {'enabled': True,  'name': 'item1', 'desc': 'desc1'},
            {'enabled': False, 'name': 'item2'                 },
            {'enabled': True,                   'desc': 'desc3'},
            {                  'name': 'item4', 'desc': 'desc4'},
            {'enabled': True,  'name': 'item5', 'desc': ''     },
            {'enabled': False, 'name': '',      'desc': 'desc6'},
        )
        self.dialog = SelectDialog(self.items, title='Test runner', message='Select the items you want:')
        self.dialog.connect('item-enabled',   self._on_dialog_action, 'Enabled')
        self.dialog.connect('item-disabled',  self._on_dialog_action, 'Disabled')
        self.dialog.connect('item-selected',  self._on_dialog_action, 'Selected')
        self.dialog.connect('selection-done', self._on_dialog_action, 'Selection done')

    def run(self):
        self.dialog.run()

    def _on_dialog_action(self, dialog, item, action):
        print '%s: %s' % (action, item)


if __name__ == '__main__':
    runner = TestSelectDialog()
    runner.run()
