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
from gobject import SIGNAL_RUN_FIRST, TYPE_PYOBJECT

from virtaal.common import GObjectWrapper

from selectview import SelectView


class SelectDialog(GObjectWrapper):
    """
    A dialog wrapper to easily select items from a list.
    """

    __gtype_name__ = 'SelectDialog'
    __gsignals__ = {
        'item-enabled':   (SIGNAL_RUN_FIRST, None, (TYPE_PYOBJECT,)),
        'item-disabled':  (SIGNAL_RUN_FIRST, None, (TYPE_PYOBJECT,)),
        'item-selected':  (SIGNAL_RUN_FIRST, None, (TYPE_PYOBJECT,)),
        'selection-done': (SIGNAL_RUN_FIRST, None, (TYPE_PYOBJECT,)),
    }

    # INITIALIZERS #
    def __init__(self, items=None, title=None, message=None, parent=None, size=None):
        super(SelectDialog, self).__init__()
        self.sview = SelectView(items)
        self._create_gui(title, message, parent)
        self._connect_signals()

        if size and len(size) == 2:
            w, h = -1, -1
            if size[0] > 0:
                w = size[0]
            if size[1] > 0:
                h = size[1]
            self.dialog.set_size_request(w, h)

    def _connect_signals(self):
        self.sview.connect('item-enabled',  self._on_item_enabled)
        self.sview.connect('item-disabled', self._on_item_disabled)
        self.sview.connect('item-selected', self._on_item_selected)

    def _create_gui(self, title, message, parent):
        self.dialog = gtk.Dialog()
        self.dialog.set_modal(True)
        if isinstance(parent, gtk.Widget):
            self.dialog.set_parent(parent)
        self.dialog.set_title(title is not None and title or 'Select items')
        self.message = gtk.Label(message is not None and message or '')
        self.dialog.child.add(self.message)
        self.dialog.child.add(self.sview)
        self.dialog.add_buttons(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)


    # METHODS #
    def get_message(self):
        return self.message.get_text()

    def set_icon(self, icon):
        """Simple proxy method to C{self.dialog.set_icon(icon)}."""
        self.dialog.set_icon(icon)

    def set_message(self, msg):
        self.message.set_text(msg)

    def set_transient_for(self, parent):
        """Simple proxy method to C{self.dialog.set_transient_for(parent)}."""
        self.dialog.set_transient_for(parent)

    def run(self, items=None, parent=None):
        if items is not None:
            self.sview.set_model(items)
        if isinstance(parent, gtk.Widget):
            self.dialog.reparent(parent)
        self.dialog.show_all()
        self.response = self.dialog.run()
        self.dialog.hide()
        self.emit('selection-done', self.sview.get_all_items())
        return self.response


    # EVENT HANDLERS #
    def _on_item_enabled(self, selectview, item):
        self.emit('item-enabled', item)

    def _on_item_disabled(self, selectview, item):
        self.emit('item-disabled', item)

    def _on_item_selected(self, selectview, item):
        self.emit('item-selected', item)
