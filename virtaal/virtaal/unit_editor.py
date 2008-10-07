#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2007-2008 Zuza Software Foundation
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
import pango
import gtk

from translate.misc.multistring import multistring
from translate.lang import factory

import pan_app
import markup
import undo_buffer
import unit_layout
import widgets.label_expander as label_expander
from support.simplegeneric import generic


@generic
def compute_optimal_height(widget, width):
    raise NotImplementedError()

@compute_optimal_height.when_type(gtk.Widget)
def gtk_widget_compute_optimal_height(widget, width):
    pass

@compute_optimal_height.when_type(gtk.Container)
def gtk_container_compute_optimal_height(widget, width):
    for child in widget.get_children():
        compute_optimal_height(child, width)

@compute_optimal_height.when_type(gtk.Table)
def gtk_table_compute_optimal_height(widget, width):
    for child in widget.get_children():
        # width / 2 because we use half of the available width
        compute_optimal_height(child, width / 2)

def make_pango_layout(widget, text, width):
    pango_layout = pango.Layout(widget.get_pango_context())
    pango_layout.set_width(width * pango.SCALE)
    pango_layout.set_wrap(pango.WRAP_WORD_CHAR)
    pango_layout.set_text(text or "")
    return pango_layout

@compute_optimal_height.when_type(gtk.TextView)
def gtk_textview_compute_optimal_height(widget, width):
    buf = widget.get_buffer()
    # For border calculations, see gtktextview.c:gtk_text_view_size_request in the GTK source
    border = 2 * widget.border_width - 2 * widget.parent.border_width
    if widget.style_get_property("interior-focus"):
        border += 2 * widget.style_get_property("focus-line-width")

    buftext = buf.get_text(buf.get_start_iter(), buf.get_end_iter())
    if not buftext:
        buftext = getattr(widget, '_source_text', "")

    _w, h = make_pango_layout(widget, buftext, width - border).get_pixel_size()
    widget.parent.set_size_request(-1, h + border)

@compute_optimal_height.when_type(label_expander.LabelExpander)
def gtk_labelexpander_compute_optimal_height(widget, width):
    if widget.label.child.get_text().strip() == "":
        widget.set_size_request(-1, 0)
    else:
        _w, h = make_pango_layout(widget, widget.label.child.get_label()[0], width).get_pixel_size()
        widget.set_size_request(-1, h + 4)


class UnitEditor(gtk.EventBox, gtk.CellEditable):
    """Text view suitable for cell renderer use."""

    __gtype_name__ = "UnitEditor"

    __gsignals__ = {
        'modified':(gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ())
    }

    def __init__(self, parent, unit):
        gtk.EventBox.__init__(self)
        self._document = parent.document
        self.layout = unit_layout.build_layout(unit, self._document.nplurals)
        self.add(self.layout)
        self.sources = [src for src in unit_layout.get_sources(self.layout)]
        self.targets = []
        for target in unit_layout.get_targets(self.layout):
            target.connect('key-press-event', self._on_text_view_key_press_event)
            target.get_buffer().connect("changed", self._on_modify)
            self.targets.append(target)
        for option in unit_layout.get_options(self.layout):
            option.connect("toggled", self._on_modify)
        self.must_advance = False
        self._modified = False
        self._unit = unit
        self.connect('key-press-event', self._on_key_press_event)

    def _on_modify(self, _buf):
        self.emit('modified')

    def _on_key_press_event(self, _widget, event, *_args):
        if event.keyval == gtk.keysyms.Return or event.keyval == gtk.keysyms.KP_Enter:
            self.must_advance = True
            self.editing_done()
            return True
        return False

    def _on_text_view_key_press_event(self, widget, event, *_args):
        # Alt-Down
        if event.keyval == gtk.keysyms.Down and event.state & gtk.gdk.MOD1_MASK:
            gobject.idle_add(self.copy_original, widget)
            return True
        return False

    def do_start_editing(self, *_args):
        """Start editing."""
        unit_layout.focus_text_view(unit_layout.get_targets(self)[0])

    def get_modified(self):
        return self._modified

    def get_text(self):
        targets = [b.props.text for b in self.buffers]
        if len(targets) == 1:
            return targets[0]
        else:
            return multistring(targets)

    def copy_original(self, text_view):
        buf = text_view.get_buffer()
        position = buf.props.cursor_position
        lang = factory.getlanguage(self._document.get_target_language())
        new_source = lang.punctranslate(self._unit.source)
        # if punctranslate actually changed something, let's insert that as an
        # undo step
        if new_source != self._unit.source:
            buf.set_text(markup.escape(self._unit.source))
            # TODO: consider a better position to return to on undo
            undo_buffer.merge_actions(buf, position)
        buf.set_text(markup.escape(new_source))
        undo_buffer.merge_actions(buf, position)
        unit_layout.focus_text_view(text_view)
        return False
