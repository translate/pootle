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
from translate.storage.placeables import general, StringElem, parse as parse_placeables

from virtaal.common import pan_app, GObjectWrapper
from virtaal.views import placeablesguiinfo

from basecontroller import BaseController


class PlaceablesController(BaseController):
    """Basic controller for placeable-related logic."""

    __gtype_name__ = 'PlaceablesController'
    __gsignals__ = {
        'parsers-changed': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, tuple()),
    }

    parsers = []
    """The list of parsers that should be used by the main placeables C{parse()}
    function.
    @see translate.storage.placeables.parse"""

    # INITIALIZERS #
    def __init__(self, main_controller):
        GObjectWrapper.__init__(self)

        self.main_controller = main_controller
        self.main_controller.placeables_controller = self
        self._init_parsers()
        self._init_parser_descriptions()
        self._init_notarget_list()

        self.main_controller.view.main_window.connect('style-set', self._on_style_set)
        self.main_controller.connect('quit', self._on_quit)

    def _init_notarget_list(self):
        self.non_target_placeables = [
            general.AltAttrPlaceable,
            general.CamelCasePlaceable,
            general.CapsPlaceable,
            general.EmailPlaceable,
            general.FilePlaceable,
            general.PunctuationPlaceable,
            general.UrlPlaceable,
        ]

    def _init_parsers(self):
        disabled = [name for name, state in pan_app.settings.placeable_state.items() if state.lower() == 'disabled']

        self.parsers = []
        for parser in general.parsers:
            classname = parser.im_self.__name__.lower()
            if classname in disabled:
                continue
            self.add_parsers(parser)

    def _init_parser_descriptions(self):
        self.parser_info = {}

        # Test for presence of parser classes by hand
        self.parser_info[general.CamelCasePlaceable.parse] = (
            #l10n: See http://en.wikipedia.org/wiki/CamelCase
            _('CamelCase'),
            _('Words with internal capitalisation, such as some brand names and WikiWords')
        )
        self.parser_info[general.CapsPlaceable.parse] = (
            _('Capitals'),
            #l10n: this refers to "UPPERCASE" / "CAPITAL" letters
            _('Words containing uppercase letters only')
        )
        self.parser_info[general.OptionPlaceable.parse] = (
            _('Command Line Options'),
            _('Application command line options, such as --help, -h and -I')
        )
        self.parser_info[general.EmailPlaceable.parse] = (
            _('E-mail'),
            _('E-mail addresses')
        )
        self.parser_info[general.FilePlaceable.parse] = (
            _('File Names'),
            _('Paths referring to file locations')
        )
        self.parser_info[general.FormattingPlaceable.parse] = (
            _('Placeholders (printf)'),
            _('Placeholders used in "printf" strings')
        )
        self.parser_info[general.PythonFormattingPlaceable.parse] = (
            _('Placeholders (Python)'),
            _('Placeholders in Python strings')
        )
        self.parser_info[general.JavaMessageFormatPlaceable.parse] = (
            _('Placeholders (Java)'),
            _('Placeholders in Java strings')
        )
        self.parser_info[general.QtFormattingPlaceable.parse] = (
            _('Placeholders (Qt)'),
            _('Placeholders in Qt strings')
        )
        self.parser_info[general.NumberPlaceable.parse] = (
            _('Numbers'),
            #l10n: 'decimal fractions' refer to numbers like 0.2 or 499,99
            _('Integer numbers and decimal fractions')
        )
        self.parser_info[general.PunctuationPlaceable.parse] = (
            _('Punctuation'),
            _('Symbols and less frequently used punctuation marks')
        )
        self.parser_info[general.UrlPlaceable.parse] = (
            _('URLs'),
            _('URLs, hostnames and IP addresses')
        )
        self.parser_info[general.XMLEntityPlaceable.parse] = (
            #l10n: see http://en.wikipedia.org/wiki/Character_entity_reference
            _('XML Entities'),
            _('Entity references, such as &amp; and &#169;')
        )
        self.parser_info[general.XMLTagPlaceable.parse] = (
            _('XML Tags'),
            _('XML tags, such as <b> and </i>')
        )
        # This code should eventually be used to add the SpacesPlaceable, but
        # it is not working well yet. We add the strings for translation so
        # that we won't need to break the string freeze later when it works.
#        self.parser_info[general.AltAttrPlaceable.parse] = (
#            _('"alt" Attributes'),
#            _('Placeable for "alt" attributes (as found in HTML)')
#        )
#        self.parser_info[general.SpacesPlaceable.parse] = (
#            _('Spaces'),
#            _('Double spaces and spaces in unexpected positions')
#        )

        _('Spaces'),
        _('Double spaces and spaces in unexpected positions')
        _('"alt" Attributes'),
        _('Placeable for "alt" attributes (as found in HTML)')


    # METHODS #
    def add_parsers(self, *newparsers):
        """Add the specified parsers to the list of placeables parser functions."""
        if [f for f in newparsers if not callable(f)]:
            raise TypeError('newparsers may only contain callable objects.')

        sortedparsers = []

        # First add parsers from general.parsers in order
        for parser in general.parsers:
            if parser in (self.parsers + list(newparsers)):
                sortedparsers.append(parser)
        # Add parsers not in general.parsers
        for parser in newparsers:
            if parser not in general.parsers:
                sortedparsers.append(parser)

        self.parsers = sortedparsers
        self.emit('parsers-changed')

    def apply_parsers(self, elems, parsers=None):
        """Apply all selected placeable parsers to the list of string elements
            given.

            @param elems: The list of C{StringElem}s to apply the parsers to."""
        if not isinstance(elems, list) and isinstance(elems, StringElem):
            elems = [elems]

        if parsers is None:
            parsers = self.parsers

        for elem in elems:
            leaves = elem.flatten()
            for leaf in leaves:
                parsed = parse_placeables(leaf, parsers)
                if isinstance(leaf, (str, unicode)) and parsed != StringElem(leaf):
                    parent = elem.get_parent_elem(leaf)
                    if parent is not None:
                        parent.sub[parent.sub.index(leaf)] = StringElem(parsed)
        return elems

    def get_parsers_for_textbox(self, textbox):
        """Get the parsers that should be applied to the given text box.
            This is intended for use by C{TextBox} to supply it with appropriate
            parsers, based on whether the text box is used for source- or target
            text."""
        if textbox in self.main_controller.unit_controller.view.targets:
            tgt_parsers = []
            return [p for p in self.parsers if p.im_self not in self.non_target_placeables]
        return self.parsers

    def get_gui_info(self, placeable):
        """Get an appropriate C{StringElemGUI} or sub-class instance based on
        the type of C{placeable}. The mapping between placeables classes and
        GUI info classes is defined in
        L{virtaal.views.placeablesguiinfo.element_gui_map}."""
        if not isinstance(placeable, StringElem):
            raise ValueError('placeable must be a StringElem.')
        for plac_type, info_type in placeablesguiinfo.element_gui_map:
            if isinstance(placeable, plac_type):
                return info_type
        return placeablesguiinfo.StringElemGUI

    def remove_parsers(self, *parsers):
        changed = False
        for p in parsers:
            if p in self.parsers:
                self.parsers.remove(p)
                changed = True
        if changed:
            self.emit('parsers-changed')


    # EVENT HANDLERS #
    def _on_style_set(self, widget, prev_style):
        import gtk
        placeablesguiinfo.StringElemGUI.bg = widget.style.base[gtk.STATE_NORMAL].to_string()
        placeablesguiinfo.StringElemGUI.fg = widget.style.fg[gtk.STATE_NORMAL].to_string()
        placeablesguiinfo.UrlGUI.bg = widget.style.base[gtk.STATE_NORMAL].to_string()

        # Refresh text boxes' colours
        unitview = self.main_controller.unit_controller.view
        for textbox in unitview.sources + unitview.targets:
            if textbox.props.visible:
                textbox.refresh()

    def _on_quit(self, main_ctrlr):
        for parser in general.parsers:
            classname = parser.im_self.__name__
            enabled = parser in self.parsers
            if classname in pan_app.settings.placeable_state or not enabled:
                pan_app.settings.placeable_state[classname.lower()] = enabled and 'enabled' or 'disabled'
