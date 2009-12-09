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

from virtaal.common import pan_app
from virtaal.views import BaseView


class LanguageAddDialog(object):
    """
    Represents and manages an instance of the dialog used for adding a language.
    """

    # INITIALIZERS #
    def __init__(self, parent=None):
        super(LanguageAddDialog, self).__init__()

        self.gladefilename, self.gui = BaseView.load_glade_file(
            ["virtaal", "virtaal.glade"],
            root='LanguageAdder',
            domain='virtaal'
        )

        self._get_widgets()
        if isinstance(parent, gtk.Widget):
            self.dialog.set_transient_for(parent)
            self.dialog.set_icon(parent.get_toplevel().get_icon())

    def _get_widgets(self):
        """Load the Glade file and get the widgets we would like to use."""
        widget_names = ('btn_add_ok', 'ent_langname', 'ent_langcode', 'sbtn_nplurals', 'ent_plural')

        for name in widget_names:
            setattr(self, name, self.gui.get_widget(name))

        self.dialog = self.gui.get_widget('LanguageAdder')


    # ACCESSORS #
    def _get_langname(self):
        return self.ent_langname.get_text()
    def _set_langname(self, value):
        self.ent_langname.set_text(value)
    langname = property(_get_langname, _set_langname)

    def _get_langcode(self):
        return self.ent_langcode.get_text()
    def _set_langcode(self, value):
        self.ent_langcode.set_text(value)
    langcode = property(_get_langcode, _set_langcode)

    def _get_nplurals(self):
        return int(self.sbtn_nplurals.get_value())
    def _set_nplurals(self):
        self.sbtn_nplurals.set_value(int(value))
    nplurals = property(_get_nplurals, _set_nplurals)

    def _get_plural(self):
        return self.ent_plural.get_text()
    def _set_plural(self, value):
        self.ent_plural.set_text(value)
    plural = property(_get_plural, _set_plural)


    # METHODS #
    def clear(self):
        for entry in (self.ent_langname, self.ent_langcode, self.ent_plural):
            entry.set_text('')
        self.sbtn_nplurals.set_value(0)

    def run(self, clear=True):
        if clear:
            self.clear()
        response = self.dialog.run() == gtk.RESPONSE_OK
        self.dialog.hide()
        return response

    def check_input_sanity(self):
        # TODO: Add more sanity checks
        code = self.langcode
        try:
            ascii_code = unicode(code, 'ascii')
        except UnicodeDecodeError:
            return _('Language code must be an ASCII string.')

        if len(code) < 2:
            return _('Language code must be at least 2 characters long.')

        return ''
