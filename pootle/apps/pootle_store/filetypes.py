#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2013 Zuza Software Foundation
# Copyright 2013 Evernote Corporation
#
# This file is part of Pootle.
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

"""Helper functions for translation file formats support."""

from django.utils.translation import ugettext_lazy as _


def get_supported_formats():
    formats = []

    # Bilingual formats
    from translate.storage.po import pofile
    formats.append(('po', _('Gettext PO'), pofile, 'bilingual'))

    try:
        from translate.storage.xliff import xlifffile
        formats.append(('xlf', _('XLIFF'), xlifffile, 'bilingual'))
        formats.append(('xliff', _('XLIFF'), xlifffile, 'bilingual'))
    except ImportError:
        pass

    try:
        from translate.storage.ts2 import tsfile
        formats.append(('ts', _('Qt ts'), tsfile, 'bilingual'))
    except ImportError:
        pass

    try:
        from translate.storage.tmx import tmxfile
        formats.append(('tmx', _('TMX'), tmxfile, 'bilingual'))
    except ImportError:
        pass

    try:
        from translate.storage.tbx import tbxfile
        formats.append(('tbx', _('TBX'), tbxfile, 'bilingual'))
    except ImportError:
        pass

    try:
        from translate.storage.catkeys import CatkeysFile
        formats.append(('catkeys', _('Haiku catkeys'), CatkeysFile, 'bilingual'))
    except ImportError:
        pass

    try:
        from translate.storage.csvl10n import csvfile
        formats.append(('csv', _('Excel CSV'), csvfile, 'bilingual'))
    except ImportError:
        pass

    try:
        from translate.storage.mozilla_lang import LangStore
        formats.append(('lang', _('Mozilla .lang'), LangStore, 'bilingual'))
    except ImportError:
        pass

    # Monolingual formats

    # FIXME: It's impossible to use both properties and UTF-8 properties
    # formats: they share the same key. For more information see bug 1918.
    try:
        from translate.storage.properties import javafile
        formats.append(('properties', _('Java Properties'), javafile,
                        'monolingual'))
    except ImportError:
        from translate.storage.properties import propfile
        formats.append(('properties', _('Java Properties'), propfile,
                        'monolingual'))
    try:
        from translate.storage.properties import javautf8file
        formats.append(('properties', _('Java Properties (UTF-8)'),
                        javautf8file, 'monolingual'))
    except ImportError:
        pass

    try:
        from translate.storage.properties import stringsfile
        # Translators: Don't translate "strings" unless you are sure these
        # files have another name in your language
        formats.append(('strings', _('OS X Strings'), stringsfile,
                        'monolingual'))
    except ImportError:
        pass

    from translate.storage.php import phpfile
    formats.append(('php', _('PHP arrays'), phpfile, 'monolingual'))

    try:
        from translate.storage.subtitles import (SubRipFile, MicroDVDFile,
                                                 AdvSubStationAlphaFile,
                                                 SubStationAlphaFile)
        formats.append(('srt', _('Subtitles: srt'), SubRipFile,
                        'monolingual'))
        formats.append(('sub', _('Subtitles: sub'), MicroDVDFile,
                        'monolingual'))
        formats.append(('ssa', _('Subtitles: ssa'), SubStationAlphaFile,
                        'monolingual'))
        formats.append(('ass', _('Subtitles: ass'), AdvSubStationAlphaFile,
                        'monolingual'))
    except ImportError:
        pass

    return formats

supported_formats = get_supported_formats()


def get_filetype_choices():
    return [(format[0], format[1]) for format in supported_formats]

filetype_choices = get_filetype_choices()


def get_factory_classes():
    classes = dict(((format[0], format[2]) for format in supported_formats))

    # Add template formats manually
    from translate.storage.po import pofile
    classes['pot'] = pofile

    return classes

factory_classes = get_factory_classes()


def is_monolingual(klass):
    classes = dict(((format[2], format[3]) for format in supported_formats))
    return classes.get(klass, 'bilingual') == 'monolingual'
