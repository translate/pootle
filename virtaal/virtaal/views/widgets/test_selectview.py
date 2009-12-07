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

from selectview import SelectView


class SelectViewTestWindow(gtk.Window):
    def __init__(self):
        super(SelectViewTestWindow, self).__init__()
        self.connect('destroy', lambda *args: gtk.main_quit())
        self.add(self.create_selectview())

    def create_selectview(self):
        self.items = (
            {'enabled': True,  'name': 'item1', 'desc': 'desc1'},
            {'enabled': False, 'name': 'item2'                 },
            {'enabled': True,                   'desc': 'desc3'},
            {                  'name': 'item4', 'desc': 'desc4'},
            {'enabled': True,  'name': 'item5', 'desc': ''     },
            {'enabled': False, 'name': '',      'desc': 'desc6'},
        )
        self.selectview = SelectView(self.items)
        self.selectview.connect('item-enabled', self._on_item_action, 'enabled')
        self.selectview.connect('item-disabled', self._on_item_action, 'disabled')
        self.selectview.connect('item-selected', self._on_item_action, 'selected')
        return self.selectview


    def _on_item_action(self, sender, item_info, action):
        print 'Item %s: %s' % (action, item_info)


if __name__ == '__main__':
    win = SelectViewTestWindow()
    win.show_all()
    gtk.main()
