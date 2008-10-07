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

import os
import os.path as path
import time
import traceback

try:
    import pygtk
    pygtk.require("2.0")
except:
    pass

import gobject
import gtk
from gtk import gdk
from gtk import glade

from translate.storage import poheader
from support import openmailto

import pan_app
from widgets.entry_dialog import EntryDialog
import store_grid
import unit_renderer
from about import About
import formats
import document
import recent
from support import bijection
from autocompletor import AutoCompletor
from autocorrector import AutoCorrector
from mode_selector import ModeSelector

# FIXME: Add docstrings!

def load_glade_file(path_parts, domain):
    gladename = pan_app.get_abs_data_filename(path_parts)
    gui = glade.XML(gladename, domain=domain)
    return gladename, gui


class Virtaal:
    """The entry point class for Virtaal"""

    WRAP_DELAY = 0.25

    def __init__(self, startup_file=None):
        #Set the Glade file
        self.gladefile, self.gui = load_glade_file(["virtaal", "virtaal.glade"], "virtaal")

        #Create our events dictionary and connect it
        dic = {
                "on_mainwindow_destroy" : gtk.main_quit,
                "on_mainwindow_delete" : self._on_mainwindow_delete,
                "on_open_activate" : self._on_file_open,
                "on_save_activate" : self._on_file_save,
                "on_saveas_activate" : self._on_file_saveas,
                "on_quit" : self._on_quit,
                "on_about_activate" : self._on_help_about,
                "on_localization_guide_activate" : self._on_localization_guide,
                "on_menuitem_documentation_activate" : self._on_documentation,
                "on_menuitem_report_bug_activate" : self._on_report_bug,
                }
        self.gui.signal_autoconnect(dic)

        self.mode_bar = self.gui.get_widget("mode_bar")
        self.status_bar = self.gui.get_widget("status_bar")
        self.statusbar_context_id = self.status_bar.get_context_id("statusbar")
        self.sw = self.gui.get_widget("scrolledwindow1")
        self.main_window = self.gui.get_widget("MainWindow")
        self.main_window.set_icon_from_file(pan_app.get_abs_data_filename(["icons", "virtaal.ico"]))
        recent_files = self.gui.get_widget("recent_files")
        recent.rc.connect("item-activated", self._on_recent_file_activated)
        recent_files.set_submenu(recent.rc)
        self._setup_key_bindings()
        self.main_window.show()

        self.modified = False
        self.filename = None

        self.store_grid = None
        self.document = None

        self.autocomp = AutoCompletor()
        self.autocorr = AutoCorrector(acorpath=pan_app.get_abs_data_filename(['virtaal', 'autocorr']))

        if startup_file != None:
            self.load_file(startup_file)

    def _setup_key_bindings(self):
        self.accel_group = gtk.AccelGroup()
        self.main_window.add_accel_group(self.accel_group)
        gtk.accel_map_add_entry("<Virtaal>/Edit/Undo", gtk.keysyms.z, gdk.CONTROL_MASK)
        gtk.accel_map_add_entry("<Virtaal>/Edit/Search", gtk.keysyms.F3, 0)
        gtk.accel_map_add_entry("<Virtaal>/Navigation/Up", gtk.accelerator_parse("Up")[0], gdk.CONTROL_MASK)
        gtk.accel_map_add_entry("<Virtaal>/Navigation/Down", gtk.accelerator_parse("Down")[0], gdk.CONTROL_MASK)
        gtk.accel_map_add_entry("<Virtaal>/Navigation/PgUp", gtk.accelerator_parse("Page_Up")[0], gdk.CONTROL_MASK)
        gtk.accel_map_add_entry("<Virtaal>/Navigation/PgDown", gtk.accelerator_parse("Page_Down")[0], gdk.CONTROL_MASK)
        self.accel_group.connect_by_path("<Virtaal>/Edit/Undo", self._on_undo)
        self.accel_group.connect_by_path("<Virtaal>/Edit/Search", self._on_search)

    def _on_undo(self, _accel_group, acceleratable, _keyval, _modifier):
        unit_renderer.undo(acceleratable.focus_widget)

    def _on_search(self, _accel_group, acceleratable, _keyval, _modifier):
        if not self.document:
            return
        self.document.mode_selector.select_mode_by_name('Search')
        # FIXME: Hack to make sure that the search entry has focus after pressing F3:
        self.document.mode_selector.current_mode.ent_search.grab_focus()

    def _on_mainwindow_delete(self, _widget, _event):
        return self._on_quit(_event)

    def _on_quit(self, _event):
        if self._confirm_unsaved(self.main_window):
            return True
        gtk.main_quit()
        return False

    def _on_file_open(self, _widget, destroyCallback=None):
        chooser = formats.file_open_chooser(destroyCallback)
        chooser.set_transient_for(self.main_window)
        while True:
            response = chooser.run()
            if response == gtk.RESPONSE_OK:
                filename = chooser.get_filename()
                uri = chooser.get_uri()
                pan_app.settings.general["lastdir"] = path.dirname(filename)
                pan_app.settings.write()
                if self.open_file(filename, chooser, uri=uri):
                    break
            elif response == gtk.RESPONSE_CANCEL or \
                    response == gtk.RESPONSE_DELETE_EVENT:
                break
        chooser.destroy()

    def _on_recent_file_activated(self, chooser):
        item = chooser.get_current_item()
        if item.exists():
            # For now we only handle local files, and limited the recent
            # manager to only give us those anyway, so we can get the filename
            self.open_file(item.get_uri_display(), self.main_window, uri=item.get_uri())

    def _confirm_unsaved(self, dialog):
        if self.modified:
            (RESPONSE_SAVE, RESPONSE_DISCARD) = (gtk.RESPONSE_YES, gtk.RESPONSE_NO)
            dialog = gtk.MessageDialog(dialog,
                            gtk.DIALOG_MODAL,
                            gtk.MESSAGE_QUESTION,
                            gtk.BUTTONS_NONE,
                            _("The current file has been modified.\nDo you want to save your changes?"))
            dialog.add_buttons(gtk.STOCK_SAVE, RESPONSE_SAVE)
            dialog.add_buttons(_("_Discard"), RESPONSE_DISCARD)
            dialog.add_buttons(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
            dialog.set_default_response(RESPONSE_SAVE)
            response = dialog.run()
            dialog.destroy()
            if response == RESPONSE_DISCARD:
                return False
            elif response in [gtk.RESPONSE_CANCEL, gtk.RESPONSE_DELETE_EVENT]:
                return True
            elif response == RESPONSE_SAVE:
                if self._on_file_save():
                    return True
        return False

    def open_file(self, filename, dialog, reload=False, uri=None):
        if self._confirm_unsaved(dialog):
            return True
        if filename == self.filename and not reload:
            dialog = gtk.MessageDialog(dialog,
                            gtk.DIALOG_MODAL,
                            gtk.MESSAGE_QUESTION,
                            gtk.BUTTONS_YES_NO,
                            _("You selected the currently open file for opening. Do you want to reload the file?"))
            dialog.set_default_response(gtk.RESPONSE_NO)
            response = dialog.run()
            dialog.destroy()
            if response in [gtk.RESPONSE_NO, gtk.RESPONSE_DELETE_EVENT]:
                return True
        return self.load_file(filename, dialog=dialog, uri=uri)

    def load_file(self, filename, dialog=None, store=None, uri=None):
        """Do the actual loading of the file into the GUI"""
        if path.isfile(filename):
            # To ensure that the WATCH cursor gets a chance to be displayed
            # before we block the GUI, we need to add it to the idle
            # processing
            def hard_work(dialog=None):
                try:
                    mode_selector = getattr(self.document, 'mode_selector', None)
                    self.document = document.Document(filename, store=store, mode_selector=mode_selector)
                    child = self.mode_bar.get_children()[0]
                    self.mode_bar.remove(child)
                    self.mode_bar.pack_start(self.document.mode_selector)
                    self.mode_bar.reorder_child(self.document.mode_selector, 0)

                    self.filename = filename
                    self.store_grid = store_grid.UnitGrid(self)
                    self.store_grid.connect("modified", self._on_modified)
                    child = self.sw.get_child()
                    self.sw.remove(child)
                    child.destroy()
                    self.sw.add(self.store_grid)
                    self.main_window.connect("configure-event", self.store_grid.on_configure_event)
                    self.main_window.show_all()
                    self.store_grid.grab_focus()
                    self._set_saveable(False)
                    menuitem = self.gui.get_widget("saveas_menuitem")
                    menuitem.set_sensitive(True)

                    self.autocomp.add_words_from_store(self.document.store)
                    self.autocorr.load_dictionary(lang=pan_app.settings.language['contentlang'])
                    self.store_grid.connect('cursor-changed', self._on_grid_cursor_changed)
                    if uri:
                        recent.rm.add_item(uri)
                    gobject.idle_add(self.main_window.window.set_cursor, None, priority=gobject.PRIORITY_LOW)

                except Exception, e:
                    dialog = gtk.MessageDialog(dialog or self.main_window,
                                    gtk.DIALOG_MODAL,
                                    gtk.MESSAGE_ERROR,
                                    gtk.BUTTONS_OK,
                                    ("%s\n\n%s" % (_("Error opening file:"), str(e))))
                    self.main_window.window.set_cursor(None)
                    traceback.print_exc()
                    dialog.run()
                    dialog.destroy()
                return False

            self.main_window.window.set_cursor(gdk.Cursor(gdk.WATCH))
            gobject.idle_add(hard_work, dialog)
            return True

        # File doesn't exist
        dialog = gtk.MessageDialog(dialog or self.main_window,
                        gtk.DIALOG_MODAL,
                        gtk.MESSAGE_ERROR,
                        gtk.BUTTONS_OK,
                        _("%(filename)s does not exist." % {"filename": filename}))
        self.main_window.window.set_cursor(None)
        dialog.run()
        dialog.destroy()
        return False

    def set_statusbar_message(self, msg):
        self.status_bar.pop(self.statusbar_context_id)
        self.status_bar.push(self.statusbar_context_id, msg)
        if msg:
            time.sleep(self.WRAP_DELAY)

    def _set_saveable(self, value):
        menuitem = self.gui.get_widget("save_menuitem")
        menuitem.set_sensitive(value)
        if self.filename:
            modified = ""
            if value:
                modified = "*"
            self.main_window.set_title((_('Virtaal - %(current_file)s %(modified_marker)s') % {"current_file": path.basename(self.filename), "modified_marker": modified}).rstrip())
        self.modified = value

    def _on_grid_cursor_changed(self, grid):
        assert grid is self.store_grid

        # Add words from previously handled widgets to the auto-completion list
        for textview in self.autocomp.widgets:
            buffer = textview.get_buffer()
            bufftext = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter()).decode('utf-8')
            self.autocomp.add_words(self.autocomp.wordsep_re.split(bufftext))

        self.autocomp.clear_widgets()
        self.autocorr.clear_widgets()
        for target in grid.renderer.get_editor(grid).targets:
            self.autocomp.add_widget(target)
            self.autocorr.add_widget(target)

        # Let the mode selector know that about the cursor change so that it can
        # perform any mode-specific actions needed.
        self.document.mode_selector.cursor_changed(grid)

    def _on_modified(self, _widget):
        if not self.modified:
            self._set_saveable(True)

    def _on_file_save(self, _widget=None, filename=None):
        if isinstance(self.document.store, poheader.poheader):
            name = pan_app.settings.translator["name"]
            email = pan_app.settings.translator["email"]
            team = pan_app.settings.translator["team"]
            if not name:
                name = EntryDialog(_("Please enter your name"))
                if name is None:
                    # User cancelled
                    return True
                pan_app.settings.translator["name"] = name
            if not email:
                email = EntryDialog(_("Please enter your e-mail address"))
                if email is None:
                    # User cancelled
                    return True
                pan_app.settings.translator["email"] = email
            if not team:
                team = EntryDialog(_("Please enter your team's information"))
                if team is None:
                    # User cancelled
                    return True
                pan_app.settings.translator["team"] = team
            pan_app.settings.write()
            header_updates = {}
            header_updates["PO_Revision_Date"] = time.strftime("%Y-%m-%d %H:%M") +  poheader.tzstring()
            header_updates["X_Generator"] = pan_app.x_generator
            if name or email:
                header_updates["Last_Translator"] = u"%s <%s>" % (name, email)
                self.document.store.updatecontributor(name, email)
            if team:
                header_updates["Language-Team"] = team
            self.document.store.updateheader(add=True, **header_updates)

        try:
            if filename is None or filename == self.filename:
                self.document.store.save()
            else:
                self.filename = filename
                self.document.store.savefile(filename)
            self._set_saveable(False)
        except IOError, e:
                dialog = gtk.MessageDialog(self.main_window,
                                gtk.DIALOG_MODAL,
                                gtk.MESSAGE_ERROR,
                                gtk.BUTTONS_OK,
                                _("Could not save file.\n\n%(error_message)s\n\nTry saving at a different location." % {error_message: str(e)}))
                dialog.set_title(_("Error"))
                response = dialog.run()
                dialog.destroy()

        return False #continue normally

    def _on_file_saveas(self, widget=None):
        buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_SAVE, gtk.RESPONSE_OK)
        # TODO: use stock text for Save as..."
        chooser = gtk.FileChooserDialog(
                _("Save"),
                self.main_window,
                gtk.FILE_CHOOSER_ACTION_SAVE,
                buttons
        )
        chooser.set_do_overwrite_confirmation(True)
        directory, filename = path.split(self.filename)
        chooser.set_current_name(filename)
        chooser.set_default_response(gtk.RESPONSE_OK)
        chooser.set_current_folder(directory)

        response = chooser.run()
        if response == gtk.RESPONSE_OK:
            filename = chooser.get_filename()
            self._on_file_save(widget, filename)
            pan_app.settings.general["lastdir"] = path.dirname(filename)
            pan_app.settings.write()
        chooser.destroy()

    def _on_help_about(self, _widget=None):
        About(self.main_window)

    def _on_localization_guide(self, _widget=None):
        # Should be more redundent
        # If the guide is installed and no internet then open local
        # If Internet then go live, if no Internet or guide then disable
        openmailto.open("http://translate.sourceforge.net/wiki/guide/start")

    def _on_documentation(self, _widget=None):
        openmailto.open("http://translate.sourceforge.net/wiki/virtaal/index")

    def _on_report_bug(self, _widget=None):
        openmailto.open("http://bugs.locamotion.org/enter_bug.cgi?product=Virtaal")

    def run(self):
        gtk.main()
