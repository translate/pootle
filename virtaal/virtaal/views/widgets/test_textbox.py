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

from textbox import TextBox


class TextWindow(gtk.Window):
    def __init__(self, textbox=None):
        super(TextWindow, self).__init__()
        if textbox is None:
            textbox = TextBox()

        self.vbox = gtk.VBox()
        self.add(self.vbox)

        self.textbox = textbox
        self.vbox.add(textbox)

        self.connect('destroy', lambda *args: gtk.main_quit())
        self.set_size_request(600, 100)


class TestTextBox(object):
    def __init__(self):
        self.window = TextWindow()


if __name__ == '__main__':
    window = TextWindow()
    window.show_all()
    window.textbox.set_text(u'Ģët <a href="http://www.example.com" alt="Ģët &brand;!">&brandLong;</a>')
    gtk.main()
