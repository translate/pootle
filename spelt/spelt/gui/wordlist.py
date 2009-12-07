#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008 Zuza Software Foundation
#
# This file is part of Spelt.
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

import gobject, gtk, gtk.glade

from spelt.common import Configuration, _
from spelt.models import LanguageDB, SurfaceForm

class WordList(object):
    """
    A view-like wrapper to the word list found at the bottom of the main
    window.
    """

    # MEMBERS #
    word_selected_handlers = []
    """A list of callable objects that will be called in order when a surface
    form is selected from the list. The callable should take a single
    parameter: the models.SurfaceForm model of the selected word."""

    # CONSTRUCTOR #
    def __init__(self, glade_xml, langdb=None, gui=None):
        """Constructor.
            @type  glade_xml: gtk.glade.XML
            @param glade_xml: The Glade XML object to load widgets from.
            """
        assert isinstance(glade_xml, gtk.glade.XML)

        self.glade_xml              = glade_xml
        self.gui                    = gui
        self.langdb                 = langdb
        self.selected_iter          = None
        self.word_selected_handlers = []

        self.__init_widgets()

    # METHODS #
    def next(self):
        iter = self.store.get_iter_first()
        if self.selected_iter is None:
            return
        self.store.remove(self.selected_iter)

        self.selected_iter = self.store.get_iter_first()
        if self.selected_iter is None:
            return
        self.treeview.get_selection().select_iter(self.selected_iter)
        self.treeview.row_activated(self.store.get_path(self.selected_iter), self.treeview.get_column(0))

    def refresh(self, langdb=None):
        """Reload data from self.langdb database."""
        if langdb is not None and isinstance(langdb, LanguageDB):
            self.langdb = langdb

        if not self.langdb or not isinstance(self.langdb, LanguageDB):
            return

        self.store.clear()
        # TODO: Replace next line with one supporting filters.
        # Currently only surface forms with status == 'todo' are filtered.
        sforms = [model for model in self.langdb.surface_forms if model.status == 'todo']
        sforms.sort(cmp=lambda x, y: x.id - y.id)

        for sf in sforms:
            self.store.append([sf])

        # Now that the TreeView's model is filled, select the first row...
        iter = self.store.get_iter_first()
        if iter is None:
            for f in self.word_selected_handlers:
                if callable(f):
                    f(None)
        else:
            self.treeview.get_selection().select_iter(iter)
            self.treeview.row_activated(self.store.get_path(iter), self.treeview.get_column(0))
            self.selected_iter = iter

    def __init_widgets(self):
        """Get and initialize widgets from the Glade object."""
        # TODO: Add support for filters
        self.store = gtk.ListStore(gobject.TYPE_PYOBJECT)

        self.treeview = self.glade_xml.get_widget('tvw_words')
        self.treeview.set_model(self.store)

        # Add columns
        cell = gtk.CellRendererText()
        col  = gtk.TreeViewColumn(_('Surface Form'))
        col.pack_start(cell)
        col.set_cell_data_func(cell, self.__render_word)
        self.treeview.append_column(col)

        # Connect signals
        self.treeview.connect('row-activated', self.__on_row_activated, self.store)

        # Load data if available
        self.refresh()


    # SIGNAL HANDLERS #
    def __on_row_activated(self, treeview, path, col, store):
        self.selected_iter = store.get_iter(path)
        model = store.get_value(self.selected_iter, 0)

        for f in self.word_selected_handlers:
            if callable(f):
                f(model)

    def __render_word(self, col, cell, store, iter):
        """Cell data function that renders the surface form from it's model in
            the gtk.ListStore.
            
            See gtk.TreeViewColumn.set_cell_data_func()'s documentation for
            description of parameters. For the sake of practicality, not that
            "store.get_value(iter, 0)" returns the object from the selected
            (double clicked) line (a models.SurfaceForm model in this case)."""
        cell.set_property('text', store.get_value(iter, 0).value)
