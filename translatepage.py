#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2004-2006 Zuza Software Foundation
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

import re
import difflib
import operator
import urllib
import os
import copy

from django.contrib.auth.models import User
from django.utils.html import urlize
from django.utils.translation import ugettext as _
from django.conf import settings
N_ = _

from translate.storage import po
from translate.misc.multistring import multistring

from pootle_app.core import Language
from pootle_app.profile import get_profile
from pootle_app.views.common import navbar_dict
from pootle_app.url_manip import URL, URLState

from Pootle import pagelayout
from Pootle import projects
from Pootle import pootlefile
from Pootle import pan_app
from Pootle.i18n.jtoolkit_i18n import localize, tr_lang

xml_re = re.compile("&lt;.*?&gt;")

def oddoreven(polarity):
  if polarity % 2 == 0:
    return "even"
  elif polarity % 2 == 1:
    return "odd"

