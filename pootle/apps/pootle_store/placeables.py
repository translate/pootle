#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Zuza Software Foundation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# Pootle is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# Pootle; if not, see <http://www.gnu.org/licenses/>.

import re

from translate.storage.placeables import general
from translate.storage.placeables.base import Ph

from django.utils.translation import ugettext_lazy as _


PLACEABLE_DESCRIPTIONS = {
    # Pootle placeables.
    'PootleTabEscapePlaceable': _("Escaped tab"),
    'PootleEscapePlaceable': _("Escaped sequence"),
    'PootleSpacesPlaceable': _("Unusual space in string"),

    # Translate Toolkit placeables.
    'AltAttrPlaceable': _("'alt' attribute inside XML tag"),
    'NewlinePlaceable': _("New-line"),
    'NumberPlaceable': _("Number"),
    'QtFormattingPlaceable': _("Qt string formatting variable"),
    'PythonFormattingPlaceable': _("Python string formatting variable"),
    'JavaMessageFormatPlaceable': _("Java Message formatting variable"),
    'FormattingPlaceable': _("String formatting variable"),
    'UrlPlaceable': _("URI"),
    'FilePlaceable': _("File location"),
    'EmailPlaceable': _("Email"),
    'PunctuationPlaceable': _("Punctuation"),
    'XMLEntityPlaceable': _("XML entity"),
    'CapsPlaceable': _("Long all-caps string"),
    'CamelCasePlaceable': _("Camel case string"),
#    'SpacesPlaceable': _("Unusual space in string"),  # Not used.
    'XMLTagPlaceable': _("XML tag"),
    'OptionPlaceable': _("Command line option"),
}


class PootleTabEscapePlaceable(Ph):
    """Placeable handling tab escapes."""
    istranslatable = False
    regex = re.compile(r'\t')
    parse = classmethod(general.regex_parse)


class PootleEscapePlaceable(Ph):
    """Placeable handling escapes."""
    istranslatable = False
    regex = re.compile(r'\\')
    parse = classmethod(general.regex_parse)


class PootleSpacesPlaceable(Ph):
    """Placeable handling spaces."""
    istranslatable = False
    regex = re.compile('^ +| +$|[\r\n\t] +| {2,}')
    parse = classmethod(general.regex_parse)


PLACEABLE_PARSERS = [
    PootleTabEscapePlaceable.parse,
    PootleEscapePlaceable.parse,
    general.NewlinePlaceable.parse,
    # The spaces placeable can match '\n  ' and mask the newline, so must come
    # later.
    PootleSpacesPlaceable.parse,
    general.XMLTagPlaceable.parse,
    general.AltAttrPlaceable.parse,
    general.XMLEntityPlaceable.parse,
    general.PythonFormattingPlaceable.parse,
    general.JavaMessageFormatPlaceable.parse,
    general.FormattingPlaceable.parse,
    # The Qt variables can consume the %1 in %1$s which will mask a printf
    # placeable, so it has to come later.
    general.QtFormattingPlaceable.parse,
    general.UrlPlaceable.parse,
    general.FilePlaceable.parse,
    general.EmailPlaceable.parse,
    general.CapsPlaceable.parse,
    general.CamelCasePlaceable.parse,
    general.OptionPlaceable.parse,
    general.PunctuationPlaceable.parse,
    general.NumberPlaceable.parse,
]
