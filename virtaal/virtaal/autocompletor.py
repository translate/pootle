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
import re

import undo_buffer


class AutoCompletor(object):
    """
    Does auto-completion of registered words in registered widgets.
    """

    wordsep_re = re.compile(r'\W+', re.UNICODE)

    DEFAULT_COMPLETION_LENGTH = 4 # The default minimum length of a word that may
                                  # be auto-completed.

    def __init__(self, word_list=[], comp_len=DEFAULT_COMPLETION_LENGTH):
        """Constructor.

            @type  word_list: iterable
            @param word_list: A list of words that should be auto-completed.
        """
        assert isinstance(word_list, list)
        self.comp_len = comp_len
        self._word_list = list(set(word_list))
        self.widgets = set()

    def add_widget(self, widget):
        """Add a widget to the list of widgets to do auto-completion for."""
        if widget in self.widgets:
            return # Widget already added

        if isinstance(widget, gtk.TextView):
            self._add_text_view(widget)
            return

        raise ValueError("Widget type %s not supported." % (type(widget)))

    def add_words(self, words):
        """Add a word or words to the list of words to auto-complete."""
        if isinstance(words, basestring):
            self._word_list.append(words)
        else:
            self._word_list += list(words)
        self._word_list = list(set(self._word_list)) # Remove duplicates

    def add_words_from_store(self, store):
        """Collect all words from the given translation store to use for
            auto-completion.

            @type  store: translate.storage.pypo.pofile
            @param store: The translation store to collect words from.
            """
        wordcounts = {}

        for unit in store.units:
            if not unit.target:
                continue
            for word in self.wordsep_re.split(unit.target):
                if len(word) > self.comp_len:
                    try:
                        wordcounts[word] += 1
                    except KeyError:
                        wordcounts[word] = 1

        # Sort found words according to frequency
        wordlist = wordcounts.items()
        wordlist.sort(key=lambda x:x[1])

        wordlist = [items[0] for items in wordlist]

        self._word_list += list(set(wordlist))

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
        self.words.clear()

    def remove_widget(self, widget):
        """Remove a widget (currently only C{gtk.TextView}s are accepted) from
            the list of widgets to do auto-correction for.
            """
        if isinstance(widget, gtk.TextView) and widget in self.widgets:
            self._remove_textview(widget)

    def remove_words(self, words):
        """Remove a word or words from the list of words to auto-complete."""
        if isinstance(words, basestring):
            self._word_list.remove(words)
        else:
            for w in words:
                try:
                    self._word_list.remove(w)
                except KeyError:
                    pass

    def _add_text_view(self, textview):
        """Add the given I{gtk.TextView} to the list of widgets to do auto-
            correction on.
            """
        id_dict_names = (
            '_textbuffer_insert_ids',
            '_textbuffer_delete_ids',
            '_textview_button_press_ids',
            '_textview_focus_out_ids',
            '_textview_key_press_ids',
            '_textview_move_cursor_ids'
        )
        for name in id_dict_names:
            if not hasattr(self, name):
                setattr(self, name, {})

        buffer = textview.get_buffer()
        handler_id = buffer.connect('insert-text', self._on_insert_text)
        self._textbuffer_insert_ids[buffer] = handler_id

        handler_id = buffer.connect('delete-range', self._on_delete_range)
        self._textbuffer_delete_ids[buffer] = handler_id

        handler_id = textview.connect('button-press-event', self._on_textview_button_press)
        self._textview_button_press_ids[textview] = handler_id

        handler_id = textview.connect('key-press-event', self._on_textview_keypress)
        self._textview_key_press_ids[textview] = handler_id

        handler_id = textview.connect('focus-out-event', self._on_textview_focus_out)
        self._textview_focus_out_ids[textview] = handler_id

        handler_id = textview.connect('move-cursor', self._on_textview_move_cursor)
        self._textview_move_cursor_ids[textview] = handler_id

        self.widgets.add(textview)

    def _check_delete_selection(self, buffer):
        """Deletes the current selection if said selection was created by the auto-completor."""
        suggestion = getattr(buffer, '_suggestion', None)
        if suggestion:
            buffer.delete_selection(False, True)
            buffer._suggestion = None

    def _on_insert_text(self, buffer, iter, text, length):
        if self.wordsep_re.match(text):
            return
        # We are only interested in single character insertions, otherwise we
        # react similarly for paste and similar events
        if len(text.decode('utf-8')) > 1:
            return
        prefix = unicode(buffer.get_text(buffer.get_start_iter(), iter) + text)
        postfix = unicode(buffer.get_text(iter, buffer.get_end_iter()))
        lastword = self.wordsep_re.split(prefix)[-1]

        if len(lastword) >= self.comp_len:
            completed_word, word_postfix = self.autocomplete(lastword)
            if completed_word == lastword:
                buffer._suggestion = None
                return

            if completed_word:
                completed_prefix = prefix[:-len(lastword)] + completed_word
                # Updating of the buffer is deferred until after this signal
                # and its side effects are taken care of. We abuse
                # gobject.idle_add for that.
                def suggest_completion():
                    def insert_action():
                        buffer.insert_at_cursor(word_postfix)
                    buffer.handler_block(self._textbuffer_insert_ids[buffer])
                    undo_buffer.execute_without_signals(buffer, insert_action)
                    buffer.handler_unblock(self._textbuffer_insert_ids[buffer])
                    sel_iter_start = buffer.get_iter_at_offset(len(prefix))
                    sel_iter_end   = buffer.get_iter_at_offset(len(prefix+word_postfix))
                    buffer.select_range(sel_iter_start, sel_iter_end)
                    buffer._suggestion = (sel_iter_start, sel_iter_end)
                    return False

                gobject.idle_add(suggest_completion)
            else:
                buffer._suggestion = None
        else:
            buffer._suggestion = None

    def _on_delete_range(self, buf, start_iter, end_iter):
        # If we are deleting the suggestion, we don't want it in the undo_stack
        suggestion = getattr(buf, '_suggestion', None)
        if suggestion:
            selection = buf.get_selection_bounds()
            if selection and suggestion[0].equal(selection[0]) and suggestion[1].equal(selection[1]):
                # Not pretty, but it works
                getattr(buf, "__undo_stack").pop()
                return False
            else:
                self._check_delete_selection(buf)
        buf._suggestion = None

    def _on_textview_button_press(self, textview, event):
        self._check_delete_selection(textview.get_buffer())

    def _on_textview_focus_out(self, textview, event):
        self._check_delete_selection(textview.get_buffer())

    def _on_textview_move_cursor(self, textview, step_size, count, expand_selection):
        self._check_delete_selection(textview.get_buffer())

    def _on_textview_keypress(self, textview, event):
        """Catch tabs to the C{gtk.TextView} and make it keep the current selection."""
        iters = textview.get_buffer().get_selection_bounds()

        if not iters:
            return False
        if event.keyval == gtk.keysyms.Tab:
            buf = textview.get_buffer()
            completion = buf.get_text(iters[0], iters[1])
            buf.delete(iters[0], iters[1])
            buf.insert_at_cursor(completion)
            return True
        elif event.state & gtk.gdk.CONTROL_MASK and \
                event.keyval == gtk.keysyms.Z or event.keyval== gtk.keysyms.BackSpace:
            # An undo/delete event will unselect the suggestion and make it hang
            # around. Therefore weneed to remove the suggestion manually.
            self._check_delete_selection(textview.get_buffer())
            return False

    def _remove_textview(self, textview):
        """Remove the given C{gtk.TextView} from the list of widgets to do
            auto-correction on.
            """
        if not hasattr(self, '_textbuffer_insert_ids'):
            return
        # Disconnect the "insert-text" event handler
        buffer = textview.get_buffer()
        buffer.disconnect(self._textbuffer_insert_ids[buffer])

        if not hasattr(self, '_textbuffer_delete_ids'):
            return
        # Disconnect the "delete-range" event handler
        buffer.disconnect(self._textbuffer_delete_ids[buffer])

        if not hasattr(self, '_textview_focus_out_ids'):
            return
        # Disconnect the "focus-out-event" event handler
        textview.disconnect(self._textview_focus_out_ids[textview])

        if not hasattr(self, '_textview_key_press_ids'):
            return
        # Disconnect the "key-press-event" event handler
        textview.disconnect(self._textview_key_press_ids[textview])

        if not hasattr(self, '_textview_move_cursor_ids'):
            return
        # Disconnect the "move-cursor" event handler
        textview.disconnect(self._textview_move_cursor_ids[textview])

        self.widgets.remove(textview)
