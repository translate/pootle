#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2007 Osmo Salomaa
# Copyright (C) 2007-2008 Zuza Software Foundation
#
# This file was part of Gaupol.
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


"""Cell renderer for multiline text data."""

import gobject
import gtk
import pango

import pan_app
import rendering
import markup
import undo_buffer
import unit_editor


def undo(tree_view):
    undo_buffer.undo(tree_view.get_buffer().__undo_stack)


class UnitRenderer(gtk.GenericCellRenderer):
    """Cell renderer for multiline text data."""

    __gtype_name__ = "UnitRenderer"

    __gproperties__ = {
        "unit":     (gobject.TYPE_PYOBJECT,
                    "The unit",
                    "The unit that this renderer is currently handling",
                    gobject.PARAM_READWRITE),
        "editable": (gobject.TYPE_BOOLEAN,
                    "editable",
                    "A boolean indicating whether this unit is currently editable",
                    False,
                    gobject.PARAM_READWRITE),
    }

    __gsignals__ = {
        "editing-done":  (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE,
                         (gobject.TYPE_STRING, gobject.TYPE_BOOLEAN, gobject.TYPE_BOOLEAN)),
        "modified":      (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ())
    }

    ROW_PADDING = 10
    """The number of pixels between rows."""

    def __init__(self, parent):
        gtk.GenericCellRenderer.__init__(self)
        self.set_property('mode', gtk.CELL_RENDERER_MODE_EDITABLE)
        self.parent = parent
        self.__unit = None
        self.editable = False
        self._editor = None
        self.source_layout = None
        self.target_layout = None

    def _get_unit(self):
        return self.__unit

    def _set_unit(self, value):
        if value.isfuzzy():
            self.props.cell_background = "gray"
            self.props.cell_background_set = True
        else:
            self.props.cell_background_set = False
        self.__unit = value

    unit = property(_get_unit, _set_unit, None, None)

    def do_set_property(self, pspec, value):
        setattr(self, pspec.name, value)

    def do_get_property(self, pspec):
        return getattr(self, pspec.name)

    def on_render(self, window, widget, _background_area, cell_area, _expose_area, _flags):
        if self.editable:
            return True
        x_offset, y_offset, width, _height = self.do_get_size(widget, cell_area)
        x = cell_area.x + x_offset
        y = cell_area.y + y_offset
        source_x = x
        target_x = x
        if widget.get_direction() == gtk.TEXT_DIR_LTR:
            target_x += width/2
        else:
            source_x += width/2
        widget.get_style().paint_layout(window, gtk.STATE_NORMAL, False,
                cell_area, widget, '', source_x, y, self.source_layout)
        widget.get_style().paint_layout(window, gtk.STATE_NORMAL, False,
                cell_area, widget, '', target_x, y, self.target_layout)

    def _get_pango_layout(self, widget, text, width, font_description):
        '''Gets the Pango layout used in the cell in a TreeView widget.'''
        # We can't use widget.get_pango_context() because we'll end up
        # overwriting the language and font settings if we don't have a
        # new one
        layout = pango.Layout(widget.create_pango_context())
        layout.set_font_description(font_description)
        layout.set_wrap(pango.WRAP_WORD_CHAR)
        layout.set_width(width * pango.SCALE)
        #XXX - plurals?
        text = text or ""
        layout.set_markup(markup.markuptext(text))
        return layout

    def compute_cell_height(self, widget, width):
        self.source_layout = self._get_pango_layout(widget, self.unit.source, width / 2,
                rendering.get_source_font_description())
        self.source_layout.get_context().set_language(rendering.get_source_language())
        self.target_layout = self._get_pango_layout(widget, self.unit.target, width / 2,
                rendering.get_target_font_description())
        self.target_layout.get_context().set_language(rendering.get_target_language())
        # This makes no sense, but has the desired effect to align things correctly for
        # both LTR and RTL languages:
        if widget.get_direction() == gtk.TEXT_DIR_RTL:
            self.source_layout.set_alignment(pango.ALIGN_RIGHT)
            self.target_layout.set_alignment(pango.ALIGN_RIGHT)
        _layout_width, source_height = self.source_layout.get_pixel_size()
        _layout_width, target_height = self.target_layout.get_pixel_size()
        return max(source_height, target_height) + self.ROW_PADDING

    def do_get_size(self, widget, _cell_area):
        #TODO: store last unitid and computed dimensions
        width = widget.get_toplevel().get_allocation().width - 32
        if self.editable:
            editor = self.get_editor(widget)
            editor.set_size_request(width, -1)
            unit_editor.compute_optimal_height(editor, width)
            _width, height = editor.size_request()
        else:
            height = self.compute_cell_height(widget, width)
        height = min(height, 600)
        y_offset = self.ROW_PADDING / 2
        return 0, y_offset, width, height

    def _on_editor_done(self, editor):
        self.emit("editing-done", editor.get_data("path"), editor.must_advance, editor.get_modified())
        return True

    def _on_modified(self, widget):
        self.emit("modified")

    def get_editor(self, parent):
        if not hasattr(self.unit, '__editor'):
            editor = unit_editor.UnitEditor(parent, self.unit)
            editor.connect("editing-done", self._on_editor_done)
            editor.connect("modified", self._on_modified)
            editor.set_border_width(min(self.props.xpad, self.props.ypad))
            editor.show_all()
            setattr(self.unit, '__editor', editor)
        return getattr(self.unit, '__editor')

    def do_start_editing(self, _event, tree_view, path, _bg_area, cell_area, _flags):
        """Initialize and return the editor widget."""
        editor = self.get_editor(tree_view)
        editor.set_size_request(cell_area.width, cell_area.height)
        return editor
