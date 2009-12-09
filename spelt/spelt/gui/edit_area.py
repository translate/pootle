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

import datetime
import gobject, gtk, gtk.glade

from spelt.common         import Configuration, exceptions, _
from spelt.models         import LanguageDB, PartOfSpeech, Root, SurfaceForm
from spelt.gui.combomodel import ComboModel
from spelt.gui.wordlist   import WordList


class EditArea(object):
    """
    This class represents the editing area on the GUI.
    """

    COL_TEXT, COL_MODEL = range(2)
    COMPLETION_POPUP_DELAY = 500
    EMPTY_COMBOMODEL = ComboModel([ ('', None) ])
    MAX_COMPLETION_LENGTH = 5

    # CONSTRUCTOR #
    def __init__(self, glade_xml, wordlist, langdb=None, gui=None):
        """Constructor.
            @type  glade_xml: gtk.glade.XML
            @param glade_xml: The Glade XML object to load widgets from.
            """
        assert isinstance(glade_xml, gtk.glade.XML)
        assert isinstance(wordlist, WordList)

        self.config     = Configuration()
        self.current_sf = None
        self.glade_xml  = glade_xml
        self.gui        = gui
        self.langdb     = langdb
        self.wordlist   = wordlist

        self.wordlist.word_selected_handlers.append(self.on_surface_form_selected)
        self.__init_widgets()

        self.root_comp_timeout = 0

    # METHODS #
    def check_pos_text(self, text=None):
        """If text was entered into cmb_pos, handle that text."""
        if text is None:
            text = self.cmb_pos.child.get_text()

        if not text:
            self.set_status(_('No part-of-speech specified.'))
            self.select_pos(None)
            self.cmb_pos.grab_focus()
            return

        shortcut, name = ('|' in text) and ( [substr.strip() for substr in text.split('|')] ) or ('_', text)
        # Search for POS on value and shortcut
        pos = \
            self.langdb.find(section='parts_of_speech', name=name, shortcut=shortcut) + \
            self.langdb.find(section='parts_of_speech', name=text, shortcut=text)

        if pos:
            # NOTE: If more than one part of speech matches, we use the first one
            self.select_pos(pos[0])

            if pos[0].id != self.current_root.pos_id:
                self.set_sensitive(btn_ok=False, btn_add_root=True, btn_mod_root=True)
                self.set_visible(btn_ok=False, btn_add_root=True, btn_mod_root=True)
            else:
                self.set_sensitive(btn_ok=True, btn_add_root=False, btn_mod_root=False)
                self.set_visible(btn_ok=True, btn_add_root=False, btn_mod_root=False)

            if self._new_root:
                # If we are working with a new root, there is not sense in
                # trying to modify it.
                self.set_visible(btn_mod_root=False)
        else:
            # If we get here, we have a new part of speech
            self.set_status(_('Part of speech not found.'))
            self.select_pos(None)
            return

        # Select the focus to the first button in the list that is both visible and active
        for btn in (self.btn_ok, self.btn_add_root, self.btn_mod_root):
            if btn.get_property('visible') and btn.get_property('sensitive'):
                btn.grab_focus()

    def check_root_text(self, text=None):
        """If text was entered into C{ent_root}, handle that text."""
        if text is None:
            text = self.ent_root.get_text()

        if not text:
            self.set_status(_('A root must be specified.'))
            self.select_root(None)
            return

        # First check if the text in entry is that of an existing root:
        roots = self.langdb.find(section='roots', value=text)

        if roots and len(roots) > 0:
            # NOTE: If more than one root matches, we use the first one
            self.select_root(roots[0])
        else:
            # If we get here, we have a new root on our hands
            self.select_root(None) # Deselect root
            self.ent_root.set_text(text)
            self.current_root = Root(
                value   = unicode(text),
                user_id = self.config.user['id'],
                date    = datetime.datetime.now()
            )
            self._new_root = True
            self.select_pos(None)  # Deselect POS

            self.set_visible(btn_ok=False, btn_add_root=True)
            self.set_sensitive(cmb_pos=True, btn_add_root=False)
            self.cmb_pos.child.grab_focus()

    def on_surface_form_selected(self, sf):
        """A proxied event handler for when a surface form is selected in the
            word list.

            See the documentation of spelt.gui.WordList.word_selected_handlers for
            the use of this method."""
        if sf is None:
            self.lbl_word.set_markup('')
            self.select_root(None)
            self.set_sensitive(btn_reject=False, btn_ignore=False)
            self.set_visible(btn_ok=False)
            return

        self.current_sf = sf
        self.lbl_status.hide()
        self.lbl_word.set_markup('<b>%s</b>' % sf.value)

        if self.langdb is None:
            return

        # Set GUI to its initial state
        self.set_sensitive(
            btn_reject=True,
            btn_ignore=True,
            btn_ok=True,
            btn_add_root=True,
            btn_mod_root=True,
            cmb_pos=True
        )
        self.set_visible(btn_ok=True, btn_add_root=False, btn_mod_root=False)

        if not sf.root_id:
            # sf does not have an associated root, so there's nothing to select
            # in the combo boxes.
            self.select_root(None)
        else:
            roots_found = self.langdb.find(id=sf.root_id, section='roots')
            # The roots_found list can have a maximum of 1 element, because we
            # search the database on ID's. ID's are guaranteed to be unique by the
            # models (via it's inheritence of IDModel).
            if roots_found:
                self.select_root(roots_found[0])
            else:
                raise exceptions.RootError(_( 'No root object found with ID %d' % (sf.root_id) ))

        self.ent_root.grab_focus()

    def pos_tostring(self, pos):
        """How a PartOfSpeech object should be represented as a string in the GUI.

            @type  pos: PartOfSpeech
            @param pos: The PartOfSpeech object to get a string representation for.
            @rtype      str
            @return     The string representation of the parameter PartOfSpeech."""
        if not pos:
            return ''
        assert isinstance(pos, PartOfSpeech)
        # TODO: Test RTL scripts
        return '%s | %s' % (pos.shortcut, pos.name)

    def root_tostring(self, root):
        """How a Root object should be represented as a string in the GUI.

            @type  pos: Root
            @param pos: The Root object to get a string representation for.
            @rtype      str
            @return     The string representation of the parameter Root."""
        if not root:
            return ''
        pos = self.langdb.find(id=root.pos_id, section='parts_of_speech')
        if not pos:
            return u"%s (<no part-of-speech>)" % (root.value)
        return u"%s (%s)" % (root.value, pos[0].name)

    def refresh(self, langdb=None):
        """Reload data from self.langdb database."""
        if not langdb is None and isinstance(langdb, LanguageDB):
            self.langdb = langdb

        if not self.langdb or not isinstance(self.langdb, LanguageDB):
            return

        self.pos_store = ComboModel([ (self.pos_tostring(m), m) for m in self.langdb.parts_of_speech ])
        self.cmb_pos.set_model(self.pos_store)
        self.cmb_pos.child.get_completion().set_model(self.pos_store)

        self.root_store = ComboModel([ (m.value, m) for m in self.langdb.roots ])
        self.ent_root.get_completion().set_model(self.root_store)

    def select_root(self, root):
        """Set the root selected in the C{ent_root} combo box to that of the parameter.

            @type  root: spelt.models.Root
            @param root: The root to select in the combo box."""
        if root is None:
            # Deselect root
            self.select_pos(None) # This deselects the part of speech too.
            self.set_sensitive(cmb_pos=False)
            self.ent_root.set_text('')
            self.ent_root.grab_focus()
            return

        assert isinstance(root, Root)

        self.current_root = root
        self._new_root = False
        self.ent_root.set_text(root.value)
        self.set_sensitive(cmb_pos=True)

        pos_found = self.langdb.find(id=root.pos_id, section='parts_of_speech')
        # The pos_found list can have a maximum of 1 element, because we
        # search the database on ID's. ID's are guaranteed to be unique by the
        # models (via it's inheritence of IDManager).
        if pos_found:
            self.select_pos(pos_found[0])
            self.btn_ok.grab_focus()
        else:
            self.cmb_pos.grab_focus()
            # The exception commented out below should be changed to a warning
            #raise exceptions.PartOfSpeechError(_( 'No part of speech found with ID %d' % (root.pos_id) ))

    def select_pos(self, pos):
        """Set the part of speech selected in the cmb_pos combo box to that of
            the parameter.

            @type  pos: models.PartOfSpeech
            @param pos: The part of speech to select in the combo box."""
        if pos is None:
            # Deselect POS
            self.cmb_pos.set_active(-1)
            self.cmb_pos.child.set_text('')
            self.cmb_pos.grab_focus()
            self.set_visible(btn_ok=True, btn_add_root=False, btn_mod_root=False)
            self.set_sensitive(btn_ok=False)
            return

        assert isinstance(pos, PartOfSpeech)
        iter = self.pos_store.get_iter_first()

        while self.pos_store.iter_is_valid(iter):
            if self.pos_store.get_value(iter, self.COL_MODEL) == pos:
                self.cmb_pos.set_active_iter(iter)
                self.current_pos = pos

                self.set_sensitive(btn_ok=True)
                break

            iter = self.pos_store.iter_next(iter)

    def set_sensitive(self, **kwargs):
        """Set widgets' sensitivity based on keyword arguments.

            Example: "set_sensitive(cmb_pos=False) disables cmb_pos."""
        for widget, sensitive in kwargs.items():
            if hasattr(self, widget):
                getattr(self, widget).set_sensitive(sensitive)

    def set_status(self, msg):
        """Displays the given status message for 3 seconds."""
        self.lbl_status.show()
        self.lbl_status.set_markup('<span color="red">%s</span>' % msg)
        gobject.timeout_add(3000, self.__clear_status)

    def set_visible(self, **kwargs):
        """Set widgets' visibility based on keyword arguments.

            Example: "set_visible(btn_ok=False)" will hide btn_ok."""
        for widget, visible in kwargs.items():
            if hasattr(self, widget):
                getattr(self, widget).set_property('visible', visible)

    def __init_widgets(self):
        """Get and initialize widgets from the Glade object."""
        widgets = (
            'lbl_word',
            'btn_reject',
            'btn_ignore',
            'ent_root',
            'cmb_pos',
            'lbl_status',
            'btn_ok',
            'btn_add_root',
            'btn_mod_root'
        )

        for widget_name in widgets:
            setattr(self, widget_name, self.glade_xml.get_widget(widget_name))

        self.lbl_word.set_markup('<b>[nothing]</b>')

        # Initialize combo's
        pos_cell = gtk.CellRendererText()
        self.pos_store = self.EMPTY_COMBOMODEL
        self.cmb_pos.set_model(self.pos_store)
        self.cmb_pos.set_text_column(self.COL_TEXT)
        self.cmb_pos.clear()
        self.cmb_pos.pack_start(pos_cell)
        self.cmb_pos.add_attribute(pos_cell, 'text', self.COL_TEXT)

        # Setup autocompletion
        pos_cell = gtk.CellRendererText()
        self.pos_completion = gtk.EntryCompletion()
        self.pos_completion.clear()
        self.pos_completion.pack_start(pos_cell)
        self.pos_completion.set_cell_data_func(pos_cell, self.__render_pos)
        self.pos_completion.set_inline_completion(True)
        self.pos_completion.set_model(self.pos_store)
        self.pos_completion.set_match_func(self.__match_pos)
        self.pos_completion.props.text_column = self.COL_TEXT
        self.cmb_pos.child.set_completion(self.pos_completion)

        self.root_store = self.EMPTY_COMBOMODEL
        root_cell = gtk.CellRendererText()
        self.root_completion = gtk.EntryCompletion()
        self.root_completion.clear()
        self.root_completion.pack_start(root_cell)
        self.root_completion.set_cell_data_func(root_cell, self.__render_root)
        self.root_completion.set_match_func(lambda *args: True) # Always match, because the model will already be filtered.
        self.root_completion.set_model(self.root_store)
        self.root_completion.props.text_column = self.COL_TEXT
        self.ent_root.set_completion(self.root_completion)

        self.__connect_signals()

    def __connect_signals(self):
        """Connects widgets' signals to their appropriate handlers.

            This method should only be called once (by __init_widgets()), but
            shouldn't break anything if it's called again: the same events will
            just be reconnected to the same handlers."""
        # Buttons
        self.btn_add_root.connect('clicked', self.__on_btn_add_root_clicked)
        self.btn_ignore.connect('clicked', self.__on_btn_ignore_clicked)
        self.btn_mod_root.connect('clicked', self.__on_btn_mod_root_clicked)
        self.btn_ok.connect('clicked', self.__on_btn_ok_clicked)
        self.btn_reject.connect('clicked', self.__on_btn_reject_clicked)
        # Combo's
        self.cmb_pos.connect('changed', self.__on_cmb_changed, self.select_pos)
        # ComboBoxEntry's Entry
        self.cmb_pos.child.connect('activate', self.__on_entry_activated, self.check_pos_text)
        self.cmb_pos.child.connect('changed', self.__on_entry_changed, self.select_pos)
        self.cmb_pos.child.connect('key-press-event', self.__on_entry_key_press_event, self.check_pos_text)

        # Entry's
        self.ent_root.connect('activate', self.__on_entry_activated, self.check_root_text)
        self.ent_root.connect('changed', self.__on_root_changed, self.ent_root.get_completion())
        self.ent_root.connect('key-press-event', self.__on_entry_key_press_event, self.check_root_text)

        # EntryCompletions
        self.pos_completion.connect('match-selected', self.__on_match_selected, self.select_pos)
        self.root_completion.connect('match-selected', self.__on_match_selected, self.select_root)

    def __match_pos(self, completion, key, iter):
        model = self.pos_store.get_value(iter, self.COL_MODEL)
        if model is None:
            return False
        return model.shortcut.lower().startswith(key) or model.name.lower().startswith(key)

    # GUI SIGNAL HANDLERS #
    def _complete_root(self):
        self.compl_count = 0

        def check(model, iter, text):
            if model[iter][self.COL_TEXT].lower().startswith(text) and self.compl_count < self.MAX_COMPLETION_LENGTH:
                self.compl_count += 1
                return True
            return False

        filter = self.root_store.filter_new()
        filter.set_visible_func(check, self.ent_root.get_text().lower())
        self.ent_root.get_completion().set_model(filter)
        self.ent_root.get_completion().insert_prefix()

        self.root_comp_timeout = 0

        return False

    def __clear_status(self):
        self.lbl_status.hide()
        return False

    def __on_btn_add_root_clicked(self, btn):
        """Add the current root to the language database."""
        if self.langdb.find(id=self.current_root.id, section='roots'):
            # The root already exists, so we have to duplicate it. It should have a different POS, though.
            self.current_root = Root(
                value   = unicode(self.current_root.value),
                user_id = self.config.user['id'],
                date    = datetime.datetime.now()
            )
        self.current_root.pos_id = self.current_pos.id
        self.langdb.add_root(self.current_root)
        self._new_root = False

        if self.cmb_pos.get_active() < 0:
            self.langdb.add_part_of_speech(self.current_pos)

        self.root_store = ComboModel(self.root_store._rows + [(self.current_root.value, self.current_root)])

        # Update GUI
        self.set_sensitive(btn_ok=True, btn_add_root=False, btn_mod_root=False)
        self.set_visible(  btn_ok=True, btn_add_root=False, btn_mod_root=False)
        self.btn_ok.clicked()
        self.gui.changes_made = True

    def __on_btn_ignore_clicked(self, btn):
        """Set the currently selected surface form's status to "ignored"."""
        if not self.current_sf:
            return

        self.current_sf.status = 'ignored'
        self.wordlist.next()
        self.gui.changes_made = True

    def __on_btn_mod_root_clicked(self, btn):
        """Update the current root with the selected part of speech."""
        if self.cmb_pos.get_active() < 0:
            self.langdb.add_part_of_speech(self.current_pos)

        self.current_root.date    = datetime.datetime.now()
        self.current_root.pos_id  = self.current_pos.id
        self.current_root.user_id = self.config.user['id']

        # Update GUI
        self.set_sensitive(btn_ok=True, btn_add_root=False, btn_mod_root=False)
        self.set_visible(  btn_ok=True, btn_add_root=False, btn_mod_root=False)
        self.btn_ok.clicked()
        self.gui.changes_made = True

    def __on_btn_ok_clicked(self, btn):
        """Save changes made to the selected surface form, save it and move on
            to the next one."""
        root = None
        pos  = None

        if self.current_sf.root_id != self.current_root.id:
            self.current_sf.root_id = self.current_root.id
            self.current_sf.user_id = self.config.user['id']

        self.current_sf.status  = 'classified'
        self.current_sf.date    = datetime.datetime.now()

        self.wordlist.next() # This will select the next word at the top of the word list
        self.gui.changes_made = True

    def __on_btn_reject_clicked(self, btn):
        """Set the currently selected surface form's status to "rejected"."""
        if not self.current_sf:
            return

        self.current_sf.status = 'rejected'
        self.wordlist.next()
        self.gui.changes_made = True

    def __on_cmb_changed(self, combo, select_model):
        """Handler for the "changed" event of a gtk.ComboBox.

            @type  select_model: function
            @param select_model: The model that should handle the selection of
                the new model."""
        iter = combo.get_active_iter()

        if not iter is None:
            model = combo.get_model().get_value(iter, self.COL_MODEL)
            select_model(model)

    def __on_entry_activated(self, entry, text_handler):
        """Handler for the "activated" event of a gtk.Entry.

            It is used here for the child Entries of the ComboBoxEntries.
            @type  text_handler: function
            @param text_handler: The function that will handle the text entered."""
        text_handler(entry.get_text())

    def __on_entry_changed(self, entry, empty_handler):
        if len(entry.get_text()) == 0:
            empty_handler(None)

    def __on_entry_key_press_event(self, widget, event, check_func):
        if event.keyval == gtk.keysyms.Tab:
            check_func()
            return True

    def __on_match_selected(self, completion, store, iter, select_model):
        """Handler for the "match-selected" event of C{gtk.EntryCompletion}s.

            See the PyGtk API documentation for the definition of the first 3
            parameters. It should be obvious, though.
            @type  combo: gtk.ComboBoxEntry
            @param combo: The combo box for which a match was selected.
            @type  select_model: function
            @param select_model: The function to which the selected model
                should be passed to handle its selection."""
        model = store[iter][self.COL_MODEL]
        select_model(model)

        return True

    def __on_root_changed(self, ent_root, completion):
        root_text = ent_root.get_text()

        if len(root_text) == 0:
            self.select_root(None)
            return

        if len(root_text) >= completion.get_property('minimum_key_length'):
            if self.root_comp_timeout:
                gobject.source_remove(self.root_comp_timeout)
                self.root_comp_timeout = 0

            completion.set_model(self.EMPTY_COMBOMODEL)
            self.root_comp_timeout = gobject.timeout_add(self.COMPLETION_POPUP_DELAY, self._complete_root)

    def __render_pos(self, layout, cell, store, iter):
        """Cell data function that renders a part-of-speech from it's model in
            the gtk.ListStore.

            See gtk.CellLayout.set_cell_data_func()'s documentation for
            description of parameters. For the sake of practicality, not that
            "store.get_value(iter, COL_MODEL)" returns the object from the selected
            (double clicked) line (a models.PartOfSpeech model in this case)."""
        model = store.get_value(iter, self.COL_MODEL)
        cell.set_property('text', self.pos_tostring(model))

    def __render_root(self, layout, cell, store, iter):
        model = store.get_value(iter, self.COL_MODEL)
        cell.set_property('text', self.root_tostring(model))
