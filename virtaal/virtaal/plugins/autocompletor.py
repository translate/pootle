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

"""Contains the AutoCompletor class."""

import gobject
import gtk
import logging
import re
try:
    from collections import defaultdict
except ImportError:
    class defaultdict(dict):
        def __init__(self, default_factory=lambda: None):
            self.__factory = default_factory

        def __getitem__(self, key):
            if key in self:
                return super(defaultdict, self).__getitem__(key)
            else:
                return self.__factory()

from virtaal.controllers import BasePlugin
from virtaal.views.widgets.textbox import TextBox


class AutoCompletor(object):
    """
    Does auto-completion of registered words in registered widgets.
    """

    wordsep_re = re.compile(r'\W+', re.UNICODE)

    MAX_WORDS = 10000
    DEFAULT_COMPLETION_LENGTH = 4 # The default minimum length of a word that may
                                  # be auto-completed.

    def __init__(self, main_controller, word_list=[], comp_len=DEFAULT_COMPLETION_LENGTH):
        """Constructor.

            @type  word_list: iterable
            @param word_list: A list of words that should be auto-completed."""
        self.main_controller = main_controller
        assert isinstance(word_list, list)
        self.comp_len = comp_len
        self._word_list = []
        self._word_freq = defaultdict(lambda: 0)
        self.add_words(word_list)
        self.widgets = set()

    def add_widget(self, widget):
        """Add a widget to the list of widgets to do auto-completion for."""
        if widget in self.widgets:
            return # Widget already added

        if isinstance(widget, TextBox):
            self._add_text_box(widget)
            return

        raise ValueError("Widget type %s not supported." % (type(widget)))

    def add_words(self, words, update=True):
        """Add a word or words to the list of words to auto-complete."""
        for word in words:
            if self.isusable(word):
                self._word_freq[word] += 1
        if update:
            self._update_word_list()

    def add_words_from_units(self, units):
        """Collect all words from the given translation units to use for
            auto-completion.

            @type  units: list
            @param units: The translation units to collect words from.
            """
        for unit in units:
            target = unit.target
            if not target:
                continue
            self.add_words(self.wordsep_re.split(target), update=False)
            if len(self._word_freq) > self.MAX_WORDS:
                break

        self._update_word_list()

    def autocomplete(self, word):
        for w in self._word_list:
            if w.startswith(word):
                return w, w[len(word):]
        return None, u''

    def clear_widgets(self):
        """Release all registered widgets from the spell of auto-completion."""
        for w in set(self.widgets):
            self.remove_widget(w)

    def clear_words(self):
        """Remove all registered words; effectively turns off auto-completion."""
        self._word_freq = []
        self._word_list = defaultdict(lambda: 0)

    def isusable(self, word):
        """Returns a value indicating if the given word should be kept as a
        suggestion for autocomplete."""
        return len(word) > self.comp_len + 2

    def remove_widget(self, widget):
        """Remove a widget (currently only L{TextBox}s are accepted) from
            the list of widgets to do auto-correction for.
            """
        if isinstance(widget, TextBox) and widget in self.widgets:
            self._remove_textbox(widget)

    def remove_words(self, words):
        """Remove a word or words from the list of words to auto-complete."""
        if isinstance(words, basestring):
            del self._word_freq[words]
            self._word_list.remove(words)
        else:
            for w in words:
                try:
                    del self._word_freq[w]
                    self._word_list.remove(w)
                except KeyError:
                    pass

    def _add_text_box(self, textbox):
        """Add the given L{TextBox} to the list of widgets to do auto-
            correction on."""
        if not hasattr(self, '_textbox_insert_ids'):
            self._textbox_insert_ids = {}
        handler_id = textbox.connect('text-inserted', self._on_insert_text)
        self._textbox_insert_ids[textbox] = handler_id
        self.widgets.add(textbox)

    def _on_insert_text(self, textbox, text, offset, elem):
        if not isinstance(text, basestring) or self.wordsep_re.match(text):
            return
        # We are only interested in single character insertions, otherwise we
        # react similarly for paste and similar events
        if len(text.decode('utf-8')) > 1:
            return

        prefix = unicode(textbox.get_text(0, offset) + text)
        postfix = unicode(textbox.get_text(offset))
        buffer = textbox.buffer

        # Quick fix to check that we don't autocomplete in the middle of a word.
        right_lim = len(postfix) > 0 and postfix[0] or ' '
        if not self.wordsep_re.match(right_lim):
            return

        lastword = self.wordsep_re.split(prefix)[-1]

        if len(lastword) >= self.comp_len:
            completed_word, word_postfix = self.autocomplete(lastword)
            if completed_word == lastword:
                return

            if completed_word:
                # Updating of the buffer is deferred until after this signal
                # and its side effects are taken care of. We abuse
                # gobject.idle_add for that.
                insert_offset = offset + len(text)
                def suggest_completion():
                    textbox.handler_block(self._textbox_insert_ids[textbox])
                    #logging.debug("textbox.suggestion = {'text': u'%s', 'offset': %d}" % (word_postfix, insert_offset))
                    textbox.suggestion = {'text': word_postfix, 'offset': insert_offset}
                    textbox.handler_unblock(self._textbox_insert_ids[textbox])

                    sel_iter_start = buffer.get_iter_at_offset(insert_offset)
                    sel_iter_end   = buffer.get_iter_at_offset(insert_offset + len(word_postfix))
                    buffer.select_range(sel_iter_start, sel_iter_end)

                    return False

                gobject.idle_add(suggest_completion, priority=gobject.PRIORITY_HIGH)

    def _remove_textbox(self, textbox):
        """Remove the given L{TextBox} from the list of widgets to do
            auto-correction on.
            """
        if not hasattr(self, '_textbox_insert_ids'):
            return
        # Disconnect the "insert-text" event handler
        textbox.disconnect(self._textbox_insert_ids[textbox])

        self.widgets.remove(textbox)

    def _update_word_list(self):
        """Update and sort found words according to frequency."""
        wordlist = self._word_freq.items()
        wordlist.sort(key=lambda x:x[1])
        self._word_list = [items[0] for items in wordlist]


class Plugin(BasePlugin):
    description = _('Automatically complete long words while you type')
    display_name = _('AutoCompletor')
    version = 0.1

    # INITIALIZERS #
    def __init__(self, internal_name, main_controller):
        self.internal_name = internal_name
        self.main_controller = main_controller

        self._init_plugin()

    def _init_plugin(self):
        from virtaal.common import pan_app
        self.autocomp = AutoCompletor(self.main_controller)

        self._store_loaded_id = self.main_controller.store_controller.connect('store-loaded', self._on_store_loaded)

        for target in self.main_controller.unit_controller.view.targets:
            self.autocomp.add_widget(target)

        if self.main_controller.store_controller.get_store():
            # Connect to already loaded store. This happens when the plug-in is enabled after loading a store.
            self._on_store_loaded(self.main_controller.store_controller)


    # METHDOS #
    def destroy(self):
        """Remove all signal-connections."""
        self.autocomp.clear_words()
        self.autocomp.clear_widgets()
        self.main_controller.store_controller.disconnect(self._store_loaded_id)
        if getattr(self, '_cursor_changed_id', None):
            self.store_cursor.disconnect(self._cursor_changed_id)


    # EVENT HANDLERS #
    def _on_cursor_change(self, cursor):
        def add_widgets():
            if hasattr(self, 'lastunit'):
                if self.lastunit.hasplural():
                    for target in self.lastunit.target:
                        if target:
                            #logging.debug('Adding words: %s' % (self.autocomp.wordsep_re.split(unicode(target))))
                            self.autocomp.add_words(self.autocomp.wordsep_re.split(unicode(target)))
                else:
                    if self.lastunit.target:
                        #logging.debug('Adding words: %s' % (self.autocomp.wordsep_re.split(unicode(self.lastunit.target))))
                        self.autocomp.add_words(self.autocomp.wordsep_re.split(unicode(self.lastunit.target)))
            self.lastunit = cursor.deref()
        gobject.idle_add(add_widgets)

    def _on_store_loaded(self, storecontroller):
        self.autocomp.add_words_from_units(storecontroller.get_store().get_units())

        if hasattr(self, '_cursor_changed_id'):
            self.store_cursor.disconnect(self._cursor_changed_id)
        self.store_cursor = storecontroller.cursor
        self._cursor_changed_id = self.store_cursor.connect('cursor-changed', self._on_cursor_change)
        self._on_cursor_change(self.store_cursor)
