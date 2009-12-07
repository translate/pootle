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

from django.utils.translation import ugettext as _

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
        'pootle_version': _("Pootle %(pootle_ver)s is powered by Translate Toolkit %(toolkit_ver)s",
            {'pootle_ver': pootleversion.sver, 'toolkit_ver': toolkitversion.sver}),
        'version_details': "\n".join([
            "Django %s" % django.get_version(),
            "Python %s" % sys.version,
            "Running on %s" % sys.platform,
        ])
    }

    return render_to_response('index/about.html', data, context_instance=RequestContext(request))
