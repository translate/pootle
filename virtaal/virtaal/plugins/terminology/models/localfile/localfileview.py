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
import logging
import pango
from gtk import gdk
from locale import strcoll
from translate.lang import factory as lang_factory
from translate.storage import factory as store_factory

from virtaal.common import pan_app
from virtaal.views import BaseView, rendering


class LocalFileView:
    """
    Class that manages the localfile terminology plug-in's GUI presense and interaction.
    """

    # INITIALIZERS #
    def __init__(self, model):
        self.term_model = model
        self.controller = model.controller
        self.mainview = model.controller.main_controller.view
        self._signal_ids = []
        self._setup_menus()
        self.addterm = TermAddDialog(model=model)
        self.fileselect = FileSelectDialog(model=model)


    # METHODS #
    def _setup_menus(self):
        mnu_transfer = self.mainview.gui.get_widget('mnu_placnext')
        self.mnui_edit = self.mainview.gui.get_widget('menuitem_edit')
        self.menu = self.mnui_edit.get_submenu()

        self.mnu_select_files, _menu = self.mainview.find_menu_item(_('Terminology _Files...'), self.mnui_edit)
        if not self.mnu_select_files:
            self.mnu_select_files = self.mainview.append_menu_item(_('Terminology _Files...'), self.mnui_edit, after=mnu_transfer)
        self._signal_ids.append((
            self.mnu_select_files,
            self.mnu_select_files.connect('activate', self._on_select_term_files)
        ))

        self.mnu_add_term, _menu = self.mainview.find_menu_item(_('Add _Term...'), self.mnui_edit)
        if not self.mnu_add_term:
            self.mnu_add_term = self.mainview.append_menu_item(_('Add _Term...'), self.mnui_edit, after=mnu_transfer)
        self._signal_ids.append((
            self.mnu_add_term,
            self.mnu_add_term.connect('activate', self._on_add_term)
        ))

        gtk.accel_map_add_entry("<Virtaal>/Terminology/Add Term", gtk.keysyms.t, gdk.CONTROL_MASK)
        accel_group = self.menu.get_accel_group()
        if accel_group is None:
            accel_group = gtk.AccelGroup()
            self.menu.set_accel_group(accel_group)
        self.mnu_add_term.set_accel_path("<Virtaal>/Terminology/Add Term")
        self.menu.set_accel_group(accel_group)

    def destroy(self):
        for gobj, signal_id in self._signal_ids:
            gobj.disconnect(signal_id)

        self.menu.remove(self.mnu_select_files)
        self.menu.remove(self.mnu_add_term)


    # EVENT HANDLERS #
    def _on_add_term(self, menuitem):
        self.addterm.run(parent=self.mainview.main_window)

    def _on_select_term_files(self, menuitem):
        self.fileselect.run(parent=self.mainview.main_window)


class FileSelectDialog:
    """
    Wrapper for the selection dialog, created in Glade, to manage the list of
    files used by this plug-in.
    """

    COL_FILE, COL_EXTEND = range(2)

    # INITIALIZERS #
    def __init__(self, model):
        self.controller = model.controller
        self.term_model = model
        self.gladefilename, self.gui = BaseView.load_glade_file(
            ["virtaal", "virtaal.glade"],
            root='TermFilesDlg',
            domain='virtaal'
        )
        self._get_widgets()
        self._init_treeview()
        self._init_add_chooser()

    def _get_widgets(self):
        widget_names = ('btn_add_file', 'btn_remove_file', 'btn_open_termfile', 'tvw_termfiles')

        for name in widget_names:
            setattr(self, name, self.gui.get_widget(name))

        self.dialog = self.gui.get_widget('TermFilesDlg')
        self.btn_add_file.connect('clicked', self._on_add_file_clicked)
        self.btn_remove_file.connect('clicked', self._on_remove_file_clicked)
        self.btn_open_termfile.connect('clicked', self._on_open_termfile_clicked)
        self.tvw_termfiles.get_selection().connect('changed', self._on_selection_changed)

    def _init_treeview(self):
        self.lst_files = gtk.ListStore(str, bool)
        self.tvw_termfiles.set_model(self.lst_files)

        cell = gtk.CellRendererText()
        cell.props.ellipsize = pango.ELLIPSIZE_MIDDLE
        col = gtk.TreeViewColumn(_('File'))
        col.pack_start(cell)
        col.add_attribute(cell, 'text', self.COL_FILE)
        col.set_expand(True)
        col.set_sort_column_id(0)
        self.tvw_termfiles.append_column(col)

        cell = gtk.CellRendererToggle()
        cell.set_radio(True)
        cell.connect('toggled', self._on_toggle)
        col = gtk.TreeViewColumn(_('Extendable'))
        col.pack_start(cell)
        col.add_attribute(cell, 'active', self.COL_EXTEND)
        col.set_expand(False)
        self.tvw_termfiles.append_column(col)

        extend_file = self.term_model.config.get('extendfile', '')
        files = self.term_model.config['files']
        for f in files:
            self.lst_files.append([f, f == extend_file])

        # If there was no extend file, select the first one
        for row in self.lst_files:
            if row[self.COL_EXTEND]:
                break
        else:
            itr = self.lst_files.get_iter_first()
            if itr and self.lst_files.iter_is_valid(itr):
                self.lst_files.set_value(itr, self.COL_EXTEND, True)
                self.term_model.config['extendfile'] = self.lst_files.get_value(itr, self.COL_FILE)
                self.term_model.save_config()

    def _init_add_chooser(self):
        # The following code was mostly copied from virtaal.views.MainView._create_dialogs()
        dlg = gtk.FileChooserDialog(
            _('Add Files'),
            self.controller.main_controller.view.main_window,
            gtk.FILE_CHOOSER_ACTION_OPEN,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK)
        )
        dlg.set_default_response(gtk.RESPONSE_OK)
        all_supported_filter = gtk.FileFilter()
        all_supported_filter.set_name(_("All Supported Files"))
        dlg.add_filter(all_supported_filter)
        supported_files_dict = dict([ (_(name), (extension, mimetype)) for name, extension, mimetype in store_factory.supported_files() ])
        supported_file_names = supported_files_dict.keys()
        supported_file_names.sort(cmp=strcoll)
        for name in supported_file_names:
            extensions, mimetypes = supported_files_dict[name]
            #XXX: we can't open generic .csv formats, so listing it is probably
            # more harmful than good.
            if "csv" in extensions:
                continue
            new_filter = gtk.FileFilter()
            new_filter.set_name(name)
            if extensions:
                for extension in extensions:
                    new_filter.add_pattern("*." + extension)
                    all_supported_filter.add_pattern("*." + extension)
                    for compress_extension in store_factory.decompressclass.keys():
                        new_filter.add_pattern("*.%s.%s" % (extension, compress_extension))
                        all_supported_filter.add_pattern("*.%s.%s" % (extension, compress_extension))
            if mimetypes:
                for mimetype in mimetypes:
                    new_filter.add_mime_type(mimetype)
                    all_supported_filter.add_mime_type(mimetype)
            dlg.add_filter(new_filter)
        all_filter = gtk.FileFilter()
        all_filter.set_name(_("All Files"))
        all_filter.add_pattern("*")
        dlg.add_filter(all_filter)
        dlg.set_select_multiple(True)

        self.add_chooser = dlg


    # METHODS #
    def clear_selection(self):
        self.tvw_termfiles.get_selection().unselect_all()

    def run(self, parent=None):
        if isinstance(parent, gtk.Widget):
            self.dialog.set_transient_for(parent)

        self.clear_selection()

        self.dialog.show_all()
        self.dialog.run()
        self.dialog.hide()


    # EVENT HANDLERS #
    def _on_add_file_clicked(self, button):
        self.add_chooser.show_all()
        response = self.add_chooser.run()
        self.add_chooser.hide()

        if response != gtk.RESPONSE_OK:
            return

        mainview = self.term_model.controller.main_controller.view
        currfiles = [row[self.COL_FILE] for row in self.lst_files]
        for filename in self.add_chooser.get_filenames():
            if filename in currfiles:
                continue
            # Try and open filename as a translation store
            try:
                store = store_factory.getobject(filename)
                currfiles.append(filename)
                self.lst_files.append([filename, False])
            except Exception, exc:
                message = _('Unable to load %(filename)s:\n\n%(errormsg)s') % {'filename': filename, 'errormsg': str(exc)}
                mainview.show_error_dialog(title=_('Error opening file'), message=message)

        self.term_model.config['files'] = currfiles
        self.term_model.save_config()
        self.term_model.load_files() # FIXME: This could be optimized to only load and add the new selected files.

    def _on_remove_file_clicked(self, button):
        model, selected = self.tvw_termfiles.get_selection().get_selected()
        if not selected:
            return

        remfile = model.get_value(selected, self.COL_FILE)
        extend = model.get_value(selected, self.COL_EXTEND)
        self.term_model.config['files'].remove(remfile)

        if extend:
            self.term_model.config['extendfile'] = ''
            itr = model.get_iter_first()
            if itr and model.iter_is_valid(itr):
                model.set_value(itr, self.COL_EXTEND, True)
                self.term_model.config['extendfile'] = model.get_value(itr, self.COL_FILE)

        self.term_model.save_config()
        self.term_model.load_files() # FIXME: This could be optimized to only remove the selected file from the terminology matcher.
        model.remove(selected)

    def _on_open_termfile_clicked(self, button):
        selection = self.tvw_termfiles.get_selection()
        model, itr = selection.get_selected()
        if itr is None:
            return
        selected_file = model.get_value(itr, self.COL_FILE)
        self.term_model.controller.main_controller.open_file(selected_file)

    def _on_selection_changed(self, treesel):
        model, itr = treesel.get_selected()
        enabled = itr is not None
        self.btn_open_termfile.set_sensitive(enabled)
        self.btn_remove_file.set_sensitive(enabled)

    def _on_toggle(self, renderer, path):
        toggled_file = self.lst_files.get_value(self.lst_files.get_iter(path), self.COL_FILE)

        itr = self.lst_files.get_iter_first()
        while itr is not None and self.lst_files.iter_is_valid(itr):
            self.lst_files.set_value(itr, self.COL_EXTEND, self.lst_files.get_value(itr, self.COL_FILE) == toggled_file)
            itr = self.lst_files.iter_next(itr)

        self.term_model.config['extendfile'] = toggled_file
        self.term_model.save_config()


class TermAddDialog:
    """
    Wrapper for the dialog used to add a new term to the terminology file.
    """

    # INITIALIZERS #
    def __init__(self, model):
        self.term_model = model
        self.lang_controller = model.controller.main_controller.lang_controller
        self.unit_controller = model.controller.main_controller.unit_controller

        self.gladefilename, self.gui = BaseView.load_glade_file(
            ["virtaal", "virtaal.glade"],
            root='TermAddDlg',
            domain='virtaal'
        )
        self._get_widgets()

    def _get_widgets(self):
        widget_names = (
            'btn_add_term', 'cmb_termfile', 'eb_add_term_errors', 'ent_source',
            'ent_target', 'lbl_add_term_errors', 'lbl_srclang', 'lbl_tgtlang',
            'txt_comment'
        )

        for name in widget_names:
            setattr(self, name, self.gui.get_widget(name))

        self.dialog = self.gui.get_widget('TermAddDlg')

        cellr = gtk.CellRendererText()
        cellr.props.ellipsize = pango.ELLIPSIZE_MIDDLE
        self.lst_termfiles = gtk.ListStore(str)
        self.cmb_termfile.set_model(self.lst_termfiles)
        self.cmb_termfile.pack_start(cellr)
        self.cmb_termfile.add_attribute(cellr, 'text', 0)

        self.ent_source.connect('changed', self._on_entry_changed)
        self.ent_target.connect('changed', self._on_entry_changed)

        self.eb_add_term_errors.modify_bg(gtk.STATE_NORMAL, gdk.color_parse('#f88'))


    # METHODS #
    def add_term_unit(self, source, target):
        filename = self.cmb_termfile.get_active_text()
        store = self.term_model.get_store_for_filename(filename)
        if store is None:
            logging.debug('No terminology store to extend :(')
            return
        unit = store.addsourceunit(source)
        unit.target = target

        buff = self.txt_comment.get_buffer()
        comments = buff.get_text(buff.get_start_iter(), buff.get_end_iter())
        if comments:
            unit.addnote(comments)

        store.save()
        self.term_model.matcher.extendtm(unit)
        #logging.debug('Added new term: [%s] => [%s], file=%s' % (source, target, store.filename))

    def reset(self):
        unitview = self.unit_controller.view

        source_text = u''
        for src in unitview.sources:
            selection = src.buffer.get_selection_bounds()
            if selection:
                source_text = src.get_text(*selection)
                break
        self.ent_source.modify_font(rendering.get_source_font_description())
        self.ent_source.set_text(source_text.strip())

        target_text = u''
        for tgt in unitview.targets:
            selection = tgt.buffer.get_selection_bounds()
            if selection:
                target_text = tgt.get_text(*selection)
                break
        self.ent_target.modify_font(rendering.get_target_font_description())
        self.ent_target.set_text(target_text.strip())

        self.txt_comment.get_buffer().set_text('')

        self.eb_add_term_errors.hide()
        self.btn_add_term.props.sensitive = True
        self.lbl_srclang.set_text_with_mnemonic(_(u'_Source term — %(langname)s') % {'langname': self.lang_controller.source_lang.name})
        self.lbl_tgtlang.set_text_with_mnemonic(_(u'_Target term — %(langname)s') % {'langname': self.lang_controller.target_lang.name})

        self.lst_termfiles.clear()

        extendfile = self.term_model.config.get('extendfile', None)
        select_index = -1
        i = 0
        for f in self.term_model.config['files']:
            if f == extendfile:
                select_index = i
            self.lst_termfiles.append([f])
            i += 1

        if select_index >= 0:
            self.cmb_termfile.set_active(select_index)

    def run(self, parent=None):
        self.reset()

        if isinstance(parent, gtk.Widget):
            self.dialog.set_transient_for(parent)

        self.dialog.show()
        self._on_entry_changed(None)
        self.ent_source.grab_focus()
        response = self.dialog.run()
        self.dialog.hide()

        if response != gtk.RESPONSE_OK:
            return

        self.add_term_unit(self.ent_source.get_text(), self.ent_target.get_text())


    # EVENT HANDLERS #
    def _on_entry_changed(self, entry):
        self.btn_add_term.props.sensitive = True
        self.eb_add_term_errors.hide()

        src_text = self.ent_source.get_text()
        tgt_text = self.ent_target.get_text()

        dup = self.term_model.get_duplicates(src_text, tgt_text)
        if dup:
            self.lbl_add_term_errors.set_text(_('Identical entry already exists.'))
            self.eb_add_term_errors.show_all()
            self.btn_add_term.props.sensitive = False
            return

        same_src_units = self.term_model.get_units_with_source(src_text)
        if src_text and same_src_units:
            lang = lang_factory.getlanguage(pan_app.get_locale_lang())
            separator = lang.listseperator
            #l10n: The variable is an existing term formatted for emphasis. The default is bold formatting, but you can remove/change the markup if needed. Leave it unchanged if you are unsure.
            translations = separator.join([_('<b>%s</b>') % (u.target) for u in same_src_units])
            errormsg = _('Existing translations: %(translations)s') % {
                'translations': translations
            }
            self.lbl_add_term_errors.set_markup(errormsg)
            self.eb_add_term_errors.show_all()
            return
