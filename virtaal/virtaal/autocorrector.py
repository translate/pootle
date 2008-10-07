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

"""Contains the AutoCorrector class."""

import gobject
import gtk
import os
import re
import zipfile
from lxml import etree

import undo_buffer


class AutoCorrector(object):
    """
    Does auto-correction on editable text widgets using OpenOffice.org auto-
    correction files.
    """

    wordsep_re = re.compile('\W+', re.UNICODE)

    REPLACEMENT, REGEX = range(2)

    def __init__(self, lang='', acorpath=None):
        """Create a new AutoCorrector instance and load the OpenOffice.org
            auto-correction diction for language code 'lang'.

            @type  lang: str
            @param lang: The code of the language to load auto-correction data
                for. See M{load_dictionary} for more information about how this
                parameter is used.
            @type  acorpath: str
            @param acorpath: The path to the directory containing the
                OpenOffice.org auto-correction data files (acor_*.dat).
            """
        self.lang = None
        if acorpath is None or not os.path.isdir(acorpath):
            acorpath = os.path.curdir
        self.acorpath = acorpath
        self.load_dictionary(lang)
        self.widgets = set()

    def add_widget(self, widget):
        """Add a widget (currently only C{gtk.TextView}s are accepted) to the
            list of widgets to do auto-correction for.
            """
        if not self.correctiondict:
            return # No dictionary to work with, so we can't handle any widgets

        if widget in self.widgets:
            return # Widget already added

        if isinstance(widget, gtk.TextView):
            self._add_textview(widget)
            return

        raise ValueError("Widget type %s not supported." % (type(widget)))

    def autocorrect(self, src, endindex, inserted=u''):
        """Apply auto-correction to source string.

            @type  src: basestring
            @param src: The candidate-string for auto-correction.
            @type  endindex: int
            @param endindex: The logical end of the string. ie. The part of the
                string _before_ this index tested for the presence of a
                correctable string.
            @type  inserted: basestring
            @param inserted: The string that was inserted at I{endindex}

            @rtype: 2-tuple
            @return: The corrected substring (C{src[:endindex]}) (or None if no
                corrections were made) and the postfix
                (C{inserted + src[endindex:]}).
            """
        if not self.correctiondict:
            return None, u''

        candidate = src[:endindex]
        postfix = inserted + src[endindex:]

        for key in self.correctiondict:
            if self.correctiondict[key][self.REGEX].match(candidate):
                replacement = self.correctiondict[key][self.REPLACEMENT]
                corrected   = re.sub(r'%s$' % (re.escape(key)), replacement, candidate)
                return corrected, postfix

        return None, postfix # No corrections done

    def clear_widgets(self):
        """Removes references to all widgets that is being auto-corrected."""
        for w in set(self.widgets):
            self.remove_widget(w)

    def load_dictionary(self, lang):
        """Load the OpenOffice.org auto-correction dictionary for language
            'lang'.

            OpenOffice.org's auto-correction data files are in named in the
            format "acor_I{lang}-I{country}.dat", where I{lang} is the ISO
            language code and I{country} the country code. This function can
            handle (for example) "af", "af_ZA" or "af-ZA" to load the Afrikaans
            data file. Here are the steps taken in trying to find the correct
            data file:
              - Underscores are replaced with hyphens in C{lang} ("af_ZA" ->
                "af-ZA").
              - The file for C{lang} is opened ("acor_af-ZA.dat").
              - If the open fails, the language code ("af") is extracted and the
                first file found starting with "acor_af" and ending in ".dat" is
                used.

            These steps imply that if "af" is given as lang, the data file
            "acor_af-ZA.dat" will end up being loaded.
            """
        # Change "af_ZA" to "af-ZA", which OOo uses to store acor files.
        if lang == self.lang:
            return

        if not lang:
            self.correctiondict = {}
            self.lang = ''
            return

        lang = lang.replace('_', '-')
        try:
            acor = zipfile.ZipFile(os.path.join(self.acorpath, 'acor_%s.dat' % lang))
        except IOError, _exc:
            # Try to find a file that starts with 'acor_%s' % (lang[0]) (where
            # lang[0] is the part of lang before the '-') and ends with '.dat'
            langparts = lang.split('-')
            filenames = [fn for fn in os.listdir(self.acorpath) if fn.startswith('acor_%s' % langparts[0])
                                                                   and fn.endswith('.dat')]
            for fn in filenames:
                try:
                    acor = zipfile.ZipFile(os.path.join(self.acorpath, fn))
                    break
                except IOError:
                    pass

            else:
                # If no acceptable auto-correction file was found, we create an
                # empty dictionary.
                self.correctiondict = {}
                self.lang = ''
                return

        xmlstr = acor.read('DocumentList.xml')
        xml = etree.fromstring(xmlstr)
        # Sample element from DocumentList.xml (it has no root element!):
        #   <block-list:block block-list:abbreviated-name="teh" block-list:name="the"/>
        # This means that xml.iterchildren() will return an iterator over all
        # of <block-list> elements and entry.values() will return a 2-tuple
        # with the values of the "abbreviated-name" and "name" attributes.
        # That is how I got to the simple line below.
        self.correctiondict = dict([entry.values() for entry in xml.iterchildren()])

        # Add auto-correction regex for each loaded word.
        for key, value in self.correctiondict.items():
            self.correctiondict[key] = (value, re.compile(r'.*\b%s$' % (re.escape(key)), re.UNICODE))

        self.lang = lang
        return

    def remove_widget(self, widget):
        """Remove a widget (currently only C{gtk.TextView}s are accepted) from
            the list of widgets to do auto-correction for.
            """
        if not self.correctiondict:
            return

        if isinstance(widget, gtk.TextView) and widget in self.widgets:
            self._remove_textview(widget)

    def set_widgets(self, widget_collection):
        """Replace the widgets being auto-corrected with the collection given."""
        self.clear_widgets()
        for w in widget_collection:
            self.add_widget(w)

    def _add_textview(self, textview):
        """Add the given I{gtk.TextView} to the list of widgets to do auto-
            correction on.
            """
        if not hasattr(self, '_textbuffer_handler_ids'):
            self._textbuffer_handler_ids = {}

        handler_id = textview.get_buffer().connect(
            'insert-text',
            self._on_insert_text
        )
        self._textbuffer_handler_ids[textview] = handler_id
        self.widgets.add(textview)

    def _on_insert_text(self, buffer, iter, text, length):
        bufftext = unicode(buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter()))
        iteroffset = iter.get_offset() + len(text)

        if not self.wordsep_re.split(text)[-1]:
            res, postfix = self.autocorrect(bufftext, iter.get_offset(), text)
            if res is not None:
                # Updating of the buffer is deferred until after this signal
                # and its side effects are taken care of. We abuse
                # gobject.idle_add for that.
                def correct_text():
                    buffer.props.text = u''.join([res, postfix])
                    buffer.place_cursor( buffer.get_iter_at_offset(len(res) + len(text)) )
                    undo_buffer.merge_actions(buffer, iteroffset)
                    return False

                gobject.idle_add(correct_text)

    def _remove_textview(self, textview):
        """Remove the given C{gtk.TextView} from the list of widgets to do
            auto-correction on.
            """
        if not hasattr(self, '_textbuffer_handler_ids'):
            return
        # Disconnect the "insert-text" event handler
        textview.get_buffer().disconnect(self._textbuffer_handler_ids[textview])
        self.widgets.remove(textview)
