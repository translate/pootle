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

import gtk
import gtk.gdk
import pango
from translate.storage.placeables import base, StringElem, general, xliff

from virtaal.views.widgets.storeviewwidgets import make_pango_layout

import rendering


class StringElemGUI(object):
    """
    A convenient container for all GUI properties of a L{StringElem}.
    """

    # MEMBERS #
    fg = '#000' # See PlaceablesController._on_style_set
    """The current foreground colour.
        @see PlaceablesController._on_style_set"""
    bg = '#fff'
    """The current background colour.
        @see PlaceablesController._on_style_set"""

    cursor_allowed = True
    """Whether the cursor is allowed to enter this element."""


    # INITIALIZERS #
    def __init__(self, elem, textbox, **kwargs):
        if not isinstance(elem, StringElem):
            raise ValueError('"elem" parameter must be a StringElem.')
        self.elem = elem
        self.textbox = textbox
        self.widgets = []
        self.create_repr_widgets()

        attribs = ('fg', 'bg', 'cursor_allowed')
        for kw in kwargs:
            if kw in attribs:
                setattr(self, kw, kwargs[kw])

    # METHODS #
    def create_tags(self):
        tag = gtk.TextTag()
        if self.fg:
            tag.props.foreground = self.fg

        if self.bg:
            tag.props.background = self.bg

        return [(tag, None, None)]

    def create_repr_widgets(self):
        """Creates the two widgets that are rendered before and after the
            contained string. The widgets should be placed in C{self.widgets}."""
        return None

    def copy(self):
        return self.__class__(
            elem=self.elem, textbox=self.textbox,
            fg=self.fg, bg=self.bg,
            cursor_allowed=self.cursor_allowed
        )

    def elem_at_offset(self, offset, child_offset=0):
        """Find the C{StringElem} at the given offset.
            This method is used in Virtaal as a replacement for
            C{StringElem.elem_at_offset}, because this method takes the rendered
            widgets into account.

            @type  offset: int
            @param offset: The offset into C{self.textbox} to find the the element
            @type  child_offset: int
            @param child_offset: The offset of C{self.elem} into the buffer of
                C{self.textbox}. This is so recursive calls to child elements
                can be aware of where in the textbox it appears."""
        if offset < 0 or offset >= self.length():
            return None

        pre_len = (self.widgets and self.widgets[0]) and 1 or 0

        # First check if offset doesn't point to a widget that does not belong to self.elem
        if offset in (0, self.length()-1):
            anchor = self.textbox.buffer.get_iter_at_offset(child_offset+offset).get_child_anchor()
            if anchor is not None:
                widget = anchor.get_widgets()

                if len(widget) > 0:
                    widget = widget[0]

                    # The list comprehension below is used, in stead of a simple "w in self.widgets",
                    # because we want to use "is" comparison in stead of __eq__.
                    if widget is not None and [w for w in self.widgets if w is widget]:
                        return self.elem
                    if self.elem.isleaf():
                        # If there's a widget at {offset}, but it does not belong to this widget or
                        # any of its children (it's a leaf, so no StringElem children), the widget
                        # can't be part of the sub-tree with {self.elem} at the root.
                        return None

        if self.elem.isleaf():
            return self.elem

        child_offset += pre_len
        offset -= pre_len

        childlen = 0 # Length of the children already consumed
        for child in self.elem.sub:
            if isinstance(child, StringElem):
                if not hasattr(child, 'gui_info'):
                    gui_info_class = self.textbox.placeables_controller.get_gui_info(child)
                    child.gui_info = gui_info_class(elem=child, textbox=self.textbox)

                try:
                    elem = child.gui_info.elem_at_offset(offset-childlen, child_offset=child_offset+childlen)
                    if elem is not None:
                        return elem
                except AttributeError:
                    pass
                childlen += child.gui_info.length()
            else:
                if offset <= len(child):
                    return self.elem
                childlen += len(child)

        return None

    def get_insert_widget(self):
        return None

    def gui_to_tree_index(self, index):
        # The difference between a GUI offset and a tree offset is the iter-
        # consuming widgets in the text box. So we just iterate from the start
        # of the text buffer and count the positions without widgets.
        i = 0
        itr = self.textbox.buffer.get_start_iter()
        while itr.get_offset() < index and not itr.is_end():
            if itr.get_child_anchor() is None:
                i += 1
            itr.forward_char()
        return i

    def has_start_widget(self):
        return len(self.widgets) > 0 and self.widgets[0]

    def has_end_widget(self):
        return len(self.widgets) > 1 and self.widgets[1]

    def index(self, elem):
        """Replacement for C{StringElem.elem_offset()} to be aware of included
            widgets."""
        if elem is self.elem:
            return 0

        i = 0
        if len(self.widgets) > 0 and isinstance(self.widgets[0], gtk.Widget):
            i = 1
        for child in self.elem.sub:
            if isinstance(child, StringElem):
                index = child.gui_info.index(elem)
                if index >= 0:
                    return index + i
                i += child.gui_info.length()
            else:
                i += len(child)
        return -1

    def length(self):
        """Calculate the length of the current element, taking into account
            possibly included widgets."""
        length = len([w for w in self.widgets if w is not None])
        for child in self.elem.sub:
            if isinstance(child, StringElem) and hasattr(child, 'gui_info'):
                length += child.gui_info.length()
            else:
                length += len(child)
        return length

    def render(self, offset=-1):
        """Render the string element string and its associatd widgets."""
        buffer = self.textbox.buffer
        if offset < 0:
            offset = 0
            buffer.set_text('')

        if len(self.widgets) >= 1 and self.widgets[0]:
            anchor = buffer.create_child_anchor(buffer.get_iter_at_offset(offset))
            self.textbox.add_child_at_anchor(self.widgets[0], anchor)
            self.widgets[0].show()
            offset += 1

        for child in self.elem.sub:
            if isinstance(child, StringElem):
                child.gui_info.render(offset)
                offset += child.gui_info.length()
            else:
                buffer.insert(buffer.get_iter_at_offset(offset), child)
                offset += len(child)

        if len(self.widgets) >= 2:
            anchor = buffer.create_child_anchor(buffer.get_iter_at_offset(offset))
            self.textbox.add_child_at_anchor(self.widgets[1], anchor)
            self.widgets[1].show()
            offset += 1

        return offset

    def tree_to_gui_index(self, index):
        if index == 0:
            return 0
        if index == len(self.elem):
            return self.textbox.buffer.get_end_iter().get_offset()
        char_counter = 0
        converted = 0
        itr = self.textbox.buffer.get_start_iter()

        while char_counter <= index and not itr.is_end():
            anchor = itr.get_child_anchor()
            if anchor is None or not anchor.get_widgets():
                char_counter += 1
            converted += 1
            itr.forward_char()
        return converted-1


class PhGUI(StringElemGUI):
    fg = 'darkred'
    bg = '#f7f7f7'


class BxGUI(StringElemGUI):
    bg = '#E6E6FA'

    def create_repr_widgets(self):
        self.widgets.append(gtk.Label('(('))

        for lbl in self.widgets:
            font_desc = self.textbox.style.font_desc
            lbl.modify_font(font_desc)
            self.textbox.get_pango_context().set_font_description(font_desc)
            w, h = make_pango_layout(self.textbox, u'((', 100).get_pixel_size()
            lbl.set_size_request(-1, int(h/1.2))


class ExGUI(StringElemGUI):
    bg = '#E6E6FA'

    def create_repr_widgets(self):
        self.widgets.append(gtk.Label('))'))

        for lbl in self.widgets:
            font_desc = self.textbox.style.font_desc
            lbl.modify_font(font_desc)
            self.textbox.get_pango_context().set_font_description(font_desc)
            w, h = make_pango_layout(self.textbox, u'))', 100).get_pixel_size()
            lbl.set_size_request(-1, int(h/1.2))


class NewlineGUI(StringElemGUI):
    SCALE_FACTOR = 1.2 # Experimentally determined

    def create_repr_widgets(self):
        lbl = gtk.Label(u'¶')
        lbl.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse('grey')) # foreground is light grey
        font_desc = self.textbox.style.font_desc
        lbl.modify_font(font_desc)
        self.textbox.get_pango_context().set_font_description(font_desc)
        w, h = make_pango_layout(self.textbox, u'¶', 100).get_pixel_size()
        lbl.set_size_request(-1, int(h/1.2))
        self.widgets.append(lbl)


class UrlGUI(StringElemGUI):
    fg = '#0000ff'
    bg = '#ffffff'

    def create_tags(self):
        tag = gtk.TextTag()
        tag.props.foreground = self.fg
        tag.props.background = self.bg
        tag.props.underline = pango.UNDERLINE_SINGLE
        return [(tag, None, None)]


class GPlaceableGUI(StringElemGUI):
    bg = '#ffd27f'

    def create_repr_widgets(self):
        self.widgets.append(gtk.Label('<'))
        self.widgets.append(gtk.Label('>'))
        if self.elem.id:
            self.widgets[0].set_text('<%s|' % (self.elem.id))

        for lbl in self.widgets:
            font_desc = self.textbox.style.font_desc
            lbl.modify_font(font_desc)
            self.textbox.get_pango_context().set_font_description(font_desc)
            w, h = make_pango_layout(self.textbox, u'<foo>', 100).get_pixel_size()
            lbl.set_size_request(-1, int(h/1.2))


class XPlaceableGUI(StringElemGUI):
    bg = '#ff7fef'

    def create_repr_widgets(self):
        lbl = gtk.Label('[]')
        self.widgets.append(lbl)
        if self.elem.id:
            lbl.set_text('[%s]' % (self.elem.id))

        font_desc = self.textbox.style.font_desc
        lbl.modify_font(font_desc)
        self.textbox.get_pango_context().set_font_description(font_desc)
        w, h = make_pango_layout(self.textbox, u'[foo]', 100).get_pixel_size()
        lbl.set_size_request(-1, int(h/1.2))


class UnknownXMLGUI(StringElemGUI):
    bg = '#add8e6'

    def create_repr_widgets(self):
        self.widgets.append(gtk.Label('{'))
        self.widgets.append(gtk.Label('}'))

        info = ''
        if self.elem.xml_node.tag:
            tag = self.elem.xml_node.tag
            if tag.startswith('{'):
                # tag is namespaced
                tag = tag[tag.index('}')+1:]
            info += tag + '|'
        # Uncomment the if's below for more verbose placeables
        #if self.elem.id:
        #    info += 'id=%s|'  % (self.elem.id)
        #if self.elem.rid:
        #    info += 'rid=%s|' % (self.elem.rid)
        #if self.elem.xid:
        #    info += 'xid=%s|' % (self.elem.xid)
        if info:
            self.widgets[0].set_text('{%s' % (info))

        for lbl in self.widgets:
            lbl.modify_font(rendering.get_role_font_description(self.textbox.role))
            w, h = make_pango_layout(self.textbox, u'{foo}', 100).get_pixel_size()
            lbl.set_size_request(-1, int(h/1.2))

element_gui_map = [
    (general.NewlinePlaceable, NewlineGUI),
    (general.UrlPlaceable, UrlGUI),
    (general.EmailPlaceable, UrlGUI),
    (base.Ph, PhGUI),
    (base.Bx, BxGUI),
    (base.Ex, ExGUI),
    (base.G, GPlaceableGUI),
    (base.X, XPlaceableGUI),
    (xliff.UnknownXML, UnknownXMLGUI),
]
