#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2009 Zuza Software Foundation
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
import gtk
import logging
import pango
from gtk import gdk
from translate.lang import factory

from virtaal.support.simplegeneric import generic
from virtaal.views import markup, rendering
from virtaal.common import pan_app


@generic
def compute_optimal_height(widget, width):
    raise NotImplementedError()

@compute_optimal_height.when_type(gtk.Widget)
def gtk_widget_compute_optimal_height(widget, width):
    pass

@compute_optimal_height.when_type(gtk.Container)
def gtk_container_compute_optimal_height(widget, width):
    if not widget.props.visible:
        return
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
    if not widget.props.visible:
        return
    buf = widget.get_buffer()
    # For border calculations, see gtktextview.c:gtk_text_view_size_request in the GTK source
    border = 2 * widget.border_width - 2 * widget.parent.border_width
    if widget.style_get_property("interior-focus"):
        border += 2 * widget.style_get_property("focus-line-width")

    buftext = buf.get_text(buf.get_start_iter(), buf.get_end_iter())
    if not buftext:
        text = getattr(widget, '_source_text', "")
        if text:
            lang = factory.getlanguage(pan_app.settings.language["targetlang"])
            buftext = lang.alter_length(text)
            buftext = markup.escape(buftext)

    _w, h = make_pango_layout(widget, buftext, width - border).get_pixel_size()
    if h == 0:
        # No idea why this bug happens, but it often happens for the first unit
        # directly after the file is opened. For now we try to guess a more
        # useful default than 0. This should look much better than 0, at least.
        h = 28
    parent = widget.parent
    if isinstance(parent, gtk.ScrolledWindow) and parent.get_shadow_type() != gtk.SHADOW_NONE:
        border += 2 * parent.rc_get_style().ythickness
    widget.parent.set_size_request(-1, h + border)

@compute_optimal_height.when_type(gtk.Label)
def gtk_label_compute_optimal_height(widget, width):
    if widget.get_text().strip() == "":
        widget.set_size_request(width, 0)
    else:
        _w, h = make_pango_layout(widget, widget.get_label(), width).get_pixel_size()
        widget.set_size_request(width, h)


COLUMN_NOTE, COLUMN_UNIT, COLUMN_EDITABLE = 0, 1, 2

class StoreTreeModel(gtk.GenericTreeModel):
    """Custom C{gtk.TreeModel} adapted from the old C{UnitModel} class."""

    def __init__(self, storemodel):
        gtk.GenericTreeModel.__init__(self)
        self._store = storemodel
        self._store_len = len(storemodel)
        self._current_editable = 0

    def on_get_flags(self):
        return gtk.TREE_MODEL_ITERS_PERSIST | gtk.TREE_MODEL_LIST_ONLY

    def on_get_n_columns(self):
        return 3

    def on_get_column_type(self, index):
        if index == 0:
            return gobject.TYPE_STRING
        elif index == 1:
            return gobject.TYPE_PYOBJECT
        elif index == 2:
            return gobject.TYPE_BOOLEAN

    def on_get_iter(self, path):
        return path[0]

    def on_get_path(self, rowref):
        return (rowref,)

    def on_get_value(self, rowref, column):
        if column <= 1:
            unit = self._store[rowref]
            if column == 0:
                note_text = unit.getnotes()
                if not note_text:
                    locations = unit.getlocations()
                    if locations:
                        note_text = unit.getlocations()[0]
                return markup.markuptext(note_text, fancyspaces=False, markupescapes=False) or None
            else:
                return unit
        else:
            return self._current_editable == rowref

    def on_iter_next(self, rowref):
        if rowref < self._store_len - 1:
            return rowref + 1
        else:
            return None

    def on_iter_children(self, parent):
        if parent == None and self._store_len > 0:
            return 0
        else:
            return None

    def on_iter_has_child(self, rowref):
        return False

    def on_iter_n_children(self, rowref):
        if rowref == None:
            return self._store_len
        else:
            return 0

    def on_iter_nth_child(self, parent, n):
        if parent == None:
            return n
        else:
            return None

    def on_iter_parent(self, child):
        return None

    # Non-model-interface methods

    def set_editable(self, new_path):
        old_path = (self._current_editable,)
        self._current_editable = new_path[0]
        self.row_changed(old_path, self.get_iter(old_path))
        self.row_changed(new_path, self.get_iter(new_path))

    def store_index_to_path(self, store_index):
        return self.on_get_path(store_index)

    def path_to_store_index(self, path):
        return path[0]


class StoreTreeView(gtk.TreeView):
    """
    The extended C{gtk.TreeView} we use display our units.
    This class was adapted from the old C{UnitGrid} class.
    """

    __gsignals__ = {
        'modified':(gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ())
    }

    # INITIALIZERS #
    def __init__(self, view):
        self.view = view
        super(StoreTreeView, self).__init__()

        self.set_headers_visible(False)
        #self.set_direction(gtk.TEXT_DIR_LTR)

        self.renderer = self._make_renderer()
        self.append_column(self._make_column(self.renderer))
        self._enable_tooltips()

        self._install_callbacks()

        # This must be changed to a mutex if you ever consider
        # writing multi-threaded code. However, the motivation
        # for this horrid little variable is so dubious that you'd
        # be better off writing better code. I'm sorry to leave it
        # to you.
        self._waiting_for_row_change = 0

    def _enable_tooltips(self):
        if hasattr(self, "set_tooltip_column"):
            self.set_tooltip_column(COLUMN_NOTE)
        self.set_rules_hint(True)

    def _install_callbacks(self):
        self.connect('key-press-event', self._on_key_press)
        self.connect("cursor-changed", self._on_cursor_changed)
        self.connect("button-press-event", self._on_button_press)
        self.connect('focus-in-event', self.on_configure_event)

        # The following connections are necessary, because Gtk+ apparently *only* uses accelerators
        # to add pretty key-bindings next to menu items and does not really care if an accelerator
        # path has a connected handler.
        mainview = self.view.controller.main_controller.view
        mainview.gui.get_widget('mnu_up').connect('activate', lambda *args: self._move_up(None, None, None, None))
        mainview.gui.get_widget('mnu_down').connect('activate', lambda *args: self._move_down(None, None, None, None))
        mainview.gui.get_widget('mnu_pageup').connect('activate', lambda *args: self._move_pgup(None, None, None, None))
        mainview.gui.get_widget('mnu_pagedown').connect('activate', lambda *args: self._move_pgdown(None, None, None, None))

    def _make_renderer(self):
        renderer = StoreCellRenderer(self.view)
        renderer.connect("editing-done", self._on_cell_edited, self.get_model())
        renderer.connect("modified", self._on_modified)
        return renderer

    def _make_column(self, renderer):
        column = gtk.TreeViewColumn(None, renderer, unit=COLUMN_UNIT, editable=COLUMN_EDITABLE)
        column.set_expand(True)
        return column


    # METHODS #
    def select_index(self, index):
        """Select the row with the given index."""
        model = self.get_model()
        newpath = model.store_index_to_path(index)
        selected = self.get_selection().get_selected()
        selected_path = isinstance(selected[1], gtk.TreeIter) and model.get_path(selected[1]) or None

        if selected[1] is None or (selected_path and selected_path != newpath):
            #logging.debug('select_index()->self.set_cursor(path="%s")' % (newpath))
            self.set_cursor(newpath, self.get_columns()[0], start_editing=True)
            self._activate_editing_path(newpath)

    def set_model(self, storemodel):
        model = StoreTreeModel(storemodel)
        super(StoreTreeView, self).set_model(model)

    def _activate_editing_path(self, new_path):
        """Activates the given path for editing."""
        # get the index of the translation unit in the translation store
        #self.get_model().set(self.get_model().get_iter(new_path), COLUMN_EDITABLE, True)
        self.get_model().set_editable(new_path)
        def change_cursor():
            self.set_cursor(new_path, self.get_columns()[0], start_editing=True)
            self._waiting_for_row_change -= 1
        self._waiting_for_row_change += 1
        gobject.idle_add(change_cursor, priority=gobject.PRIORITY_DEFAULT_IDLE)

    def _keyboard_move(self, offset):
        if not self.view.controller.get_store():
            return

        # We don't want to process keyboard move events until we have finished updating
        # the display after a move event. So we use this awful, awful, terrible scheme to
        # keep track of pending draw events. In reality, it should be impossible for
        # self._waiting_for_row_change to be larger than 1, but my superstition led me
        # to be safe about it.
        if self._waiting_for_row_change > 0:
            return True

        try:
            #self._owner.set_statusbar_message(self.document.mode_cursor.move(offset))
            self.view.cursor.move(offset)
            path = self.get_model().store_index_to_path(self.view.cursor.index)
            self._activate_editing_path(path)
        except IndexError:
            pass

        return True

    def _move_up(self, _accel_group, _acceleratable, _keyval, _modifier):
        return self._keyboard_move(-1)

    def _move_down(self, _accel_group, _acceleratable, _keyval, _modifier):
        return self._keyboard_move(1)

    def _move_pgup(self, _accel_group, _acceleratable, _keyval, _modifier):
        return self._keyboard_move(-10)

    def _move_pgdown(self, _accel_group, _acceleratable, _keyval, _modifier):
        return self._keyboard_move(10)


    # EVENT HANDLERS #
    def _on_button_press(self, widget, event):
        # If the event did not happen in the treeview, but in the
        # editing widget, then the event window will not correspond to
        # the treeview's drawing window. This happens when the
        # user clicks on the edit widget. But if this happens, then
        # we don't want anything to happen, so we return True.
        if event.window != widget.get_bin_window():
            return True

        answer = self.get_path_at_pos(int(event.x), int(event.y))
        if answer is None:
            logging.debug("Not path found at (%d,%d)" % (int(event.x), int(event.y)))
            return True

        old_path, _old_column = self.get_cursor()
        path, _column, _x, _y = answer
        if old_path != path:
            index = self.get_model().path_to_store_index(path)
            if index not in self.view.cursor.indices:
                self.view.controller.main_controller.mode_controller.select_default_mode()
            self.view.cursor.index = index

        return True

    def _on_cell_edited(self, _cell, _path_string, must_advance, _modified, _model):
        if must_advance:
            return self._keyboard_move(1)
        return True

    def on_configure_event(self, widget, _event, *_user_args):
        path, column = self.get_cursor()

        self.columns_autosize()
        if path != None:
            self.set_cursor(path, column, start_editing=True)

        return False

    def _on_cursor_changed(self, _treeview):
        path, _column = self.get_cursor()

        index = _treeview.get_model().path_to_store_index(path)
        if index != self.view.cursor.index:
            self.view.cursor.index = index

        # We defer the scrolling until GTK has finished all its current drawing
        # tasks, hence the gobject.idle_add. If we don't wait, then the TreeView
        # draws the editor widget in the wrong position. Presumably GTK issues
        # a redraw event for the editor widget at a given x-y position and then also
        # issues a TreeView scroll; thus, the editor widget gets drawn at the wrong
        # position.
        def do_scroll():
            self.scroll_to_cell(path, self.get_column(0), True, 0.5, 0.0)
            return False

        gobject.idle_add(do_scroll)
        return True

    def _on_key_press(self, _widget, _event, _data=None):
        # The TreeView does interesting things with combos like SHIFT+TAB.
        # So we're going to stop it from doing this.
        return True

    def _on_modified(self, _widget):
        self.emit("modified")
        return True


class StoreCellRenderer(gtk.GenericCellRenderer):
    """
    Cell renderer for a unit based on the C{UnitRenderer} class from Virtaal's
    pre-MVC days.
    """

    __gtype_name__ = "StoreCellRenderer"

    __gproperties__ = {
        "unit": (
            gobject.TYPE_PYOBJECT,
            "The unit",
            "The unit that this renderer is currently handling",
            gobject.PARAM_READWRITE
        ),
        "editable": (
            gobject.TYPE_BOOLEAN,
            "editable",
            "A boolean indicating whether this unit is currently editable",
            False,
            gobject.PARAM_READWRITE
        ),
    }

    __gsignals__ = {
        "editing-done": (
            gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE,
            (gobject.TYPE_STRING, gobject.TYPE_BOOLEAN, gobject.TYPE_BOOLEAN)
        ),
        "modified": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ())
    }

    ROW_PADDING = 10
    """The number of pixels between rows."""

    # INITIALIZERS #
    def __init__(self, view):
        gtk.GenericCellRenderer.__init__(self)
        self.set_property('mode', gtk.CELL_RENDERER_MODE_EDITABLE)
        self.view = view
        self.__unit = None
        self.editable = False
        self._editor = None
        self.source_layout = None
        self.target_layout = None


    # ACCESSORS #
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


    # INTERFACE METHODS #
    def do_set_property(self, pspec, value):
        setattr(self, pspec.name, value)

    def do_get_property(self, pspec):
        return getattr(self, pspec.name)

    def do_get_size(self, widget, _cell_area):
        #TODO: store last unitid and computed dimensions
        width = widget.get_toplevel().get_allocation().width - 32
        if width < -1:
            width = -1
        if self.editable:
            editor = self.view.get_unit_celleditor(self.unit)
            editor.set_size_request(width, -1)
            editor.show()
            compute_optimal_height(editor, width)
            parent_height = widget.get_allocation().height
            if parent_height < -1:
                parent_height = widget.size_request()[1]
            if parent_height > 0:
                self.check_editor_height(editor, width, parent_height)
            _width, height = editor.size_request()
            height += self.ROW_PADDING
        else:
            height = self.compute_cell_height(widget, width)
        #height = min(height, 600)
        y_offset = self.ROW_PADDING / 2
        return 0, y_offset, width, height

    def do_start_editing(self, _event, tree_view, path, _bg_area, cell_area, _flags):
        """Initialize and return the editor widget."""
        editor = self.view.get_unit_celleditor(self.unit)
        editor.set_size_request(cell_area.width, cell_area.height)
        if not getattr(self, '_editor_editing_done_id', None):
            self._editor_editing_done_id = editor.connect("editing-done", self._on_editor_done)
        if not getattr(self, '_editor_modified_id', None):
            self._editor_modified_id = editor.connect("modified", self._on_modified)
        editor.set_border_width(min(self.props.xpad, self.props.ypad))
        editor.show()
        return editor

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
            source_x += (width/2) + 10
        widget.get_style().paint_layout(window, gtk.STATE_NORMAL, False,
                cell_area, widget, '', source_x, y, self.source_layout)
        widget.get_style().paint_layout(window, gtk.STATE_NORMAL, False,
                cell_area, widget, '', target_x, y, self.target_layout)


    # METHODS #
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
        lang_controller = self.view.controller.main_controller.lang_controller
        srclang = lang_controller.source_lang.code
        tgtlang = lang_controller.target_lang.code
        self.source_layout = self._get_pango_layout(widget, self.unit.source, width / 2,
                rendering.get_source_font_description())
        self.source_layout.get_context().set_language(rendering.get_language(srclang))
        self.target_layout = self._get_pango_layout(widget, self.unit.target, width / 2,
                rendering.get_target_font_description())
        self.target_layout.get_context().set_language(rendering.get_language(tgtlang))
        # This makes no sense, but has the desired effect to align things correctly for
        # both LTR and RTL languages:
        if widget.get_direction() == gtk.TEXT_DIR_RTL:
            self.source_layout.set_alignment(pango.ALIGN_RIGHT)
            self.target_layout.set_alignment(pango.ALIGN_RIGHT)
            self.target_layout.set_auto_dir(False)
        _layout_width, source_height = self.source_layout.get_pixel_size()
        _layout_width, target_height = self.target_layout.get_pixel_size()
        return max(source_height, target_height) + self.ROW_PADDING

    def check_editor_height(self, editor, width, parentheight):
        notesheight = 0

        for note in editor._widgets['notes'].values():
            notesheight += note.size_request()[1]

        maxheight = parentheight - notesheight

        if maxheight < 0:
            return

        visible_textboxes = []
        for textbox in (editor._widgets['sources'] + editor._widgets['targets']):
            if textbox.props.visible:
                visible_textboxes.append(textbox)

        max_tb_height = maxheight / len(visible_textboxes)

        for textbox in visible_textboxes:
            if textbox.props.visible and textbox.parent.size_request()[1] > max_tb_height:
                textbox.parent.set_size_request(-1, max_tb_height)
                #logging.debug('%s.set_size_request(-1, %d)' % (textbox.parent, max_tb_height))


    # EVENT HANDLERS #
    def _on_editor_done(self, editor):
        self.emit("editing-done", editor.get_data("path"), editor.must_advance, editor.is_modified())
        return True

    def _on_modified(self, widget):
        self.emit("modified")
