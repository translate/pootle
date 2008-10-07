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

"""Contains the DlgDBLoad class."""

import gtk, gtk.glade

from spelt.common import _
from spelt.models import LanguageDB, User

class DlgDBLoad(object):
    """
    A wrapper around a gtk.Dialog that gets configuration information from the user.
    """

    # ACCESSORS #
    def _set_langdb_path(self, txt):
        if txt is None or not txt:
            self.langdb = None
            self.ent_langdb_path.set_text('')
            return

        self.langdb = LanguageDB(filename=txt)
        self.ent_langdb_path.set_text(txt)

    langdb_path = property(
        lambda self: self.ent_langdb_path.get_text(),
        _set_langdb_path
    )

    user_name = property(
        lambda self: self.cmb_user.child.get_text(),
        lambda self, txt: self.cmb_user.child.set_text(txt)
    )

    langdb_path_confirm = property(
        lambda self: self.ent_langdb_confirm.get_text(),
        lambda self, txt: self.ent_langdb_confirm.set_text(txt)
    )

    lang_confirm = property(
        lambda self: self.ent_lang_confirm.get_text(),
        lambda self, txt: self.ent_lang_confirm.set_text(txt)
    )

    username_confirm = property(
        lambda self: self.ent_username_confirm.get_text(),
        lambda self, txt: self.ent_username_confirm.set_text(txt)
    )

    userid_confirm = property(
        lambda self: self.ent_userid_confirm.get_text(),
        lambda self, txt: self.ent_userid_confirm.set_text(txt)
    )

    # CONSTRUCTOR #
    def __init__(self, glade_xml, gui):
        """Constructor.

            @type  glade_xml: gtk.glade.XML
            @param glade_xml: The Glade XML object to load widgets from.
            """
        assert isinstance(glade_xml, gtk.glade.XML)
        self.glade_xml = glade_xml
        self.gui       = gui
        self.__init_widgets()

    # METHODS #
    def clear(self):
        self.langdb_path = None

    def get_default_user_name(self):
        # pwd is only available on UNIX
        try:
            import pwd
            import getpass
        except ImportError, _e:
            return u""
        return pwd.getpwnam(getpass.getuser())[4].split(",")[0]

    def run(self):
        start_page = 0
        if self.langdb is not None and self.langdb.filename == self.langdb_path:
            start_page = 1
            self.user_name = self.get_default_user_name()

            for u in self.langdb.users:
                self.user_store.append([u.name])
        self.notebook.set_current_page(start_page)
        res = self.dlg_dbload.run()
        self.dlg_dbload.hide()

        return res

    def __init_widgets(self):
        """Get and initialize widgets from the Glade object."""
        widgets = (
            # Main widgets
            'dlg_dbload',
            'notebook',
            # Language database page
            'ent_langdb_path',
            'btn_open',
            # User information page
            'cmb_user',
            # Confirmation page
            'ent_langdb_confirm',
            'ent_lang_confirm',
            'ent_username_confirm',
            'ent_userid_confirm',
            # Buttons in the button box at the bottom
            'btn_next', 'btn_ok_fr'
        )

        for widget_name in widgets:
            setattr(self, widget_name, self.glade_xml.get_widget(widget_name))

        self.dlg_dbload.set_icon_from_file(self.gui.icon_filename)
        self.notebook.set_show_tabs(False)
        # Connect signal handlers
        self.btn_next.connect('clicked', self.__on_next_clicked)
        self.btn_ok_fr.connect('clicked', self.__on_ok_clicked)
        self.btn_open.connect('clicked', self.__on_open_clicked)

        self.__setup_cmbe_user()

    def __setup_cmbe_user(self):
        self.user_store = gtk.ListStore(str)
        cell = gtk.CellRendererText()
        self.cmb_user.set_model(self.user_store)
        self.cmb_user.set_text_column(0)
        self.cmb_user.pack_start(cell)

        cell = gtk.CellRendererText()
        completion = gtk.EntryCompletion()
        completion.pack_start(cell)
        completion.set_model(self.user_store)
        self.cmb_user.child.set_completion(completion)

    # SIGNAL HANDLERS #
    def __on_close_clicked(self, btn):
        self.dlg_dbload.response(self.gui.RESPONSE_CANCEL)

    def __on_next_clicked(self, btn):
        if self.user_name:
            self.notebook.next_page()

            # Add the user if he's not in the database.
            usersfound = self.langdb.find(section='users', name=self.user_name)
            if not usersfound:
                self.langdb.add_user( User(name=self.user_name) )
                self.langdb.save()

            self.langdb_path_confirm = self.langdb.filename
            self.lang_confirm        = self.langdb.lang
            self.username_confirm    = self.user_name

    def __on_ok_clicked(self, btn):
        self.dlg_dbload.response(self.gui.RESPONSE_OK)

    def __on_open_clicked(self, btn):
        self.langdb_path = self.gui.get_open_filename()

        if self.langdb_path:
            try:
                self.langdb = LanguageDB(filename=self.langdb_path)
            except Exception, exc:
                self.gui.show_error(_('Error opening language database:\n\n') + str(exc))
                self.langdb_path = ''
                return
        else:
            return

        # We won't get here unless the language database was successfully opened.
        self.notebook.next_page()
        self.user_name = self.get_default_user_name()

        for u in self.langdb.users:
            self.user_store.append([u.name])
