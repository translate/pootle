#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Zuza Software Foundation
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

import sys
import os

from django.utils.translation import ugettext as _
N_ = _

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.conf import settings

# get versions
import django
from translate import __version__ as toolkitversion
from pootle import __version__ as pootleversion



def view(request):
    data = {
        'description': _(settings.DESCRIPTION),
        'keywords' : [ 'Pootle',
                       'locamotion',
                       'translate',
                       'translation',
                       'localisation',
                       'localization',
                       'l10n',
                       'traduction',
                       'traduire',
                       ],
        'versiontext': ("""
        Pootle %s<br />
        Translate Toolkit %s<br />
        Django %s<br />
        Python %s<br />
        Running on %s/%s
        """ % (pootleversion.sver,
              toolkitversion.sver,
              django.get_version(),
              sys.version,
              sys.platform,
              os.name,
              )),
        }
                         
    return render_to_response('index/about.html', data, context_instance=RequestContext(request))

