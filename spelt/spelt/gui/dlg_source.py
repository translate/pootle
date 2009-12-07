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

"""Contains the DlgSource (Source dialog) class."""

import gtk, gtk.glade

class DlgSource(object):
    """
    A wrapper around a gtk.Dialog that gets source information from the user.
    """

    # ACCESSORS #
    description = property(
        lambda self: self.desc_buffer.get_text( *(self.desc_buffer.get_bounds()) ),
        lambda self, txt: self.txt_desc.get_buffer().set_text(txt)
    )

    filename = property(
        lambda self: self.ent_filename.get_text(),
        lambda self, txt: self.ent_filename.set_text(txt)
    )

    name = property(
        lambda self: self.ent_name.get_text(),
        lambda self, txt: self.ent_name.set_text(txt)
    )

    # CONSTRUCTOR #
    def __init__(self, glade_xml, icon_filename):
        """Constructor.
            @type  glade_xml: gtk.glade.XML
            @param glade_xml: The Glade XML object to load widgets from.
            """
        assert isinstance(glade_xml, gtk.glade.XML)
        self.glade_xml = glade_xml
        self.icon_filename = icon_filename
        self.__init_widgets()

    # METHODS #
    def clear(self):
        self.filename    = ''
        self.name        = ''
        self.description = ''

    def has_valid_input(self):
        """Determines whether or not the dialog's fields constitute complete
            values.

            @rtype:  bool
            @return: Whether or not there is sufficiently correct information.
            """
        return len(self.filename) > 0 and len(self.name) > 0

    def run(self, filename=''):
        self.filename    = filename
        self.name        = ''
        self.description = ''

        res = self.dlg_source.run()
        self.dlg_source.hide()
        return res

    def __init_widgets(self):
        """Get and initialize widgets from the Glade object."""
        widgets = (
            'dlg_source',
            'ent_filename',
            'ent_name',
            'txt_desc'
        )

        for widget_name in widgets:
            setattr(self, widget_name, self.glade_xml.get_widget(widget_name))

        self.dlg_source.set_icon_from_file(self.icon_filename)
        self.desc_buffer = self.txt_desc.get_buffer()
