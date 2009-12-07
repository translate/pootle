#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008 Zuza Software Foundation
#
# This file is part of Spelt.
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

"""All exceptions used in Spelt."""

# Model-related exceptions
class DuplicateModelError(StandardError):
    """Raised if a model with the same ID as another is found."""
    pass

class IDUsedError(StandardError):
    """Raised when a strict ID is requested by a model, but already taken."""
    pass

class InvalidElementError(StandardError):
    """Thrown by an XMLModel when an attempt is made to use an invalid element
    in its from_xml() method."""
    pass

class InvalidSectionError(StandardError):
    """Raised if an invalid section was specified."""
    pass

class LanguageDBFormatError(StandardError):
    """There is something wrong with a language database's format."""
    pass

class LanguageDBFormatWarning(UserWarning):
    """Warning raised when a non-critical language database formatting issue is
    found. Such as no /language_database/users/* (XPath) path found."""
    pass

class PartOfSpeechError(StandardError):
    """Raised on any part of speech related error."""
    pass

class RootError(StandardError):
    """Raised on any word root related error."""
    pass

class UnknownIDError(StandardError):
    """Raised when an unclaimed ID is being deleted."""
    pass

class UnknownModelError(StandardError):
    """Raised when an unknown model was specified somewhere."""
    pass
