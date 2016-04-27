# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

"""Helper functions for translation file formats support."""

from django.utils.translation import ugettext_lazy as _


def get_supported_formats():
    formats = []

    # Bilingual formats
    from translate.storage.po import pofile
    formats.append(('po', _('Gettext PO'), pofile, 'bilingual'))

    try:
        from translate.storage.xliff import xlifffile
        formats.append(('xlf', _('XLIFF (.xlf)'), xlifffile, 'bilingual'))
        formats.append(('xliff', _('XLIFF (.xliff)'), xlifffile, 'bilingual'))
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
        formats.append(('catkeys', _('Haiku catkeys'), CatkeysFile,
                        'bilingual'))
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
