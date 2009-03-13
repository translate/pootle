#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2006 Zuza Software Foundation
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

from django.contrib.auth.models import User
from django.conf import settings
from django.utils.translation import ugettext as _
N_ = _

from translate.filters import checks

from pootle_app.models import get_profile, Project
from pootle_app.profile import PootleProfile
from pootle_app import project_tree

from Pootle.i18n.jtoolkit_i18n import tr_lang
from Pootle import pagelayout
from Pootle import projects
from Pootle import pan_app

import locale

class AdminPage(pagelayout.PootlePage):
  """page for administering pootle..."""
  def __init__(self, request):
    self.request = request
    templatename = "adminindex"
    instancetitle = pan_app.get_title()
    text = self.gettext(request)
    templatevars = {
        "options": self.getoptions(),
        "pagetitle": _("Pootle Admin Page"),
        "instancetitle": instancetitle,
        "text": text}
    pagelayout.PootlePage.__init__(self, templatename, templatevars, request)

  def gettext(self, request):
    """Localize the text"""
    text = {}
    text["home"] = _("Home")
    text["users"] = _("Users")
    text["languages"] = _("Languages")
    text["projects"] = _("Projects")
    text["generaloptions"] = _("General options")
    text["option"] = _("Option")
    text["currentvalue"] = _("Current value")
    text["savechanges"] = _("Save changes")
    return text
    
  def getoptions(self):
    optiontitles = {"TITLE":       _("Title"), 
                    "DESCRIPTION": _("Description"),
                    "BASE_URL":    _("Base URL"),
                    "MEDIA_URL":   _("Media URL"),
                    "HOMEPAGE":    _("Home Page")}
    option_values = {"TITLE":       pan_app.get_title(),
                     "DESCRIPTION": pan_app.get_description()}
    options = []
    for optionname, optiontitle in optiontitles.items():
      optionvalue = getattr(settings, optionname, option_values.get(optionname, ""))
      option = {"name": "option-%s" % optionname, "title": optiontitle, "value": optionvalue}
      options.append(option)
    return options

