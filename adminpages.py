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

from Pootle import pagelayout
from Pootle import projects
from translate.filters import checks
from django.contrib.auth.models import User
from Pootle import pan_app
from pootle_app.models import get_profile, Project
from Pootle.i18n.jtoolkit_i18n import localize, tr_lang

import locale

class AdminPage(pagelayout.PootlePage):
  """page for administering pootle..."""
  def __init__(self, request):
    self.potree = pan_app.get_po_tree()
    self.request = request
    templatename = "adminindex"
    instancetitle = getattr(pan_app.prefs, "title", localize("Pootle Demo"))
    text = self.gettext(request)
    templatevars = {
        "options": self.getoptions(),
        "instancetitle": instancetitle,
        "text": text}
    pagelayout.PootlePage.__init__(self, templatename, templatevars, request)

  def gettext(self, request):
    """Localize the text"""
    text = {}
    text["home"] = localize("Home")
    text["users"] = localize("Users")
    text["languages"] = localize("Languages")
    text["projects"] = localize("Projects")
    text["generaloptions"] = localize("General options")
    text["option"] = localize("Option")
    text["currentvalue"] = localize("Current value")
    text["savechanges"] = localize("Save changes")
    return text
    
  def getoptions(self):
    optiontitles = {"title": localize("Title"), 
                    "description": localize("Description"),
                    "baseurl": localize("Base URL"),
                    "homepage": localize("Home Page")}
    options = []
    for optionname, optiontitle in optiontitles.items():
      optionvalue = getattr(pan_app.prefs, optionname, "")
      option = {"name": "option-%s" % optionname, "title": optiontitle, "value": optionvalue}
      options.append(option)
    return options

def updaterights(project, request, argdict):
  if "admin" in project.getrights(request.user):
    if "doupdaterights" in request.POST:
      for key, value in request.POST.lists():
        if isinstance(key, str):
          key = key.decode("utf-8")
        if key.startswith("rights-"):
          username = key.replace("rights-", "", 1)
          user = User.objects.include_hidden().get(username=username)
          if isinstance(value, list):
            try:
              value.remove("existence")
            except:
              pass
          project.setrights(user, value)
        if key.startswith("rightsremove-"):
          username = key.replace("rightsremove-", "", 1)
          user = User.objects.include_hidden().get(username=username)
          project.delrights(user)
      username = request.POST.get("rightsnew-username", None)
      if username:
        username = username.strip()
        try:
          user = User.objects.include_hidden().get(username=username)
          project.setrights(user, request.POST.get("rightsnew", ""))
        except User.DoesNotExist:
          raise IndexError(localize("Cannot set rights for username %s - user does not exist", username))
 
class TranslationProjectAdminPage(pagelayout.PootlePage):
  """admin page for a translation project (project+language)"""
  def __init__(self, project, request, argdict):
    self.potree = pan_app.get_po_tree()
    self.project = project
    self.request = request
    self.rightnames = self.project.getrightnames(request)

    if "admin" not in project.getrights(request.user):
      raise projects.Rights404Error

    try:
      if "scanpofiles" in argdict:
        self.project.scanpofiles()
    except:
      pass

    updaterights(project, request, argdict)
    # l10n: This is the page title. The first parameter is the language name, the second parameter is the project name
    pagetitle = localize("Pootle Admin: %s %s", self.project.languagename, self.project.projectname)
    main_link = localize("Project home page")
    rescan_files_link = localize("Rescan project files")
    norights_text = localize("You do not have the rights to administer this project.")
    templatename = "projectlangadmin"
    instancetitle = getattr(pan_app.prefs, "title", localize("Pootle Demo"))
    templatevars = {"pagetitle": pagetitle, "norights_text": norights_text,
        "project": {"code": self.project.projectcode, "name": self.project.projectname},
        "language": {"code": self.project.languagecode, "name": self.project.languagename},
        "main_link": main_link,
        "rescan_files_link": rescan_files_link,
        "instancetitle": instancetitle}
    templatevars.update(self.getoptions())
    pagelayout.PootlePage.__init__(self, templatename, templatevars, request, bannerheight=80)

  def getoptions(self):
    """returns a box that describes the options"""
    self.project.readprefs()
    if self.project.filestyle == "gnu":
      filestyle_text = localize("This is a GNU-style project (one directory, files named per language).")
    else:
      filestyle_text = localize("This is a standard style project (one directory per language).")
    permissions_title = localize("User Permissions")
    username_title = localize("Username")
    adduser_text = localize("(select to add user)")
    rights_title = localize("Rights")
    remove_title = localize("Remove")
    nobodyrights = self.project.getrights(User.objects.include_hidden().get(username='nobody'))
    nobody_dict = self.getuserdict("nobody", delete=False)
    defaultrights = self.project.getrights(User.objects.include_hidden().get(username='default'))
    default_dict = self.getuserdict("default", delete=False)
    users_with_rights = ["nobody", "default"]
    rights = {"nobody": nobodyrights, "default": defaultrights}
    for username in self.project.getuserswithrights():
      if username in ("nobody", "default"): continue
      users_with_rights.append(username)
      rights[username] = self.project.getrights(User.objects.include_hidden().get(username=username))
    users = self.project.getuserswithinterest()
    user_details = {"nobody": nobody_dict, "default": default_dict}
    for username, usernode in users.iteritems():
      if not isinstance(username, unicode):
        username = username.decode("utf-8")
      user_dict = self.getuserdict(username, usernode=usernode)
      user_details[username] = user_dict
    # We need to make sure that users_with_rights are also in user_details,
    # since they might not be there yet or anymore
    for username in users_with_rights:
      if username in user_details:
        continue
      user_dict = self.getuserdict(username, usernode=None)
      user_details[username] = user_dict
    users_without_rights = [username for username in user_details if username not in users_with_rights]
    newuser_dict = self.getuserdict(None, delete=False)
    updaterights_text = localize("Update Rights")
    return {"filestyle_text": filestyle_text,
            "permissions_title": permissions_title,
            "username_title": username_title,
            "rights_title": rights_title,
            "remove_title": remove_title,
            "users_with_rights": users_with_rights,
            "users_without_rights": users_without_rights,
            "user_details": user_details,
            "rights": rights,
            "newuser": newuser_dict,
            "updaterights_text": updaterights_text,
            "rightnames": self.rightnames,
            "adduser_text": adduser_text,
           }

  def getuserdict(self, username, delete=True, usernode=None):
    """gets a dictionary for the given user given user's rights"""
    # l10n: The parameter is a languagecode, projectcode or username
    remove_text = localize("Remove %s", username)
    description = getattr(usernode, "description", None) or username
    userdict = {"username": username, "delete": delete or None, "remove_text": remove_text, "description": description}
    return userdict

