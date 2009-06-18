#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2008 Zuza Software Foundation
# 
# This file is part of translate.
#
# translate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""The functions here match the methods of the same name in jToolkit. They
are provided to make it easier to deal with legacy code in Pootle.

They all use our gettext module to get hold of the Pootle project object
which is associated with the thread in which we are running. The Pootle
project is then used to perform the translations."""

from translate.lang import data as langdata
from pootle.i18n import gettext

# Taken from jToolkit
def localize(message, *variables):
    if variables:
        try:
            return gettext.get_active().ugettext(message) % variables
        except:
            return message % variables
    else:
        return gettext.get_active().ugettext(message)

# Taken from jToolkit
def nlocalize(singular, plural, n, *variables):
    """returns the localized form of a plural message, falls back to
    original if failure with variables"""
    if variables:
        try:
            return gettext.get_active().ungettext(singular, plural, n) % variables
        except:
            if n != 1:
                return plural % variables
            else:
                return singular % variables
    else:
        return gettext.get_active().ungettext(singular, plural, n)

