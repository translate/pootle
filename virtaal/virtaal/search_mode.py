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
import logging
import re

from translate.tools.pogrep import GrepFilter

from virtaal.modes import BaseMode
from virtaal.support.set_enumerator import UnionSetEnumerator
from virtaal.support.sorted_set import SortedSet


HL_START, HL_END = range(2) # Indexes into SearchMode.highlight_marks

class SearchMode(BaseMode):
    mode_name = "Search"
    user_name = _("Search")
    widgets = []

    highlight_marks = '[]'

    SEARCH_DELAY = 500

    def __init__(self):
        UnionSetEnumerator.__init__(self)
        self.ent_search = gtk.Entry()
        self.ent_search.connect('changed', self._on_search_text_changed)
        self.ent_search.connect('activate', self._on_entry_activate)
        self.default_base = gtk.widget_get_default_style().base[gtk.STATE_NORMAL]
        self.default_text = gtk.widget_get_default_style().text[gtk.STATE_NORMAL]
        self.chk_casesensitive = gtk.CheckButton(_('_Case sensitive'))
        self.chk_casesensitive.connect('toggled', self._refresh_proxy)
        self.chk_regex = gtk.CheckButton(_("_Regular expression"))
        self.chk_regex.connect('toggled', self._refresh_proxy)

        self.prev_editor = None
        self.re_search = None
        self.widgets = [self.ent_search, self.chk_casesensitive, self.chk_regex]
        self.filter = self.makefilter()
        self.select_first_match = True
        self._search_timeout = 0

    def makefilter(self):
        searchstring = self.ent_search.get_text()
        searchparts = ('source', 'target')
        ignorecase = not self.chk_casesensitive.get_active()
        useregexp = self.chk_regex.get_active()

        return GrepFilter(searchstring, searchparts, ignorecase, useregexp)

    def selected(self, document):
        """Focus the search entry.

            This method should only be called after this mode has been selected."""
        self.document = document
        if not self.ent_search.get_text():
            UnionSetEnumerator.__init__(self, SortedSet(document.stats['total']))
        else:
            self._on_search_text_changed(self.ent_search)

        def grab_focus():
            self.ent_search.grab_focus()
            return False

        # FIXME: The following line is a VERY UGLY HACK, but at least it works.
        gobject.timeout_add(100, grab_focus)

    def unit_changed(self, editor):
        """Highlights all occurances of the search string in the newly selected unit."""
        self._unhighlight_previous_matches()
        if not self.ent_search.get_text():
            return
        self._highlight_matches(editor)
        self.prev_editor = editor

    def unselected(self):
        """This mode has been unselected, so any current highlighting should be removed."""
        self._unhighlight_previous_matches()

    def update_search(self):
        self.filter = self.makefilter()

        # Filter stats with text in "self.ent_search"
        filtered = []
        i = 0
        for unit in self.document.store.units:
            if self.filter.filterunit(unit):
                filtered.append(i)
            i += 1

        logging.debug('Search text: %s (%d matches)' % (self.ent_search.get_text(), len(filtered)))

        old_elem = self.document.mode_cursor.deref()

        if filtered:
            self.ent_search.modify_base(gtk.STATE_NORMAL, self.default_base)
            self.ent_search.modify_text(gtk.STATE_NORMAL, self.default_text)

            searchstr = self.ent_search.get_text().decode('utf-8')
            flags = re.UNICODE | re.MULTILINE
            if not self.chk_casesensitive.get_active():
                flags |= re.IGNORECASE
            if not self.chk_regex.get_active():
                searchstr = re.escape(searchstr)
            self.re_search = re.compile(u'(%s)' % searchstr, flags)
            UnionSetEnumerator.__init__(self, SortedSet(filtered))
        else:
            self.ent_search.modify_base(gtk.STATE_NORMAL, gtk.gdk.color_parse('#f66'))
            self.ent_search.modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse('#fff'))
            self.re_search = None
            # Act like the "Default" mode...
            UnionSetEnumerator.__init__(self, SortedSet(self.document.stats['total']))

        self.document.mode_cursor = self.document.mode.cursor_from_element(old_elem)
        self.document.cursor_changed()

        def grabfocus():
            self.ent_search.grab_focus()
            self.ent_search.set_position(-1)
            return False
        gobject.idle_add(grabfocus)

    def _highlight_matches(self, editor):
        if self.re_search is None:
            return

        for textview in editor.sources + editor.targets:
            buff = textview.get_buffer()
            buffstr = buff.get_text(buff.get_start_iter(), buff.get_end_iter()).decode('utf-8')

            # First make sure that the current buffer contains a highlighting tag.
            # Because a gtk.TextTag can only be associated with one gtk.TagTable,
            # we make copies (created by _make_highlight_tag()) to add to all
            # TagTables. If the tag is already added to a given table, a
            # ValueError is raised which we can safely ignore.
            try:
                buff.get_tag_table().add(self._make_highlight_tag())
            except ValueError:
                pass

            select_iters = []
            for match in self.re_search.finditer(buffstr):
                start_iter, end_iter = buff.get_iter_at_offset(match.start()), buff.get_iter_at_offset(match.end())
                buff.apply_tag_by_name('highlight', start_iter, end_iter)

                if textview in editor.targets and not select_iters and self.select_first_match:
                    select_iters = [start_iter, end_iter]

            if select_iters:
                def do_selection():
                    buff.move_mark_by_name('selection_bound', select_iters[0])
                    buff.move_mark_by_name('insert', select_iters[1])
                    return False
                gobject.idle_add(do_selection)

    def _unhighlight_previous_matches(self):
        if self.prev_editor is None:
            return

        for textview in self.prev_editor.sources + self.prev_editor.targets:
            buff = textview.get_buffer()
            buff.remove_all_tags(buff.get_start_iter(), buff.get_end_iter())

    def _make_highlight_tag(self):
        tag = gtk.TextTag(name='highlight')
        tag.set_property('background', 'blue')
        tag.set_property('foreground', 'white')
        return tag

    def _on_entry_activate(self, entry):
        if self.document is None:
            return
        self.document.cursor_changed()

    def _on_search_text_changed(self, entry):
        if self._search_timeout:
            gobject.source_remove(self._search_timeout)
            self._search_timeout = 0

        self._search_timeout = gobject.timeout_add(self.SEARCH_DELAY, self.update_search)

    def _refresh_proxy(self, *args):
        self._on_search_text_changed(self.ent_search)
