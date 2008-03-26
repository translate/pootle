#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2007 Zuza Software Foundation
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

"""A class loader that will load C or Python implementations of the PO class
depending on the use_implementation variable

Use the environment variable USECPO to choose the C implementation which
uses Gettext's libgettextpo for high parsing speed.  Otherise the local 
Python based parser is used (slower but very well tested)"""

import os
import sys

if os.getenv('USECPO'):
    if os.getenv('USECPO') == "1":
        print >> sys.stderr, "Using cPO"
        from cpo import *
    else:
        print >> sys.stderr, "Using Python PO"
        from pypo import *
else:
    from pypo import *

