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

"""Contains the Menu class which handles menu selections."""

import gtk, gtk.glade
import os

from spelt.common  import Configuration, _
from spelt.models  import Source, SurfaceForm
from spelt.support import openmailto

RESPONSE_OK, RESPONSE_CANCEL = range(2)

class Menu(object):
    """
    Class that handles menu options and selections.
    """

    # CONSTRUCTOR #
    def __init__(self, glade_xml, gui):
        """Constructor.
            @type  glade_xml: gtk.glade.XML
            @param glade_xml: The Glade XML object to load widgets from.
            """
        assert isinstance(glade_xml, gtk.glade.XML)
        assert not gui is None

        self.config    = Configuration()
        self.glade_xml = glade_xml
        self.gui       = gui

        self.__init_widgets()

    # METHODS #
    def create_source_from_file(self, filename):
        """Create a model.Source for the given filename."""
        fname      = os.path.split(filename)[1]
        dlg_source = self.gui.dlg_source

        dlg_source.clear()

        if dlg_source.run(fname) == RESPONSE_CANCEL:
            return None

        while not dlg_source.has_valid_input():
            self.gui.show_error(
                _('Please fill in a name for the source'),
                title='Incomplete information'
            )
            if dlg_source.run(fname) == RESPONSE_CANCEL:
                return None

        name = dlg_source.name
        desc = dlg_source.description
        import_user_id = self.config.user['id']

        src = Source(
            name           = name,
            filename       = fname,
            desc           = desc,
            import_user_id = import_user_id
        )
        return src

    def __init_widgets(self):
        """Get and initialize widgets from the Glade object."""
        self.widgets = (
            # File menu
            'mnu_open',
            'mnu_save',
            'mnu_saveas',
            'mnu_quit',
            # Database menu
            'mnu_emaildb',
            'mnu_import',
            #'mnu_roots',   # Removed
            # Help menu
            'mnu_about'
        )

        for widget_name in self.widgets:
            widget = self.glade_xml.get_widget(widget_name)
            widget.connect('activate', self.__on_item_activated)
            setattr(self, widget_name, widget)

    # SIGNAL HANDLERS #
    def handler_open(self):
        """Display an "Open" dialog and try to open the file as a language database."""
        if self.gui.changes_made and self.gui.prompt(
                    text=_('Save language database changes?'),
                    title=_('The language database you are\ncurrently working with has changed.\n\nSave changes?')
                ):
            self.config.current_database.save()

        filename = self.gui.get_open_filename()
        if filename is None:
            return

        if not os.path.exists(filename):
            self.gui.show_error(_('File does not exist: "%s"') % (filename))
            return

        # Get and save new user information
        self.gui.load_langdb(filename)

        # Ask the main GUI object to reload the database everywhere...
        self.gui.reload_database()

    def handler_save(self):
        """Save the contents of the current open database."""
        try:
            self.config.current_database.save()
        except Exception, exc:
            self.gui.show_error(text=str(exc), title=_('Error saving database!'))
            print _( 'Error saving database: "%s"') % (exc)
            return

    def handler_saveas(self):
        """Display a "Save as" dialog and try to save the language database to
            the selected file."""
        filename = self.gui.get_save_filename()
        if filename is None:
            return

        if not filename.endswith('.xldb'):
            filename = filename + '.xldb'

        if os.path.exists(filename) and not self.gui.prompt(_( 'File "%s" already exists.\n\nOverwrite?' % (filename) )):
            return

        try:
            self.config.current_database.save(filename)
        except Exception, exc:
            self.gui.show_error(text=str(exc), title=_('Error saving database to file %s') % (filename))
            print _('Error saving database to %s: %s') % (filename, exc)

    def handler_quit(self):
        """Quit the application after confirmation."""
        self.gui.quit()

    def handler_emaildb(self):
        db = self.config.current_database

        try:
            db.save()
        except Exception, exc:
            self.gui.show_error(_('Unable to save database before e-mailing!'))
            print _('Unable to save database before e-mailing: "%s"') % (exc)
            return

        subj = _('Language database: ') + str(db).decode('utf-8')
        openmailto.mailto('', subject=subj, attach=db.filename)

    def handler_import(self):
        """Import words from a text file."""
        db = self.config.current_database
        user_id = self.config.user['id']
        filename = self.gui.get_open_filename(_('Open word list...'))

        if filename is None:
            return

        src = self.create_source_from_file(filename)
        if src is None:
            return

        db.import_source(src, filename=filename)
        self.gui.reload_database()

    def handler_about(self):
        """Shows the "About" dialog. See spelt.gui.GUI.__create_dialogs()."""
        self.gui.dlg_about.run()
        self.gui.dlg_about.hide()

    def __on_item_activated(self, menu_item):
        """Signal handler for all menu items."""
        if not menu_item.name.startswith('mnu_'):
            return

        # The following looks up the appropriate signal handler for a menu item
        # by changing the leading 'mnu_' of the menu item's name to 'handler_'.
        # ie. 'mnu_save' becomes 'handler_save', which is called with no arguments.
        handler_name = 'handler_%s' % (menu_item.name[4:])
        getattr(self, handler_name)()
