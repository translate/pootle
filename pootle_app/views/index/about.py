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
try:
# ElementTree is part of Python 2.5, so let's try that first
    from xml.etree import ElementTree
except ImportError:
    from elementtree import ElementTree

from kid import __version__ as kidversion

from translate import __version__ as toolkitversion

from pootle_app.views.util import render_jtoolkit
from pootle_app.views.indexpage import shortdescription

from Pootle import pagelayout
from Pootle import pan_app
from Pootle import __version__ as pootleversion
from Pootle.legacy.jToolkit import __version__ as jtoolkitversion

def view(request):
    return render_jtoolkit(AboutPage(request))

class AboutPage(pagelayout.PootlePage):

    """the bar at the side describing current login details etc"""

    def __init__(self, request):
        pagetitle = pan_app.get_title()
        description = pan_app.get_description()
        meta_description = shortdescription(description)
        keywords = [
            'Pootle',
            'locamotion',
            'translate',
            'translation',
            'localisation',
            'localization',
            'l10n',
            'traduction',
            'traduire',
            ]
        abouttitle = _('About Pootle')
        # l10n: Take care to use HTML tags correctly. A markup error
        # could cause a display error.
        introtext = \
            _("<strong>Pootle</strong> is a simple web portal that should allow you to <strong>translate</strong>! Since Pootle is <strong>Free Software</strong>, you can download it and run your own copy if you like. You can also help participate in the development in many ways (you don't have to be able to program)."
              )
        hosttext = \
            _('The Pootle project itself is hosted at <a href="http://translate.sourceforge.net/">translate.sourceforge.net</a> where you can find the details about source code, mailing lists etc.'
              )
        # l10n: If your language uses right-to-left layout and you
        # leave the English untranslated, consider enclosing the
        # necessary text with <span dir="ltr">.......</span> to help
        # browsers to display it correctly. l10n: Take care to use
        # HTML tags correctly. A markup error could cause a display
        # error.
        nametext = \
            _('The name stands for <b>PO</b>-based <b>O</b>nline <b>T</b>ranslation / <b>L</b>ocalization <b>E</b>ngine, but you may need to read <a href="http://www.thechestnut.com/flumps.htm">this</a>.'
              )
        versiontitle = _('Versions')
        # l10n: If your language uses right-to-left layout and you
        # leave the English untranslated, consider enclosing the
        # necessary text with <span dir="ltr">.......</span> to help
        # browsers to display it correctly. l10n: Take care to use
        # HTML tags correctly. A markup error could cause a display
        # error.
        versiontext = \
            _('This site is running:<br />Pootle %s<br />Translate Toolkit %s<br />jToolkit %s<br />Kid %s<br />ElementTree %s<br />Python %s (on %s/%s)'
               % (
            pootleversion.ver,
            toolkitversion.sver,
            jtoolkitversion.ver,
            kidversion,
            ElementTree.VERSION,
            sys.version,
            sys.platform,
            os.name,
            ))
        templatename = 'index/about.html'
        instancetitle = pan_app.get_title()
        templatevars = {
            'pagetitle': pagetitle,
            'description': description,
            'meta_description': meta_description,
            'keywords': keywords,
            'abouttitle': abouttitle,
            'introtext': introtext,
            'hosttext': hosttext,
            'nametext': nametext,
            'versiontitle': versiontitle,
            'versiontext': versiontext,
            'instancetitle': instancetitle,
            }
        pagelayout.PootlePage.__init__(self, templatename, templatevars,
                                       request)
