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

import gtk
import gobject
import pango


def label_escape(text):
    escapes = [("\n", '\\n'), ("\r", '\\r')]
    return reduce(lambda text, escape: text.replace(*escape), escapes, text)


class LabelExpander(gtk.EventBox):
    __gproperties__ = {
        "expanded": (gobject.TYPE_BOOLEAN,
                     "expanded",
                     "A boolean indicating whether this widget has been expanded to show its contained widget",
                     False,
                     gobject.PARAM_READWRITE),
    }

    def __init__(self, widget, get_text, expanded=False):
        super(LabelExpander, self).__init__()

        label_text = gtk.Label()
        label_text.set_single_line_mode(True)
        label_text.set_ellipsize(pango.ELLIPSIZE_END)
        label_text.set_justify(gtk.JUSTIFY_LEFT)
        label_text.set_use_markup(True)

        self.label = gtk.EventBox()
        self.label.add(label_text)

        self.widget = widget
        self.get_text = get_text

        self.expanded = expanded

        #self.label.connect('button-release-event', lambda widget, *args: setattr(self, 'expanded', True))

    def do_get_property(self, prop):
        return getattr(self, prop.name)

    def do_set_property(self, prop, value):
        setattr(self, prop.name, value)

    def _get_expanded(self):
        return self.child == self.widget

    def _set_expanded(self, value):
        if self.child != None:
            self.remove(self.child)

        if value:
            self.add(self.widget)
        else:
            self.add(self.label)
            self.label.child.set_text(label_escape(self.get_text()))

        self.child.show()

    expanded = property(_get_expanded, _set_expanded)
