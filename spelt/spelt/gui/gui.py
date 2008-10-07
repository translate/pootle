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

"""Contains the main GUI class."""

import gtk, gtk.glade, os
from xml.sax.saxutils import escape

from spelt.common  import Configuration, __version__, _
from spelt.models  import LanguageDB, User
from spelt.support import openmailto

from spelt.gui.dlg_dbload import DlgDBLoad
from spelt.gui.dlg_source import DlgSource
from spelt.gui.edit_area  import EditArea
from spelt.gui.menu       import Menu
from spelt.gui.wordlist   import WordList

LICENSE = """This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Library General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, see <http://www.gnu.org/licenses/>."""

class GUI(object):
    """The main GUI class. Also contains commonly used functionality."""

    RESPONSE_OK, RESPONSE_CANCEL = range(2)

    # CONSTRUCTOR #
    def __init__(self, dbfilename, glade_filename, icon_filename, splash_logo):
        self.glade = gtk.glade.XML(glade_filename)
        self.config = Configuration()
        self.changes_made = False
        self.dbfilename = dbfilename
        self.icon_filename = icon_filename

        # Main window
        self.main_window = self.glade.get_widget('wnd_main')
        self.main_window.connect('destroy', lambda *w: gtk.main_quit())
        self.main_window.set_icon_from_file(self.icon_filename)

        self.__create_dialogs()

        self.splash = self.glade.get_widget('wnd_splash')
        self.splash.show_all()
        self.glade.get_widget('img_splash').set_from_file(splash_logo)

    def __del__(self):
        """Destructor."""
        self.open_chooser.destroy()
        self.save_chooser.destroy()

    # METHODS #
    def __create_dialogs(self):
        self.open_chooser = gtk.FileChooserDialog(
            title=_('Select language database to open'),
            action=gtk.FILE_CHOOSER_ACTION_OPEN,
            buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN,gtk.RESPONSE_OK)
        )

        self.save_chooser = gtk.FileChooserDialog(
            title=_('Save as...'),
            action=gtk.FILE_CHOOSER_ACTION_SAVE,
            buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN,gtk.RESPONSE_OK)
        )

        all_filter = gtk.FileFilter()
        all_filter.set_name(_('All files'))
        all_filter.add_pattern('*')

        langdb_filter = gtk.FileFilter()
        langdb_filter.set_name(_('Language Database'))
        langdb_filter.add_mime_type('text/xml')
        langdb_filter.add_pattern('*.' + LanguageDB.FILE_EXTENSION)

        self.open_chooser.add_filter(all_filter)
        self.open_chooser.add_filter(langdb_filter)
        self.save_chooser.add_filter(langdb_filter)
        self.save_chooser.add_filter(all_filter)

        # Message dialog
        self.dlg_error = gtk.MessageDialog(
            parent=self.main_window,
            flags=gtk.DIALOG_MODAL,
            type=gtk.MESSAGE_ERROR,
            buttons=gtk.BUTTONS_OK,
            message_format=''
        )

        self.dlg_info = gtk.MessageDialog(
            parent=self.main_window,
            flags=gtk.DIALOG_MODAL,
            type=gtk.MESSAGE_INFO,
            buttons=gtk.BUTTONS_OK,
            message_format=''
        )

        self.dlg_prompt = gtk.MessageDialog(
            parent=self.main_window,
            flags=gtk.DIALOG_MODAL,
            type=gtk.MESSAGE_QUESTION,
            buttons=gtk.BUTTONS_YES_NO,
            message_format=''
        )

        # Source dialog wrapper
        self.dlg_source = DlgSource(self.glade, self.icon_filename)
        # LanguageDB loading dialog
        self.dlg_dbload = DlgDBLoad(self.glade, self)

        # About dialog
        def on_about_url(dialog, uri, data):
            if data == "mail":
                openmailto.mailto(uri)
            elif data == "url":
                openmailto.open(uri)

        self.dlg_about = gtk.AboutDialog()
        gtk.about_dialog_set_url_hook(on_about_url, "url")
        gtk.about_dialog_set_email_hook(on_about_url, "mail")
        self.dlg_about.set_name("Spelt")
        self.dlg_about.set_version(__version__)
        self.dlg_about.set_copyright(_("© Copyright 2007-2008 Zuza Software Foundation"))
        self.dlg_about.set_comments(
            _("A tool to categorize words from a language database according to its root.")
        )
        self.dlg_about.set_license(LICENSE)
        self.dlg_about.set_website("http://translate.sourceforge.net/wiki/spelt/index")
        self.dlg_about.set_website_label(_("Spelt website"))
        self.dlg_about.set_authors(["Walter Leibbrandt <walter@translate.org.za>"])
        self.dlg_about.set_translator_credits(_("translator-credits"))
        self.dlg_about.set_icon(self.main_window.get_icon())
        # XXX entries that we may want to add (commented out):
        #self.dlg_about.set_logo()
        self.dlg_about.set_documenters([
            "Friedel Wolff <friedel@translate.org.za>",
            "Wynand Winterbach <wynand@translate.org.za>",
            "Walter Leibbrandt <walter@translate.org.za>"
        ])
        #self.dlg_about.set_artists()

        # Set icon on all dialogs
        for dlg in (
            self.open_chooser, self.save_chooser, self.dlg_error,
            self.dlg_info, self.dlg_prompt, self.dlg_about
            ):
            dlg.set_icon_from_file(self.icon_filename)

    def check_work_done(self, sf):
        if sf is None:
            self.show_info(_('All work done!'))

    def get_open_filename(self, title=_('Select language database to open')):
        """Display an "Open" dialog and return the selected file.
            @rtype  str
            @return The filename selected in the "Open" dialog. None if the selection was cancelled."""
        self.open_chooser.set_title(title)
        res = self.open_chooser.run()
        self.open_chooser.hide()

        if res != gtk.RESPONSE_OK:
            return None

        return self.open_chooser.get_filename()

    def get_save_filename(self, title=_('Save...')):
        """Display an "Save" dialog and return the selected file.
            @rtype  str
            @return The filename selected in the "Save" dialog. None if the selection was cancelled."""
        self.save_chooser.set_title(title)
        res = self.save_chooser.run()
        self.save_chooser.hide()

        if res != gtk.RESPONSE_OK:
            return None

        return self.save_chooser.get_filename()

    def load_langdb(self, langdb_path=None):
        self.dlg_dbload.clear()

        if langdb_path is not None and os.path.exists(langdb_path):
            self.dlg_dbload.langdb_path = langdb_path

        if self.dlg_dbload.run() != self.RESPONSE_OK:
            return False

        self.config.current_database = db = self.dlg_dbload.langdb

        user = db.find(section='users', name=self.dlg_dbload.user_name)[0]
        self.config.user['id']                  = user.id
        self.config.general['last_langdb_path'] = os.path.abspath(db.filename)
        self.config.save()

        fn = os.path.split(db.filename)[-1]
        self.main_window.set_title('Spelt - %(langdb_filename)s' % {'langdb_filename': fn})

        return True

    def show(self):
        # Load last database
        db = LanguageDB(lang='')
        self.config.current_database = db

        if self.dbfilename:
            self.dbfilename = os.path.abspath(self.dbfilename)

        if os.path.exists(self.dbfilename) and self.dbfilename != self.config.general['last_langdb_path']:
            if not self.load_langdb(self.dbfilename):
                self.quit()
        elif os.path.exists(self.config.general['last_langdb_path']):
            db.load(self.config.general['last_langdb_path'])
            fn = os.path.split(db.filename)[-1]
            self.main_window.set_title('Spelt - %(langdb_filename)s' % {'langdb_filename': fn})
        else:
            # If we couldn't find the previous database, act as if this is a
            # first run.
            if not self.load_langdb():
                self.quit()

        self.splash.hide()

        self.menu      = Menu(self.glade, gui=self)
        self.word_list = WordList(self.glade, langdb=db, gui=self)
        self.edit_area = EditArea(self.glade, self.word_list, langdb=db, gui=self)

        self.word_list.word_selected_handlers.append(self.check_work_done)

        # Check if this is the first time the program is run
        if self.config.user['id'] == 0:
            if not self.load_langdb():
                self.quit()

        self.main_window.show_all()
        self.reload_database()

    def show_error(self, text, title=_('Error!')):
        self.dlg_error.set_markup(escape(text))
        self.dlg_error.set_title(title)
        self.dlg_error.run()
        self.dlg_error.hide()

    def show_info(self, text, title=_('Information')):
        self.dlg_info.set_markup(escape(text))
        self.dlg_info.set_title(title)
        self.dlg_info.run()
        self.dlg_info.hide()

    def prompt(self, text, title=_('Prompt')):
        self.dlg_prompt.set_markup(escape(text))
        self.dlg_prompt.set_title(title)
        res = self.dlg_prompt.run()
        self.dlg_prompt.hide()

        return res == gtk.RESPONSE_YES

    def quit(self):
        if self.changes_made and self.prompt(
                    text=_('There are unsaved changes.\n\nSave before exiting?'),
                    title=_('Save changes?')
                ):
            self.langdb.save()

        self.config.save()
        gtk.main_quit()

    def reload_database(self):
        """Have all sub-components reload its database information."""
        db = self.config.current_database
        self.edit_area.refresh(langdb=db)
        self.word_list.refresh(langdb=db)
