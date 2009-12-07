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

import gobject
import gtk
import locale

from virtaal.common import pan_app
from virtaal.views import BaseView


class LanguageSelectDialog(object):
    """
    Represents and manages an instance of the dialog used for language-selection.
    """

    # INITIALIZERS #
    def __init__(self, languages, parent=None):
        super(LanguageSelectDialog, self).__init__()

        self.gladefilename, self.gui = BaseView.load_glade_file(
            ["virtaal", "virtaal.glade"],
            root='LanguageSelector',
            domain='virtaal'
        )

        self._get_widgets()
        self._init_treeviews()
        self.update_languages(languages)

        if isinstance(parent, gtk.Widget):
            self.dialog.set_transient_for(parent)
            self.dialog.set_icon(parent.get_toplevel().get_icon())

    def _get_widgets(self):
        """Load the Glade file and get the widgets we would like to use."""
        widget_names = ('btn_add', 'btn_cancel', 'btn_ok', 'tvw_sourcelang', 'tvw_targetlang')

        for name in widget_names:
            setattr(self, name, self.gui.get_widget(name))

        self.dialog = self.gui.get_widget('LanguageSelector')

        self.btn_ok.connect('clicked', lambda *args: self.dialog.response(gtk.RESPONSE_OK))
        self.btn_cancel.connect('clicked', lambda *args: self.dialog.response(gtk.RESPONSE_CANCEL))

    def _init_treeviews(self):
        self.lst_langs_src = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING)
        self.lst_langs_tgt = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING)
        self.tvw_sourcelang.set_model(self.lst_langs_src)
        self.tvw_targetlang.set_model(self.lst_langs_tgt)

        def searchfunc(model, column, key, iter):
            if  model.get_value(iter, 0).lower().startswith(key.lower()) or \
                model.get_value(iter, 1).lower().startswith(key.lower()):
                return False
            return True
        self.tvw_sourcelang.set_search_equal_func(searchfunc)
        self.tvw_targetlang.set_search_equal_func(searchfunc)

        cell = gtk.CellRendererText()
        col = gtk.TreeViewColumn(_('Language'))
        col.pack_start(cell)
        col.add_attribute(cell, 'text', 0)
        col.set_sort_column_id(0)
        self.tvw_sourcelang.append_column(col)

        cell = gtk.CellRendererText()
        col = gtk.TreeViewColumn(_('Language'))
        col.pack_start(cell)
        col.add_attribute(cell, 'text', 0)
        col.set_sort_column_id(0)
        self.tvw_targetlang.append_column(col)

        cell = gtk.CellRendererText()
        #l10n: This is the column heading for the language code
        col = gtk.TreeViewColumn(_('Code'))
        col.pack_start(cell)
        col.add_attribute(cell, 'text', 1)
        col.set_sort_column_id(1)
        self.tvw_sourcelang.append_column(col)

        cell = gtk.CellRendererText()
        col = gtk.TreeViewColumn(_('Code'))
        col.pack_start(cell)
        col.add_attribute(cell, 'text', 1)
        col.set_sort_column_id(1)
        self.tvw_targetlang.append_column(col)

        def sortfunc(model, iter1, iter2, col):
            return locale.strcoll(model.get_value(iter1, col), model.get_value(iter2, col))
        self.lst_langs_src.set_sort_func(0, sortfunc, 0)
        self.lst_langs_src.set_sort_func(1, sortfunc, 1)
        self.lst_langs_tgt.set_sort_func(0, sortfunc, 0)
        self.lst_langs_tgt.set_sort_func(1, sortfunc, 1)


    # ACCESSORS #
    def get_selected_source_lang(self):
        model, i = self.tvw_sourcelang.get_selection().get_selected()
        if i is not None and model.iter_is_valid(i):
            return model.get_value(i, 1)
        return ''

    def get_selected_target_lang(self):
        model, i = self.tvw_targetlang.get_selection().get_selected()
        if i is not None and model.iter_is_valid(i):
            return model.get_value(i, 1)
        return ''


    # METHODS #
    def clear_langs(self):
        self.lst_langs_src.clear()
        self.lst_langs_tgt.clear()

    def run(self, srclang, tgtlang):
        self.curr_srclang = srclang
        self.curr_tgtlang = tgtlang

        self._select_lang(self.tvw_sourcelang, srclang)
        self._select_lang(self.tvw_targetlang, tgtlang)

        self.tvw_targetlang.grab_focus()
        response = self.dialog.run() == gtk.RESPONSE_OK
        self.dialog.hide()
        return response

    def update_languages(self, langs):
        selected_srccode = self.get_selected_source_lang()
        selected_tgtcode = self.get_selected_target_lang()

        for lang in langs:
            self.lst_langs_src.append([lang.name, lang.code])
            self.lst_langs_tgt.append([lang.name, lang.code])

        if selected_srccode:
            self._select_lang(self.tvw_sourcelang, selected_srccode)
        else:
            self._select_lang(self.tvw_sourcelang, getattr(self, 'curr_srclang', 'en'))
        if selected_tgtcode:
            self._select_lang(self.tvw_targetlang, selected_tgtcode)
        else:
            self._select_lang(self.tvw_targetlang, getattr(self, 'curr_tgtlang', 'en'))

    def _select_lang(self, treeview, langcode):
        model = treeview.get_model()
        i = model.get_iter_first()
        while i is not None and model.iter_is_valid(i):
            if model.get_value(i, 1) == langcode:
                break
            i = model.iter_next(i)

        if i is None or not model.iter_is_valid(i):
            return

        path = model.get_path(i)
        treeview.get_selection().select_iter(i)
        treeview.scroll_to_cell(path)

