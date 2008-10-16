# -*- coding: utf-8 -*-
# 
# Copyright 2005 Zuza Software Foundation
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

"""module to handle consistent file locations for Pootle"""

import os.path
import sys
import imp

def check_if_frozen():
    return (hasattr(sys, "frozen") or # new py2exe
            hasattr(sys, "importers") # old py2exe
            or imp.is_frozen("__main__")) # tools/freeze

is_frozen = check_if_frozen()
# same directory as this file (or the executable under py2exe)
if is_frozen:
  pootledir = os.path.abspath(os.path.dirname(sys.executable))
  jtoolkitdir = os.path.abspath(os.path.dirname(sys.executable))
else:
  from jToolkit import __version__ as jtoolkitversion
  pootledir = os.path.abspath(os.path.dirname(__file__))
  jtoolkitdir = os.path.dirname(jtoolkitversion.__file__)

# default prefs file is pootle.prefs in the pootledir
prefsfile = os.path.join(pootledir, 'pootle.prefs')

htmldir = os.path.join(pootledir, "html")
templatedir = os.path.join(pootledir, "templates")
sys.path.append(templatedir) # So kid can find our templates

