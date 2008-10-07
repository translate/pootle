#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2007-2008 Zuza Software Foundation
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

__all__ = ['build_layout', 'get_targets', 'get_options']

import logging
import re

import gtk
try:
    import gtkspell
except ImportError, e:
    gtkspell = None

import pan_app
import rendering
import markup
import undo_buffer
from support.partial import partial
from widgets import label_expander, util
from terminology import get_terminology_matcher


def get_sources(widget):
    def add_sources_to_list(lst):
        def do(widget):
            if '_is_source' in widget.__dict__:
                lst.append(widget)
        return do

    result = []
    util.forall_widgets(add_sources_to_list(result), widget)
    return result

def get_targets(widget):
    def add_targets_to_list(lst):
        def do(widget):
            if '_is_target' in widget.__dict__:
                lst.append(widget)
        return do

    result = []
    util.forall_widgets(add_targets_to_list(result), widget)
    return result

def get_options(widget):
    def add_options_to_list(lst):
        def do(widget):
            if isinstance(widget, gtk.CheckButton):
                lst.append(widget)
        return do

    result = []
    util.forall_widgets(add_options_to_list(result), widget)
    return result


#A regular expression to help us find a meaningful place to position the
#cursor initially.
first_word_re = re.compile("(?m)(?u)^(<[^>]+>|\\\\[nt]|[\W$^\n])*(\\b|\\Z)")

def focus_text_view(text_view):
    text_view.grab_focus()

    buf = text_view.get_buffer()
    text = buf.get_text(buf.get_start_iter(), buf.get_end_iter())

    translation_start = first_word_re.match(text).span()[1]
    buf.place_cursor(buf.get_iter_at_offset(translation_start))

################################################################################

def add_events(widget):
    def on_key_press_event(widget, event, *_args):
        if event.keyval == gtk.keysyms.Return or event.keyval == gtk.keysyms.KP_Enter:
            widget.parent.emit('key-press-event', event)
            return True
        return False

    # Skip Enter key processing
    widget.connect('key-press-event', on_key_press_event)
    return widget

def layout(left=None, middle=None, right=None):
    table = gtk.Table(rows=1, columns=4, homogeneous=True)
    if left != None:
        table.attach(left, 0, 1, 0, 1, xoptions=gtk.FILL|gtk.EXPAND, yoptions=gtk.FILL)
    if middle != None:
        table.attach(middle, 1, 3, 0, 1, xoptions=gtk.FILL|gtk.EXPAND, yoptions=gtk.FILL)
    if right != None:
        table.attach(right, 3, 4, 0, 1, xoptions=gtk.FILL|gtk.EXPAND, yoptions=gtk.FILL)
    return add_events(table)

def fill_list(lst, children):
    for child in children:
        lst.pack_start(child, fill=True, expand=False)
    return lst

def vlist(*children):
    return add_events(fill_list(gtk.VBox(), children))

def hlist(*children):
    return fill_list(gtk.HBox(), children)

def add_spell_checking(text_view, language):
    global gtkspell
    if gtkspell:
        try:
            spell = gtkspell.Spell(text_view)
            spell.set_language(language)
        except:
            logging.info("Could not initialize spell checking")
            gtkspell = None
    return text_view

def set_text(text_view, txt):
    text_view.get_buffer().set_text(markup.escape(txt))
    return text_view

def text_view(editable):
    text_view = gtk.TextView()
    text_view.set_editable(editable)
    text_view.set_wrap_mode(gtk.WRAP_WORD)
    text_view.set_border_window_size(gtk.TEXT_WINDOW_TOP, 1)
    return text_view

def scrolled_window(widget, scroll_vertical=gtk.POLICY_AUTOMATIC, add_viewport=False):
    scrolled_window = gtk.ScrolledWindow()
    scrolled_window.set_policy(gtk.POLICY_NEVER, scroll_vertical)
    if not add_viewport:
        scrolled_window.add(widget)
    else:
        scrolled_window.add_with_viewport(widget)
    return add_events(scrolled_window)

def make_scrolled_text_view(get_text, editable, scroll_vertical, language):
    return scrolled_window(
               add_spell_checking(
                   set_text(
                       text_view(editable),
                       get_text()),
                   pan_app.settings.language[language]),
               scroll_vertical)

def source_text_box(get_text, set_text):
    scrolled_window = make_scrolled_text_view(get_text, False, gtk.POLICY_NEVER, "sourcelang")
    text_view = scrolled_window.get_child()
    text_view.modify_font(rendering.get_source_font_description())
    # This causes some problems, so commented out for now
    #text_view.get_pango_context().set_font_description(rendering.get_source_font_description())
    text_view.get_pango_context().set_language(rendering.get_source_language())
    text_view._is_source = True
    return scrolled_window

def target_text_box(get_text, set_text, source_text):
    def get_range(buf, left_offset, right_offset):
        return buf.get_text(buf.get_iter_at_offset(left_offset),
                            buf.get_iter_at_offset(right_offset))

    def on_text_view_n_press_event(text_view, event):
        """Handle special keypresses in the textarea."""
        # Automatically move to the next line if \n is entered

        if event.keyval == gtk.keysyms.n:
            buf = text_view.get_buffer()
            if get_range(buf, buf.props.cursor_position-1, buf.props.cursor_position) == "\\":
                buf.insert_at_cursor('n\n')
                text_view.scroll_mark_onscreen(buf.get_insert())
                return True
        return False

    def on_change(buf):
        set_text(markup.unescape(buf.get_text(buf.get_start_iter(), buf.get_end_iter())))

    scrolled_window = make_scrolled_text_view(get_text, True, gtk.POLICY_AUTOMATIC, "contentlang")
    text_view = scrolled_window.get_child()
    text_view.modify_font(rendering.get_target_font_description())
    text_view.get_pango_context().set_font_description(rendering.get_target_font_description())
    text_view.get_pango_context().set_language(rendering.get_target_language())
    text_view.connect('key-press-event', on_text_view_n_press_event)
    text_view._is_target = True
    text_view._source_text = source_text

    buf = undo_buffer.add_undo_to_buffer(text_view.get_buffer())
    undo_buffer.execute_without_signals(buf, lambda: buf.set_text(markup.escape(get_text())))
    buf.connect('changed', on_change)

    return scrolled_window

def connect_target_text_views(child):
    def target_key_press_event(text_view, event, next_text_view):
        if event.keyval == gtk.keysyms.Return or event.keyval == gtk.keysyms.KP_Enter:
            focus_text_view(next_text_view)
            return True
        return False

    def end_target_key_press_event(text_view, event, *_args):
        if event.keyval == gtk.keysyms.Return or event.keyval == gtk.keysyms.KP_Enter:
            text_view.parent.emit('key-press-event', event)
            return True
        return False

    targets = get_targets(child)
    for target, next_target in zip(targets, targets[1:]):
        target.connect('key-press-event', target_key_press_event, next_target)
    targets[-1].connect('key-press-event', end_target_key_press_event)
    return child

def comment(get_text, set_text=lambda value: None):
    text_box = source_text_box(get_text, set_text)
    return label_expander.LabelExpander(text_box, get_text)

def option(label, get_option, set_option):
    def on_toggled(widget, *_args):
        if widget.get_active():
            set_option(True)
        else:
            set_option(False)

    check_button = gtk.CheckButton(label=label)
    check_button.connect('toggled', on_toggled)
    check_button.set_active(get_option())
    # FIXME: not allowing focus willprobably raise various issues related to keyboard accesss.
    check_button.set_property("can-focus", False)
    return check_button

def terminology_source(txt):
    label = gtk.Label()
    label.set_justify(gtk.JUSTIFY_RIGHT)
    label.set_markup("<b>%s</b>:" % txt)
    return label

def terminology_target(txt):
    label = gtk.Label()
    label.set_justify(gtk.JUSTIFY_LEFT)
    label.set_text(txt)
    return label

def list_model(types, data_list):
    model = gtk.ListStore(*types)
    for data_row in data_list:
        last_row = model.append()
        for i, data_element in enumerate(data_row):
            model.set(last_row, i, data_element)
    return model

def treeview(model):
    v = gtk.TreeView(model)
    v.set_headers_visible(False)
    text_renderer = gtk.CellRendererText()
    for i in xrange(model.get_n_columns()):
        v.append_column(gtk.TreeViewColumn(None, text_renderer, text=i))
    return v

def terminology_grid(matches):
    return treeview(list_model([str, str], ((unicode(u.source), unicode(u.target)) for u in matches)))

def terminology_list(sources):
    matcher = get_terminology_matcher(pan_app.settings.language["contentlang"])
    results = matcher.matches(" ".join(sources))
    if len(results) > 0:
        return scrolled_window(terminology_grid(results))
    else:
        return None

################################################################################

def build_layout(unit, nplurals):
    """Construct a blueprint which can be used to build editor widgets
    or to compute the height required to display editor widgets; this
    latter operation is required by the TreeView.

    @param unit: A translation unit used by the translate toolkit.
    @param nplurals: The number of plurals in the
    """

    def get(multistring, unit, i):
        if unit.hasplural():
            return multistring.strings[i]
        elif i == 0:
            return multistring
        else:
            raise IndexError()

    def get_source(unit, index):
        return get(unit.source, unit, index)

    def get_target(unit, nplurals, index):
        if unit.hasplural() and nplurals != len(unit.target.strings):
            targets = nplurals * [u""]
            targets[:len(unit.target.strings)] = unit.target.strings
            unit.target = targets
        return get(unit.target, unit, index)

    def set(unit, attr, index, value):
        if unit.hasplural():
            str_list = list(getattr(unit, attr).strings)
            str_list[index] = value
            setattr(unit, attr, str_list)
        elif index == 0:
            setattr(unit, attr, value)
        else:
            raise IndexError()

    def set_source(unit, index, value):
        set(unit, 'source', index, value)

    def set_target(unit, index, value):
        set(unit, 'target', index, value)

    def num_sources(unit):
        if unit.hasplural():
            return len(unit.source.strings)
        return 1

    def num_targets(unit, nplurals):
        if unit.hasplural():
            return nplurals
        return 1

    first_source = source_text_box(partial(get_source, unit, 0), partial(set_source, unit, 0))

    sources = [source_text_box(partial(get_source, unit, i), partial(set_source, unit, i))
               for i in xrange(num_sources(unit))]

    targets = [target_text_box(partial(get_target, unit, nplurals, i), partial(set_target, unit, i), unit.source)
               for i in xrange(num_targets(unit, nplurals))]

    widget = layout(
               middle=vlist(
                 comment(partial(unit.getnotes, 'programmer')),
                 vlist(*sources),
                 comment(unit.getcontext),
                 connect_target_text_views(
                    vlist(*targets)),
                 comment(partial(unit.getnotes, 'translator')),
                 option(_('F_uzzy'), unit.isfuzzy, unit.markfuzzy)),
               right=terminology_list([get_source(unit, i) for i in xrange(num_sources(unit))]))

    widget.sources = sources
    widget.target = targets
    return widget

