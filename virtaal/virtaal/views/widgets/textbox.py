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
from gobject import SIGNAL_RUN_FIRST, SIGNAL_RUN_LAST

from translate.misc.typecheck import accepts, Self, IsOneOf
from translate.storage.placeables import StringElem, parse as elem_parse
from translate.lang import data

from virtaal.views import placeablesguiinfo


class TextBox(gtk.TextView):
    """
    A C{gtk.TextView} extended to work with our nifty L{StringElem} parsed
    strings.
    """

    __gtype_name__ = 'TextBox'
    __gsignals__ = {
        'after-apply-gui-info':  (SIGNAL_RUN_FIRST, None, (object,)),
        'before-apply-gui-info': (SIGNAL_RUN_FIRST, None, (object,)),
        'element-selected':      (SIGNAL_RUN_FIRST, None, (object,)),
        'key-pressed':           (SIGNAL_RUN_LAST,  bool, (object, str)),
        'refreshed':             (SIGNAL_RUN_FIRST, None, (object,)),
        'text-deleted':          (SIGNAL_RUN_LAST,  bool, (object, object, int, int, object)),
        'text-inserted':         (SIGNAL_RUN_LAST,  bool, (object, int, object)),
    }

    SPECIAL_KEYS = {
        'alt-down':  [(gtk.keysyms.Down,  gtk.gdk.MOD1_MASK)],
        'alt-left':  [(gtk.keysyms.Left,  gtk.gdk.MOD1_MASK)],
        'alt-right': [(gtk.keysyms.Right, gtk.gdk.MOD1_MASK)],
        'enter':     [(gtk.keysyms.Return, 0), (gtk.keysyms.KP_Enter, 0)],
        'shift-tab': [(gtk.keysyms.ISO_Left_Tab, gtk.gdk.SHIFT_MASK), (gtk.keysyms.Tab, gtk.gdk.SHIFT_MASK)],
    }
    """A table of name-keybinding mappings. The name (key) is passed as the
    second parameter to the 'key-pressed' event."""
    unselectables = [StringElem]
    """A list of classes that should not be selectable with Alt+Left or Alt+Right."""

    # INITIALIZERS #
    def __init__(self, main_controller, text=None, selector_textbox=None, role=None):
        """Constructor.
        @type  main_controller: L{virtaal.controllers.main_controller}
        @param main_controller: The main controller instance.
        @type  text: String
        @param text: The initial text to set in the new text box. Optional.
        @type  selector_textbox: C{TextBox}
        @param selector_textbox: The text box in which placeable selection
            (@see{select_elem}) should happen. Optional."""
        super(TextBox, self).__init__()
        self.buffer = self.get_buffer()
        self.elem = None
        self.main_controller = main_controller
        self.placeables_controller = main_controller.placeables_controller
        self.refresh_actions = []
        self.refresh_cursor_pos = -1
        self.role = role
        self.selector_textbox = selector_textbox or self
        self.selected_elem = None
        self.selected_elem_index = None
        self._suggestion = None
        self.undo_controller = main_controller.undo_controller

        self.__connect_default_handlers()

        if self.placeables_controller is None or self.undo_controller is None:
            # This should always happen, because the text boxes are created
            # when the unit controller is created, which happens before the
            # creation of the placeables- and undo controllers.
            self.__controller_connect_id = main_controller.connect('controller-registered', self.__on_controller_register)
        if text:
            self.set_text(text)

    def __connect_default_handlers(self):
        self.connect('button-press-event', self._on_event_remove_suggestion)
        self.connect('focus-out-event', self._on_event_remove_suggestion)
        self.connect('key-press-event', self._on_key_pressed)
        self.connect('move-cursor', self._on_event_remove_suggestion)
        self.buffer.connect('insert-text', self._on_insert_text)
        self.buffer.connect('delete-range', self._on_delete_range)
        self.buffer.connect('begin-user-action', self._on_begin_user_action)
        self.buffer.connect('end-user-action', self._on_end_user_action)


    def _get_suggestion(self):
        return self._suggestion
    def _set_suggestion(self, value):
        if value is None:
            self.hide_suggestion()
            self._suggestion = None
            return

        if not (isinstance(value, dict) and \
                'text'   in value and value['text'] and \
                'offset' in value and value['offset'] >= 0):
            raise ValueError('invalid suggestion dictionary: %s' % (value))

        if self.suggestion_is_visible():
            self.suggestion = None
        self._suggestion = value
        self.show_suggestion()
    suggestion = property(_get_suggestion, _set_suggestion)

    # OVERRIDDEN METHODS #
    def get_stringelem(self):
        if self.elem is None:
            return None
        return elem_parse(self.elem, self.placeables_controller.get_parsers_for_textbox(self))

    def get_text(self, start_iter=None, end_iter=None):
        """Return the text rendered in this text box.
            Uses C{gtk.TextBuffer.get_text()}."""
        if isinstance(start_iter, int):
            start_iter = self.buffer.get_iter_at_offset(start_iter)
        if isinstance(end_iter, int):
            end_iter = self.buffer.get_iter_at_offset(end_iter)
        if start_iter is None:
            start_iter = self.buffer.get_start_iter()
        if end_iter is None:
            end_iter = self.buffer.get_end_iter()
        return data.forceunicode(self.buffer.get_text(start_iter, end_iter))

    @accepts(Self(), [[IsOneOf(StringElem, str, unicode)]])
    def set_text(self, text):
        """Set the text rendered in this text box.
            Uses C{gtk.TextBuffer.set_text()}.
            @type  text: str|unicode|L{StringElem}
            @param text: The text to render in this text box."""
        if not isinstance(text, StringElem):
            text = StringElem(text)

        if self.elem is None:
            self.elem = StringElem(u'')

        if text is not self.elem:
            # If text is self.elem, we are busy with a refresh and we should remember the selected element.
            self.selected_elem = None
            self.selected_elem_index = None

            if self.placeables_controller:
                self.elem.sub = [elem_parse(text, self.placeables_controller.get_parsers_for_textbox(self))]
            else:
                self.elem.sub = [text]
            self.elem.prune()

        self.update_tree(self.elem)


    # METHODS #
    @accepts(Self(), [StringElem])
    def add_default_gui_info(self, elem):
        """Add default GUI info to string elements in the tree that does not
            have any GUI info.

            Only leaf nodes are (currently) extended with a C{StringElemGUI}
            (or sub-class) instance. Other nodes has C{gui_info} set to C{None}.

            @type  elem: StringElem
            @param elem: The root of the string element tree to add default
                GUI info to.
            """
        if not isinstance(elem, StringElem):
            return

        if not hasattr(elem, 'gui_info') or not elem.gui_info:
            if not self.placeables_controller:
                return
            elem.gui_info = self.placeables_controller.get_gui_info(elem)(elem=elem, textbox=self)

        for sub in elem.sub:
            self.add_default_gui_info(sub)

    @accepts(Self(), [StringElem, bool])
    def apply_gui_info(self, elem, include_subtree=True):
        offset = self.elem.gui_info.index(elem)
        #logging.debug('offset for %s: %d' % (repr(elem), offset))
        if offset >= 0:
            #logging.debug('[%s] at offset %d' % (unicode(elem).encode('utf-8'), offset))
            self.emit('before-apply-gui-info', elem)

            if getattr(elem, 'gui_info', None):
                start_index = offset
                end_index = offset + elem.gui_info.length()
                interval = end_index - start_index
                for tag, tag_start, tag_end in elem.gui_info.create_tags():
                    if tag is None:
                        continue
                    # Calculate tag start and end offsets
                    if tag_start is None:
                        tag_start = 0
                    if tag_end is None:
                        tag_end = end_index
                    if tag_start < 0:
                        tag_start += interval + 1
                    else:
                        tag_start += start_index
                    if tag_end < 0:
                        tag_end += end_index + 1
                    else:
                        tag_end += start_index
                    if tag_start < start_index:
                        tag_start = start_index
                    if tag_end > end_index:
                        tag_end = end_index

                    iters = (
                        self.buffer.get_iter_at_offset(tag_start),
                        self.buffer.get_iter_at_offset(tag_end)
                    )
                    #logging.debug('  Apply tag at interval (%d, %d) [%s]' % (tag_start, tag_end, self.get_text(*iters)))

                    if not include_subtree or \
                            elem.gui_info.fg != placeablesguiinfo.StringElemGUI.fg or \
                            elem.gui_info.bg != placeablesguiinfo.StringElemGUI.bg:
                        self.buffer.get_tag_table().add(tag)
                        self.buffer.apply_tag(tag, iters[0], iters[1])

        if include_subtree:
            for sub in elem.sub:
                if isinstance(sub, StringElem):
                    self.apply_gui_info(sub)

        self.emit('after-apply-gui-info', elem)

    def hide_suggestion(self):
        if not self.suggestion_is_visible():
            return
        selection = self.buffer.get_selection_bounds()
        if not selection:
            return

        self.buffer.handler_block_by_func(self._on_delete_range)
        self.buffer.delete(*selection)
        self.buffer.handler_unblock_by_func(self._on_delete_range)

    @accepts(Self(), [StringElem])
    def insert_translation(self, elem):
        selection = self.buffer.get_selection_bounds()
        if selection:
            self.buffer.delete(*selection)

        while gtk.events_pending():
            gtk.main_iteration()

        cursor_pos = self.buffer.props.cursor_position
        widget = elem.gui_info.get_insert_widget()
        if widget:
            def show_widget():
                cursor_iter = self.buffer.get_iter_at_offset(cursor_pos)
                anchor = self.buffer.create_child_anchor(cursor_iter)
                # It is necessary to recreate cursor_iter becuase, for some inexplicable reason,
                # the Gtk guys thought it acceptable to have create_child_anchor() above CHANGE
                # THE PARAMETER ITER'S VALUE! But only in some cases, while the moon is 73.8% full
                # and it's after 16:33. Documenting this is obviously also too much to ask.
                # Nevermind the fact that there isn't simply a gtk.TextBuffer.remove_anchor() method
                # or something similar. Why would you want to remove anything from a TextView that
                # you have added anyway!?
                # It's crap like this that'll make me ditch Gtk.
                cursor_iter = self.buffer.get_iter_at_offset(cursor_pos)
                self.add_child_at_anchor(widget, anchor)
                widget.show_all()
                if callable(getattr(widget, 'inserted', None)):
                    widget.inserted(cursor_iter, anchor)
            # show_widget() must be deferred until the refresh() following this
            # signal's completion. Otherwise the changes made by show_widget()
            # and those made by the refresh() will wage war on each other and
            # leave Virtaal as one of the casualties thereof.
            self.refresh_actions.append(show_widget)
        else:
            translation = elem.translate()
            if isinstance(translation, StringElem):
                self.add_default_gui_info(translation)
                insert_offset = self.elem.gui_info.gui_to_tree_index(cursor_pos)
                self.elem.insert(insert_offset, translation)
                self.elem.prune()

                self.emit('text-inserted', translation, cursor_pos, self.elem)

                if hasattr(translation, 'gui_info'):
                    cursor_pos += translation.gui_info.length()
                else:
                    cursor_pos += len(translation)
            else:
                self.buffer.insert_at_cursor(translation)
                cursor_pos += len(translation)
        self.refresh_cursor_pos = cursor_pos
        self.refresh()

    @accepts(Self(), [int])
    def move_elem_selection(self, offset):
        if self.selector_textbox.selected_elem_index is None:
            if offset <= 0:
                self.selector_textbox.select_elem(offset=offset)
            else:
                self.selector_textbox.select_elem(offset=offset-1)
        else:
            self.selector_textbox.select_elem(offset=self.selector_textbox.selected_elem_index + offset)

    def place_cursor(self, cursor_pos):
        cursor_iter = self.buffer.get_iter_at_offset(cursor_pos)

        if not cursor_iter:
            raise ValueError('Could not get TextIter for position %d (%d)' % (cursor_pos, len(self.get_text())))
        #logging.debug('setting cursor to position %d' % (cursor_pos))
        self.buffer.place_cursor(self.buffer.get_iter_at_offset(cursor_pos))

    def refresh(self, preserve_selection=True):
        """Refresh the text box by setting its text to the current text."""
        if not self.props.visible:
            return # Don't refresh if this text box is not going to be seen anyway
        #logging.debug('self.refresh_cursor_pos = %d' % (self.refresh_cursor_pos))
        if self.refresh_cursor_pos < 0:
            self.refresh_cursor_pos = self.buffer.props.cursor_position
        selection = [itr.get_offset() for itr in self.buffer.get_selection_bounds()]

        if self.elem is not None:
            self.elem.prune()
            self.set_text(self.elem)
        else:
            self.set_text(self.get_text())

        if preserve_selection and selection:
            self.buffer.select_range(
                self.buffer.get_iter_at_offset(selection[0]),
                self.buffer.get_iter_at_offset(selection[1]),
            )
        elif self.refresh_cursor_pos >= 0:
            self.place_cursor(self.refresh_cursor_pos)
        self.refresh_cursor_pos = -1

        for action in self.refresh_actions:
            if callable(action):
                action()
        self.refresh_actions = []

        self.emit('refreshed', self.elem)

    @accepts(Self(), [[StringElem, None], [int, None]])
    def select_elem(self, elem=None, offset=None):
        if elem is not None and offset is not None:
            raise ValueError('Only one of "elem" or "offset" may be specified.')

        if elem is None and offset is None:
            # Clear current selection
            if self.selected_elem is not None:
                #logging.debug('Selected item *was* %s' % (repr(self.selected_elem)))
                self.selected_elem.gui_info = None
                self.add_default_gui_info(self.selected_elem)
                self.selected_elem = None
            self.selected_elem_index = None
            return

        filtered_elems = [e for e in self.elem.depth_first() if e.__class__ not in self.unselectables]
        if not filtered_elems:
            return

        if elem is None and offset is not None:
            return self.select_elem(elem=filtered_elems[offset % len(filtered_elems)])

        if not elem in filtered_elems:
            return

        # Reset the default tag for the previously selected element
        if self.selected_elem is not None:
            self.selected_elem.gui_info = None
            self.add_default_gui_info(self.selected_elem)

        i = 0
        for fe in filtered_elems:
            if fe is elem:
                break
            i += 1
        self.selected_elem_index = i
        self.selected_elem = elem
        #logging.debug('Selected element: %s (%s)' % (repr(self.selected_elem), unicode(self.selected_elem)))
        if not hasattr(elem, 'gui_info') or not elem.gui_info:
            elem.gui_info = placeablesguiinfo.StringElemGUI(elem, self, fg='#000000', bg='#90ee90')
        else:
            elem.gui_info.fg = '#000000'
            elem.gui_info.bg = '#90ee90'
        self.apply_gui_info(self.elem, include_subtree=False)
        self.apply_gui_info(self.elem)
        self.apply_gui_info(elem, include_subtree=False)
        cursor_offset = self.elem.find(self.selected_elem) + len(self.selected_elem)
        self.place_cursor(cursor_offset)
        self.emit('element-selected', self.selected_elem)

    def show_suggestion(self, suggestion=None):
        if isinstance(suggestion, dict):
            self.suggestion = suggestion
        if self.suggestion is None:
            return
        iters = (self.buffer.get_iter_at_offset(self.suggestion['offset']),)
        self.buffer.handler_block_by_func(self._on_insert_text)
        self.buffer.insert(iters[0], self.suggestion['text'])
        self.buffer.handler_unblock_by_func(self._on_insert_text)
        iters = (
            self.buffer.get_iter_at_offset(self.suggestion['offset']),
            self.buffer.get_iter_at_offset(
                self.suggestion['offset'] + len(self.suggestion['text'])
            )
        )
        self.buffer.select_range(*iters)

    def suggestion_is_visible(self):
        """Checks whether the current text suggestion is visible."""
        selection = self.buffer.get_selection_bounds()
        if not selection or self.suggestion is None:
            return False
        start_offset = selection[0].get_offset()
        text = self.buffer.get_text(*selection)
        return self.suggestion['text'] and \
                self.suggestion['text'] == text and \
                self.suggestion['offset'] >= 0 and \
                self.suggestion['offset'] == start_offset

    @accepts(Self(), [[StringElem, basestring, None]])
    def update_tree(self, text=None):
        if not self.placeables_controller:
            return
        if not isinstance(text, StringElem):
            return
        if self.elem is None:
            self.elem = StringElem(u'')
        if text is not self.elem:
            self.elem.sub = [text]
            self.elem.prune()

        self.add_default_gui_info(self.elem)

        self.buffer.handler_block_by_func(self._on_delete_range)
        self.buffer.handler_block_by_func(self._on_insert_text)
        self.elem.gui_info.render()
        self.show_suggestion()
        self.buffer.handler_unblock_by_func(self._on_delete_range)
        self.buffer.handler_unblock_by_func(self._on_insert_text)

        tagtable = self.buffer.get_tag_table()
        def remtag(tag, data):
            tagtable.remove(tag)
        # FIXME: The following line caused the program to segfault, so it's removed (for now).
        #tagtable.foreach(remtag)
        # At this point we have a tree of string elements with GUI info.
        self.apply_gui_info(text)


    # EVENT HANDLERS #
    def __on_controller_register(self, main_controller, controller):
        if controller is main_controller.placeables_controller:
            self.placeables_controller = controller
        elif controller is main_controller.undo_controller:
            self.undo_controller = controller

        if self.placeables_controller is not None and \
                self.undo_controller is not None:
            main_controller.disconnect(self.__controller_connect_id)

    def _on_begin_user_action(self, buffer):
        if not self.undo_controller.model.recording:
            self.undo_controller.record_start()

    def _on_end_user_action(self, buffer):
        if self.undo_controller.model.recording:
            self.undo_controller.record_stop()
        self.refresh()

    def _on_delete_range(self, buffer, start_iter, end_iter):
        if self.elem is None:
            return

        cursor_pos = self.refresh_cursor_pos
        if cursor_pos < 0:
            cursor_pos = self.buffer.props.cursor_position

        text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter())
        text = data.forceunicode(text)
        start_offset = start_iter.get_offset()
        end_offset = end_iter.get_offset()

        start_elem = self.elem.gui_info.elem_at_offset(start_offset)
        if start_elem is None:
            return
        start_elem_len = start_elem.gui_info.length()
        start_elem_offset = self.elem.gui_info.index(start_elem)

        end_elem = self.elem.gui_info.elem_at_offset(end_offset)
        if end_elem is not None:
            # end_elem can be None if end_offset == self.elem.gui_info.length()
            end_elem_len = end_elem.gui_info.length()
            end_elem_offset = self.elem.gui_info.index(end_elem)
        else:
            end_elem_len = 0
            end_elem_offset = self.elem.gui_info.length()

        #logging.debug('pre-checks: %s[%d:%d]' % (repr(self.elem), start_offset, end_offset))
        #logging.debug('start_elem_offset= %d\tend_elem_offset= %d' % (start_elem_offset, end_elem_offset))
        #logging.debug('start_elem_len   = %d\tend_elem_len   = %d' % (start_elem_len, end_elem_len))
        #logging.debug('start_offset     = %d\tend_offset     = %d' % (start_offset, end_offset))

        # Per definition of a selection, cursor_pos must be at either
        # start_offset or end_offset
        key_is_delete = cursor_pos == start_offset
        done = False

        deleted, parent, index = None, None, None

        if abs(start_offset - end_offset) == 1:
            position = None
            #################################
            #  Placeable:  |<<|content|>>|  #
            #  Cursor:     a  b       c  d  #
            #===============================#
            #           Editable            #
            #===============================#
            #   |  Backspace  |  Delete     #
            #---|-------------|-------------#
            # a |  N/A        |  Placeable  #
            # b |  Nothing    | @Delete "c" #
            # c | @Delete "t" |  Nothing    #
            # d |  Placeable  |  N/A        #
            #===============================#
            #         Non-Editable          #
            #===============================#
            # a |  N/A        |  Placeable  #
            # b | *Nothing    | *Nothing    #
            # c | *Nothing    | *Nothing    #
            # d |  Placeable  |  N/A        #
            #################################
            # The table above specifies what should be deleted for editable and
            # non-editable placeables when the cursor is at a specific boundry
            # position (a, b, c, d) and a specified key is pressed (backspace or
            # delete). Without widgets, positions b and c fall away.
            #
            # @ It is unnecessary to handle these cases, as long as control drops
            #   through to a place where it is handled below.
            # * Or "Placeable" depending on the value of the XXX flag in the
            #   placeable's GUI info object

            # First we check if we fall in any of the situations represented by
            # the table above.
            has_start_widget = has_end_widget = False
            if hasattr(start_elem, 'gui_info'):
                widgets = start_elem.gui_info.widgets
                has_start_widget = start_elem.gui_info.has_start_widget()
                has_end_widget   = start_elem.gui_info.has_end_widget()

            if cursor_pos == start_elem_offset:
                position = 'a'
            elif has_start_widget and cursor_pos == start_elem_offset+1:
                position = 'b'
            elif has_end_widget and cursor_pos == start_elem_offset + start_elem_len - 1:
                position = 'c'
            elif cursor_pos == start_elem_offset + start_elem_len:
                position = 'd'

            # If the current state is in the table, handle it
            if position:
                #logging.debug('(a)<<(b)content(c)>>(d)   pos=%s' % (position))
                if (position == 'a' and not key_is_delete) or (position == 'd' and key_is_delete):
                    # "N/A" fields in table
                    pass
                elif (position == 'a' and key_is_delete) or (position == 'd' and not key_is_delete):
                    # "Placeable" fields
                    if (position == 'a' and (has_start_widget or not start_elem.iseditable)) or \
                            (position == 'd' and (has_end_widget or not start_elem.iseditable)):
                        deleted = start_elem.copy()
                        parent = self.elem.get_parent_elem(start_elem)
                        index = parent.elem_offset(start_elem)
                        self.elem.delete_elem(start_elem)

                        self.refresh_cursor_pos = start_elem_offset
                        start_offset = start_elem_offset
                        end_offset = start_elem_offset + start_elem_len
                        done = True
                elif not start_elem.iseditable and position in ('b', 'c'):
                    # "*Nothing" fields
                    if start_elem.isfragile:
                        deleted = start_elem.copy()
                        parent = self.elem.get_parent_elem(start_elem)
                        index = parent.elem_offset(start_elem)
                        self.elem.delete_elem(start_elem)

                        self.refresh_cursor_pos = start_elem_offset
                        start_offset = start_elem_offset
                        end_offset = start_elem_offset + start_elem_len
                    done = True
                # At this point we have checked for all cases except where
                # position in ('b', 'c') for editable elements.
                elif (position == 'c' and not key_is_delete) or (position == 'b' and key_is_delete):
                    # '@Delete "t"' and '@Delete "c"' fields; handled normally below
                    pass
                elif (position == 'b' and not key_is_delete) or (position == 'c' and key_is_delete):
                    done = True
                else:
                    raise Exception('Unreachable code reached. Please close the black hole nearby.')

        #logging.debug('%s[%d] >===> %s[%d]' % (repr(start_elem), start_offset, repr(end_elem), end_offset))

        if not done:
            start_tree_offset = self.elem.gui_info.gui_to_tree_index(start_offset)
            end_tree_offset = self.elem.gui_info.gui_to_tree_index(end_offset)
            deleted, parent, index = self.elem.delete_range(start_tree_offset, end_tree_offset)

            if index is not None:
                parent_offset = self.elem.gui_info.index(parent)
                if parent_offset < 0:
                    parent_offset = 0

                if hasattr(deleted, 'gui_info'):
                    length = deleted.gui_info.length()
                else:
                    length = len(deleted)

                # Take the parent placeable's starting widget into account
                if hasattr(parent, 'gui_info') and parent.gui_info.has_start_widget():
                    parent_offset += 1

                start_offset = parent_offset + index
                end_offset = parent_offset + index + length
                self.refresh_cursor_pos = start_offset
            else:
                self.refresh_cursor_pos = self.elem.gui_info.tree_to_gui_index(start_offset)

        if index is None:
            index = start_offset

        if deleted:
            self.elem.prune()
            self.emit(
                'text-deleted', deleted, parent, index,
                self.buffer.props.cursor_position, self.elem
            )

    def _on_insert_text(self, buffer, iter, ins_text, length):
        if self.elem is None:
            return

        ins_text = data.forceunicode(ins_text[:length])
        buff_offset = iter.get_offset()
        gui_info = self.elem.gui_info
        left = gui_info.elem_at_offset(buff_offset-1)
        right = gui_info.elem_at_offset(buff_offset)

        #logging.debug('"%s[[%s]]%s" | elem=%s[%d] | left=%s right=%s' % (
        #    buffer.get_text(buffer.get_start_iter(), iter),
        #    ins_text,
        #    buffer.get_text(iter, buffer.get_end_iter()),
        #    repr(self.elem), buff_offset,
        #    repr(left), repr(right)
        #))

        succeeded = False
        if not (left is None and right is None) and (left is not right or not unicode(left)):
            succeeded = self.elem.insert_between(left, right, ins_text)
            #logging.debug('self.elem.insert_between(%s, %s, "%s"): %s' % (repr(left), repr(right), ins_text, succeeded))
        if not succeeded and left is not None and left is right and left.isleaf():
            # This block handles the special case where a the cursor is just
            # inside a leaf element with a closing widget. In this case both
            # left and right will point to the element in question, but it
            # need not be empty to be a leaf. Because the cursor is still
            # "inside" the element, we want to append to this leaf in stead
            # of after it, which is what StringElem.insert() will do, seeing
            # as the position before and after the widget is the same to in
            # the context of StringElem.
            anchor = iter.get_child_anchor()
            if anchor:
                widgets = anchor.get_widgets()
                left_widgets = left.gui_info.widgets
                if len(widgets) > 0 and len(left_widgets) > 1 and \
                        widgets[0] is left_widgets[1] and \
                        iter.get_offset() == self.elem.gui_info.length() - 1:
                    succeeded = left.insert(len(left), ins_text)
                    #logging.debug('%s.insert(len(%s), "%s")' % (repr(left), repr(left), ins_text))
        if not succeeded:
            offset = gui_info.gui_to_tree_index(buff_offset)
            succeeded = self.elem.insert(offset, ins_text)
            #logging.debug('self.elem.insert(%d, "%s"): %s' % (offset, ins_text, succeeded))

        if succeeded:
            self.elem.prune()
            cursor_pos = self.refresh_cursor_pos
            if cursor_pos < 0:
                cursor_pos = self.buffer.props.cursor_position
            cursor_pos += len(ins_text)
            self.refresh_cursor_pos = cursor_pos
            #logging.debug('text-inserted: %s@%d of %s' % (ins_text, iter.get_offset(), repr(self.elem)))
            self.emit('text-inserted', ins_text, buff_offset, self.elem)

    def _on_key_pressed(self, widget, event, *args):
        evname = None

        if self.suggestion_is_visible():
            if event.keyval == gtk.keysyms.Tab:
                self.hide_suggestion()
                self.buffer.insert(
                    self.buffer.get_iter_at_offset(self.suggestion['offset']),
                    self.suggestion['text']
                )
                self.suggestion = None
                return True
            self.suggestion = None

        # Uncomment the following block to get nice textual logging of key presses in the textbox
        #keyname = '<unknown>'
        #for attr in dir(gtk.keysyms):
        #    if getattr(gtk.keysyms, attr) == event.keyval:
        #        keyname = attr
        #statenames = []
        #for attr in [a for a in ('MOD1_MASK', 'MOD2_MASK', 'MOD3_MASK', 'MOD4_MASK', 'MOD5_MASK', 'CONTROL_MASK', 'SHIFT_MASK', 'RELEASE_MASK', 'LOCK_MASK', 'SUPER_MASK', 'HYPER_MASK', 'META_MASK')]:
        #    if event.state & getattr(gtk.gdk, attr):
        #        statenames.append(attr)
        #statenames = '|'.join(statenames)
        #logging.debug('Key pressed: %s (%s)' % (keyname, statenames))
        #logging.debug('state (raw): %x' % (event.state,))

        # Filter out unimportant flags that is present with other keyboard
        # layouts and input methods. The following has been encountered:
        # * MOD2_MASK - Num Lock (bug 926)
        # * LEAVE_NOTIFY_MASK - Arabic keyboard layout (?) (bug 926)
        # * 0x2000000 - IBus input method (bug 1281)
        filtered_state = event.state & (gtk.gdk.CONTROL_MASK | gtk.gdk.MOD1_MASK | gtk.gdk.MOD4_MASK | gtk.gdk.SHIFT_MASK)

        for name, keyslist in self.SPECIAL_KEYS.items():
            for keyval, state in keyslist:
                if event.keyval == keyval and filtered_state == state:
                    evname = name

        if evname == 'alt-left':
            self.move_elem_selection(-1)
        elif evname == 'alt-right':
            self.move_elem_selection(1)

        return self.emit('key-pressed', event, evname)

    def _on_event_remove_suggestion(self, *args):
        self.suggestion = None


    # SPECIAL METHODS #
    def __repr__(self):
        return '<TextBox %x %s "%s">' % (id(self), self.role, unicode(self.elem))
