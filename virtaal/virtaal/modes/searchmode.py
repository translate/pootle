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

import gobject
import gtk
import gtk.gdk
import logging
import re
from translate.tools.pogrep import GrepFilter

from virtaal.controllers import Cursor

from basemode import BaseMode
from virtaal.views import markup


class SearchMode(BaseMode):
    """Search mode - Includes only units matching the given search term."""

    display_name = _("Search")
    name = 'Search'
    widgets = []

    MAX_RESULTS = 100000
    SEARCH_DELAY = 500

    # INITIALIZERS #
    def __init__(self, controller):
        """Constructor.
            @type  controller: virtaal.controllers.ModeController
            @param controller: The ModeController that managing program modes."""
        self.controller = controller
        self.unitview = controller.main_controller.unit_controller.view

        self._create_widgets()
        self._setup_key_bindings()

        self.matches = []
        self.select_first_match = True
        self._search_timeout = 0
        self._unit_modified_id = 0

    def _create_widgets(self):
        # Widgets for search functionality (in first row)
        self.ent_search = gtk.Entry()
        self.ent_search.connect('changed', self._on_search_text_changed)
        self.ent_search.connect('activate', self._on_entry_activate)
        self.btn_search = gtk.Button(_('Search'))
        self.btn_search.connect('clicked', self._on_search_clicked)
        self.chk_casesensitive = gtk.CheckButton(_('_Case sensitive'))
        self.chk_casesensitive.connect('toggled', self._refresh_proxy)
        # l10n: To read about what regular expressions are, see
        # http://en.wikipedia.org/wiki/Regular_expression
        self.chk_regex = gtk.CheckButton(_("_Regular expression"))
        self.chk_regex.connect('toggled', self._refresh_proxy)

        # Widgets for replace (second row)
        # l10n: This text label shows in front of the text box where the replacement
        # text is typed. Keep in mind that the text box will appear after this text.
        # If this sentence construction is hard to use, consdider translating this as
        # "Replacement"
        self.lbl_replace = gtk.Label(_('Replace with'))
        self.ent_replace = gtk.Entry()
        # l10n: Button text
        self.btn_replace = gtk.Button(_('Replace'))
        self.btn_replace.connect('clicked', self._on_replace_clicked)
        # l10n: Check box
        self.chk_replace_all = gtk.CheckButton(_('Replace _All'))

        self.widgets = [
            self.ent_search, self.btn_search, self.chk_casesensitive, self.chk_regex,
            self.lbl_replace, self.ent_replace, self.btn_replace, self.chk_replace_all
        ]

        self.default_base = gtk.widget_get_default_style().base[gtk.STATE_NORMAL]
        self.default_text = gtk.widget_get_default_style().text[gtk.STATE_NORMAL]

    def _setup_key_bindings(self):
        gtk.accel_map_add_entry("<Virtaal>/Edit/Search", gtk.keysyms.F3, 0)
        gtk.accel_map_add_entry("<Virtaal>/Edit/Search Ctrl+F", gtk.keysyms.F, gtk.gdk.CONTROL_MASK)
        gtk.accel_map_add_entry("<Virtaal>/Edit/Search: Next", gtk.keysyms.G, gtk.gdk.CONTROL_MASK)
        gtk.accel_map_add_entry("<Virtaal>/Edit/Search: Previous", gtk.keysyms.G, gtk.gdk.CONTROL_MASK | gtk.gdk.SHIFT_MASK)

        self.accel_group = gtk.AccelGroup()
        self.accel_group.connect_by_path("<Virtaal>/Edit/Search", self._on_start_search)
        self.accel_group.connect_by_path("<Virtaal>/Edit/Search Ctrl+F", self._on_start_search)
        self.accel_group.connect_by_path("<Virtaal>/Edit/Search: Next", self._on_search_next)
        self.accel_group.connect_by_path("<Virtaal>/Edit/Search: Previous", self._on_search_prev)

        self.controller.main_controller.view.add_accel_group(self.accel_group)


    # METHODS #
    def selected(self):
        # XXX: Assumption: This method is called when a new file is loaded and that is
        #      why we keep a reference to the store's cursor.
        self.storecursor = self.controller.main_controller.store_controller.cursor
        if not self.storecursor or not self.storecursor.model:
            return

        self._add_widgets()
        self._connect_highlighting()
        self._connect_textboxes()
        if not self.ent_search.get_text():
            self.storecursor.indices = self.storecursor.model.stats['total']
        else:
            self.update_search()

        curpos = self.ent_search.props.cursor_position
        def grab_focus():
            self.ent_search.grab_focus()
            self.ent_search.set_position(curpos)
            return False

        # FIXME: The following line is a VERY UGLY HACK, but at least it works.
        gobject.timeout_add(100, grab_focus)

    def select_match(self, match):
        """Select the specified match in the GUI."""
        main_controller = self.controller.main_controller
        main_controller.select_unit(match.unit)
        view = main_controller.unit_controller.view

        if match.part == 'target':
            textbox = view.targets[match.part_n]
        elif match.part == 'source':
            textbox = view.sources[match.part_n]

        if not textbox:
            return False

        # Wait for SearchMode to finish with its highlighting and stuff, and then we do...
        def select_match_text():
            textbox.grab_focus()
            buff = textbox.buffer
            buffstr = textbox.get_text()
            unescaped = markup.unescape(buffstr)

            start, end = self._escaped_indexes(unescaped, match.start, match.end)
            if hasattr(textbox.elem, 'gui_info'):
                start = textbox.elem.gui_info.tree_to_gui_index(start)
                end = textbox.elem.gui_info.tree_to_gui_index(end)
            start_iter = buff.get_iter_at_offset(start)
            end_iter = buff.get_iter_at_offset(end)

            buff.select_range(end_iter, start_iter)
            return False

        # TODO: Implement for 'notes' and 'locations' parts
        gobject.idle_add(select_match_text)

    def replace_match(self, match, replace_str):
        main_controller = self.controller.main_controller
        unit_controller = main_controller.unit_controller
        # Using unit_controller directly is a hack to make sure that the replacement changes are immediately displayed.
        if match.part != 'target':
            return

        if unit_controller is None:
            if match.unit.hasplural():
                string_n = match.unit.target.strings[match.part_n]
                strings[match.part_n] = string_n[:match.start] + replace_str + string_n[match.end:]
                match.unit.target = strings
            else:
                rstring = match.unit.target
                rstring = rstring[:match.start] + replace_str + rstring[match.end:]
                match.unit.target = rstring
        else:
            main_controller.select_unit(match.unit)
            rstring = unit_controller.get_unit_target(match.part_n)
            unit_controller.set_unit_target(match.part_n, rstring[:match.start] + replace_str + rstring[match.end:])

    def update_search(self):
        self.filter = GrepFilter(
            searchstring=unicode(self.ent_search.get_text()),
            searchparts=('source', 'target'),
            ignorecase=not self.chk_casesensitive.get_active(),
            useregexp=self.chk_regex.get_active(),
            max_matches=self.MAX_RESULTS
        )
        store_units = self.storecursor.model.get_units()
        self.matches, indexes = self.filter.getmatches(store_units)
        self.matchcursor = Cursor(self.matches, range(len(self.matches)))

        logging.debug('Search text: %s (%d matches)' % (self.ent_search.get_text(), len(indexes)))

        if indexes:
            self.ent_search.modify_base(gtk.STATE_NORMAL, self.default_base)
            self.ent_search.modify_text(gtk.STATE_NORMAL, self.default_text)

            self.storecursor.indices = indexes
            # Select initial match for in the current unit.
            match_index = 0
            selected_unit = self.storecursor.model[self.storecursor.index]
            for match in self.matches:
                if match.unit is selected_unit:
                    break
                match_index += 1
            self.matchcursor.index = match_index
        else:
            if self.ent_search.get_text():
                self.ent_search.modify_base(gtk.STATE_NORMAL, gtk.gdk.color_parse('#f66'))
                self.ent_search.modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse('#fff'))
            else:
                self.ent_search.modify_base(gtk.STATE_NORMAL, self.default_base)
                self.ent_search.modify_text(gtk.STATE_NORMAL, self.default_text)

            self.filter.re_search = None
            # Act like the "Default" mode...
            self.storecursor.indices = self.storecursor.model.stats['total']
        self._highlight_matches()

        curpos = self.ent_search.props.cursor_position
        def grabfocus():
            self.ent_search.grab_focus()
            self.ent_search.set_position(curpos)
            return False
        gobject.idle_add(grabfocus)

    def unselected(self):
        # TODO: Unhightlight the previously selected unit
        if hasattr(self, '_signalid_cursor_changed'):
            self.storecursor.disconnect(self._signalid_cursor_changed)

        if hasattr(self, '_textbox_signals'):
            for textbox, signal_id in self._textbox_signals.items():
                textbox.disconnect(signal_id)

        if self._unit_modified_id:
            self.controller.main_controller.unit_controller.disconnect(self._unit_modified_id)
            self._unit_modified_id = 0

        self.matches = []

    def _add_widgets(self):
        table = self.controller.view.mode_box

        xoptions = gtk.FILL
        table.attach(self.ent_search, 2, 3, 0, 1, xoptions=xoptions)
        table.attach(self.btn_search, 3, 4, 0, 1, xoptions=xoptions)
        table.attach(self.chk_casesensitive, 4, 5, 0, 1, xoptions=xoptions)
        table.attach(self.chk_regex, 5, 6, 0, 1, xoptions=xoptions)

        table.attach(self.lbl_replace, 1, 2, 1, 2, xoptions=xoptions)
        table.attach(self.ent_replace, 2, 3, 1, 2, xoptions=xoptions)
        table.attach(self.btn_replace, 3, 4, 1, 2, xoptions=xoptions)
        table.attach(self.chk_replace_all, 4, 5, 1, 2, xoptions=xoptions)

        table.show_all()

    def _connect_highlighting(self):
        self._signalid_cursor_changed = self.storecursor.connect('cursor-changed', self._on_cursor_changed)

    def _connect_textboxes(self):
        self._textbox_signals = {}
        for textbox in self.unitview.sources + self.unitview.targets:
            self._textbox_signals[textbox] = textbox.connect(
                'refreshed', self._on_textbox_refreshed
            )

    def _get_matches_for_unit(self, unit):
        return [match for match in self.matches if match.unit is unit]

    def _get_unit_matches_dict(self):
        d = {}
        for match in self.matches:
            if match.unit not in d:
                d[match.unit] = []
            d[match.unit].append(match)
        return d

    def _escaped_indexes(self, unescaped, start, end):
        """Returns the indexes of start and end in the escaped version of the
        given unescaped string."""
        # Escaping might mean that the indexes should be offset, so we
        # test to see if escaping comes into play. The unescaped version
        # will help us calculate how much we need to adjust.
        leading_segment = unescaped[:end]
        lines = leading_segment.count(u'\n') + leading_segment.count(u'\t')
        start = start + lines * 2
        end = end + lines * 2
        return (start, end)

    def _highlight_matches(self):
        if not hasattr(self, 'filter') or not hasattr(self.filter, 're_search') or self.filter.re_search is None:
            return

        for textbox in self.unitview.sources + self.unitview.targets:
            self._highlight_textbox_matches(textbox)

    def _get_matches_for_textbox(self, textbox):
        if textbox.role == 'source':
            textbox_n = self.unitview.sources.index(textbox)
        elif textbox.role == 'target':
            textbox_n = self.unitview.targets.index(textbox)
        else:
            raise ValueError('Could not find text box in sources or targets: %s' % (textbox))
        return [
            m for m in self.matches
            if m.unit is self.unitview.unit and \
                m.part == textbox.role and \
                m.part_n == textbox_n
        ]

    def _highlight_textbox_matches(self, textbox):
        buff = textbox.buffer
        buffstr = textbox.get_text()
        unescaped = markup.unescape(buffstr)

        # Make sure the 'search_highlight' tag in the textbox's tag table
        # is "fresh".
        try:
            tagtable = buff.get_tag_table()
            tag = tagtable.lookup('search_highlight')
            if tag:
                tagtable.remove(tag)
            tagtable.add(self._make_highlight_tag())
        except ValueError:
            pass

        select_iters = []
        for match in self._get_matches_for_textbox(textbox):
            start, end = self._escaped_indexes(unescaped, match.start, match.end)
            if hasattr(textbox.elem, 'gui_info'):
                start = textbox.elem.gui_info.tree_to_gui_index(start)
                end   = textbox.elem.gui_info.tree_to_gui_index(end)
            start_iter, end_iter = buff.get_iter_at_offset(start), buff.get_iter_at_offset(end)
            buff.apply_tag_by_name('search_highlight', start_iter, end_iter)

            if textbox.role == 'target' and not select_iters and self.select_first_match:
                select_iters = [start_iter, end_iter]

        if select_iters:
            buff.select_range(select_iters[1], select_iters[0])

    def _make_highlight_tag(self):
        tag = gtk.TextTag(name='search_highlight')
        tag.set_property('background', 'yellow')
        tag.set_property('foreground', 'black')
        return tag

    def _move_match(self, offset):
        if self.controller.current_mode is not self:
            return

        if getattr(self, 'matchcursor', None) is None:
            self.update_search()
            self._move_match(offset)
            return

        old_match_index = self.matchcursor.index
        if not self.matches or old_match_index != self.matchcursor.index:
            self.update_search()
            return

        self.matchcursor.move(offset)
        self.select_match(self.matches[self.matchcursor.index])

    def _replace_all(self):
        self.controller.main_controller.undo_controller.record_start()

        repl_str = self.ent_replace.get_text()
        unit_matches = self._get_unit_matches_dict()

        for unit, matches in unit_matches.items():
            for match in reversed(matches):
                self.replace_match(match, repl_str)

        self.controller.main_controller.undo_controller.record_stop()
        self.update_search()


    # EVENT HANDLERS #
    def _on_entry_activate(self, entry):
        self.update_search()
        self._move_match(0) # Select the current match.

    def _on_cursor_changed(self, cursor):
        assert cursor is self.storecursor

        unitcont = self.controller.main_controller.unit_controller
        if self._unit_modified_id:
            unitcont.disconnect(self._unit_modified_id)
        self._unit_modified_id = unitcont.connect('unit-modified', self._on_unit_modified)
        self._highlight_matches()

    def _on_replace_clicked(self, btn):
        if not self.storecursor or not self.ent_search.get_text() or not self.ent_replace.get_text():
            return
        self.update_search()

        if self.chk_replace_all.get_active():
            self._replace_all()
        else:
            current_unit = self.storecursor.deref()
            # Find matches in the current unit.
            unit_matches = [match for match in self.matches if match.unit is current_unit and match.part == 'target']
            if len(unit_matches) > 0:
                i = self.matches.index(unit_matches[0])
                self.controller.main_controller.undo_controller.record_start()
                self.replace_match(unit_matches[0], self.ent_replace.get_text())
                self.controller.main_controller.undo_controller.record_stop()
                # FIXME: The following if is necessary to avoid an IndexError in del in certain circumstances.
                # I'm not sure why it happens, but I suspect it has something to do with self.matches not
                # being updated as expected after an undo.
                if 0 <= i < len(self.matches):
                    del self.matches[i]
            else:
                self.storecursor.move(1)

        self.update_search()

    def _on_search_clicked(self, btn):
        self._move_match(1)

    def _on_search_next(self, *args):
        self._move_match(1)

    def _on_search_prev(self, *args):
        self._move_match(-1)

    def _on_search_text_changed(self, entry):
        if self._search_timeout:
            gobject.source_remove(self._search_timeout)
            self._search_timeout = 0

        self._search_timeout = gobject.timeout_add(self.SEARCH_DELAY, self.update_search)

    def _on_start_search(self, _accel_group, _acceleratable, _keyval, _modifier):
        """This is called via the accelerator."""
        self.controller.select_mode(self)

    def _on_textbox_refreshed(self, textbox, elem):
        """Redoes highlighting after a C{StringElem} render destoyed it."""
        if not textbox.props.visible or not unicode(elem):
            return

        self._highlight_textbox_matches(textbox)

    def _on_unit_modified(self, unit_controller, current_unit):
        unit_matches = self._get_matches_for_unit(current_unit)
        for match in unit_matches:
            if not self.filter.re_search.match(match.get_getter()()[match.start:match.end]):
                logging.debug('Match to remove: %s' % (match))
                self.matches.remove(match)
                self.matchcursor.indices = range(len(self.matches))

    def _refresh_proxy(self, *args):
        self.update_search()
