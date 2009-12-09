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
import pango
from gobject import idle_add, PARAM_READWRITE, SIGNAL_RUN_FIRST, TYPE_PYOBJECT


def flagstr(flags):
    """Create a string-representation for the given flags structure."""
    fset = []
    for f in dir(gtk):
        if not f.startswith('CELL_RENDERER_'):
            continue
        if flags & getattr(gtk, f):
            fset.append(f)
    return '|'.join(fset)


class CellRendererWidget(gtk.GenericCellRenderer):
    __gtype_name__ = 'CellRendererWidget'
    __gproperties__ = {
        'widget': (TYPE_PYOBJECT, 'Widget', 'The column containing the widget to render', PARAM_READWRITE),
    }

    XPAD = 2
    YPAD = 2


    # INITIALIZERS #
    def __init__(self, strfunc, default_width=-1):
        gtk.GenericCellRenderer.__init__(self)

        self.default_width = default_width
        self._editing = False
        self.editablemap = {}
        self.strfunc = strfunc
        self.widget = None


    # INTERFACE METHODS #
    def do_set_property(self, pspec, value):
        setattr(self, pspec.name, value)

    def do_get_property(self, pspec):
        return getattr(self, pspec.name)

    def on_get_size(self, widget, cell_area=None):
        #print '%s>> on_get_size()' % (self.strfunc(self.widget))
        # FIXME: This method works fine for unselected cells (rows) and gives the same (wrong) results for selected cells.
        height = width = 0

        if cell_area is not None:
            return self.XPAD, self.YPAD, cell_area.width - 2*self.XPAD, cell_area.height - 2*self.YPAD

        width = widget.get_allocation().width
        if width <= 1:
            width = self.default_width
        layout = self.create_pango_layout(self.strfunc(self.widget), widget, width)
        width, height = layout.get_pixel_size()

        if self.widget:
            w, h = self.widget.size_request()
            width =  max(width,  w)
            height = max(height, h)

        #print 'width %d | height %d | lw %d | lh %d' % (width, height, lw, lh)
        height += self.YPAD * 2
        width  += self.XPAD * 2

        return self.XPAD, self.YPAD, width, height

    def on_render(self, window, widget, bg_area, cell_area, expose_area, flags):
        #print '%s>> on_render(flags=%s)' % (self.strfunc(self.widget), flagstr(flags))
        if flags & gtk.CELL_RENDERER_SELECTED:
            self.props.mode = gtk.CELL_RENDERER_MODE_EDITABLE
            self._start_editing(widget) # FIXME: This is obviously a hack, but what more do you want?
            return True
        self.props.mode = gtk.CELL_RENDERER_MODE_INERT
        xo, yo, w, h = self.get_size(widget, cell_area)
        x = cell_area.x + xo
        layout = self.create_pango_layout(self.strfunc(self.widget), widget, w)
        layout_w, layout_h = layout.get_pixel_size()
        y = cell_area.y + yo + (h-layout_h)/2
        widget.get_style().paint_layout(window, gtk.STATE_NORMAL, True, cell_area, widget, '', x, y, layout)

    def on_start_editing(self, event, tree_view, path, bg_area, cell_area, flags):
        #print '%s>> on_start_editing(flags=%s, event=%s)' % (self.strfunc(self.widget), flagstr(flags), event)
        if self.widget not in self.editablemap:
            editable = CellWidget(self.widget)
            self.editablemap[self.widget] = editable
        editable = self.editablemap[self.widget]
        editable.show_all()
        editable.grab_focus()
        return editable

    # METHODS #
    def create_pango_layout(self, string, widget, width):
        font = widget.get_pango_context().get_font_description()
        layout = pango.Layout(widget.get_pango_context())
        layout.set_font_description(font)
        layout.set_wrap(pango.WRAP_WORD_CHAR)
        layout.set_width(width * pango.SCALE)
        layout.set_markup(string)
        # This makes no sense, but mostly has the desired effect to align things correctly for
        # RTL languages which is otherwise incorrect. Untranslated entries is still wrong.
        if widget.get_direction() == gtk.TEXT_DIR_RTL:
            layout.set_alignment(pango.ALIGN_RIGHT)
            layout.set_auto_dir(False)
        return layout

    def _start_editing(self, treeview):
        """Force the cell to enter editing mode by going through the parent
            gtk.TextView."""
        if self._editing:
            return
        self._editing = True

        model, iter = treeview.get_selection().get_selected()
        path = model.get_path(iter)
        col = [c for c in treeview.get_columns() if self in c.get_cell_renderers()]
        if len(col) < 1:
            self._editing = False
            return
        treeview.set_cursor_on_cell(path, col[0], self, True)
        # XXX: Hack to make sure that the lock (_start_editing) is not released before the next on_render() is called.
        def update_lock():
            self._editing = False
        idle_add(update_lock)


class CellWidget(gtk.HBox, gtk.CellEditable):
    __gtype_name__ = 'CellWidget'
    __gsignals__ = {
        'modified': (SIGNAL_RUN_FIRST, None, ())
    }

    # INITIALIZERS #
    def __init__(self, *widgets):
        super(CellWidget, self).__init__()
        for w in widgets:
            if w.parent is not None:
                w.parent.remove(w)
            self.pack_start(w)


    # INTERFACE METHODS #
    def do_editing_done(self, *args):
        pass

    def do_remove_widget(self, *args):
        pass

    def do_start_editing(self, *args):
        pass


if __name__ == "__main__":
    class Tree(gtk.TreeView):
        def __init__(self):
            self.store = gtk.ListStore(str, TYPE_PYOBJECT, bool)
            gtk.TreeView.__init__(self)
            self.set_model(self.store)
            self.set_headers_visible(True)

            self.append_column(gtk.TreeViewColumn('First', gtk.CellRendererText(), text=0))
            self.append_column(gtk.TreeViewColumn('Second', CellRendererWidget(lambda widget: '<b>' + widget.get_children()[0].get_label() + '</b>'), widget=1))

        def insert(self, name):
            iter = self.store.append()
            hb = gtk.HBox()
            hb.pack_start(gtk.Button(name))
            lbl = gtk.Label((name + ' ') * 20)
            lbl.set_line_wrap(True)
            hb.pack_start(lbl, expand=False)
            self.store.set(iter, 0, name, 1, hb, 2, True)

    w = gtk.Window()
    w.set_position(gtk.WIN_POS_CENTER)
    w.connect('delete-event', gtk.main_quit)
    t = Tree()
    t.insert('foo')
    t.insert('bar')
    t.insert('baz')
    w.add(t)

    w.show_all()
    gtk.main()
