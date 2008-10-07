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

"""This provides a simple dialog with a text entry field."""

import gtk


def EntryDialog(title):
    dlg = gtk.Dialog(title)
    dlg.set_size_request(450, 100)
    dlg.show()

    entry = gtk.Entry()
    entry.show()
    entry.set_activates_default(True)
    dlg.vbox.pack_start(entry)

    dlg.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
    dlg.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
    dlg.set_default_response(gtk.RESPONSE_OK)
    entry.grab_focus()
    response = dlg.run()

    text = None
    if response == gtk.RESPONSE_OK:
        text = entry.get_text().decode('utf-8')
    dlg.destroy()
    return text
