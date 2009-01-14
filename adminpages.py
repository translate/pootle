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

class LanguagesAdminPage(pagelayout.PootlePage):
  """page for administering pootle..."""
  def __init__(self, request):
    self.potree = pan_app.get_po_tree()
    self.request = request
    templatename = "adminlanguages"
    instancetitle = getattr(pan_app.prefs, "title", localize("Pootle Demo"))
    pagetitle = localize("Pootle Languages Admin Page")
    text = self.gettext(request)
    templatevars = {"pagetitle": pagetitle, "languages": self.getlanguagesoptions(), "options": self.getoptions(), "instancetitle": instancetitle, "text": text}
    pagelayout.PootlePage.__init__(self, templatename, templatevars, request)

  def gettext(self, request):
    """Localize the text"""
    text = {}
    text["home"] = localize("Home")
    text["admin"] = localize("Main admin page")
    text["languages"] = localize("Languages")
    text["savechanges"] = localize("Save changes")
    return text
    
  def getoptions(self):
    options = [{"name": "code", "title": localize("ISO Code"), "size": 6, "newvalue": ""},
               {"name": "name", "title": localize("Full Name"), 
                                "newvalue": localize("(add language here)")},
               {"name": "specialchars", "title": localize("Special Chars"), "newvalue": localize("(special characters)")},
               {"name": "nplurals", "title": localize("Number of Plurals"), "newvalue": localize("(number of plurals)")},
               {"name": "pluralequation", "title": localize("Plural Equation"), "newvalue": localize("(plural equation)")},
               {"name": "remove", "title": localize("Remove Language")}]
    for option in options:
      if "newvalue" in option:
        option["newname"] = "newlanguage" + option["name"]
    return options

  def getlanguagesoptions(self):
    languages = []
    for languagecode, languagename in self.potree.getlanguages():
      languagespecialchars = self.potree.getlanguagespecialchars(languagecode)
      languagenplurals = self.potree.getlanguagenplurals(languagecode)
      languagepluralequation = self.potree.getlanguagepluralequation(languagecode)
      languageremove = None
      # TODO: make label work like this
      # l10n: The parameter is a languagecode, projectcode or username
      removelabel = localize("Remove %s", languagecode)
      languageoptions = [{"name": "languagename-%s" % languagecode, "value": languagename, "type": "text"},
                         {"name": "languagespecialchars-%s" % languagecode, "value": languagespecialchars, "type": "text"},
                         {"name": "languagenplurals-%s" % languagecode, "value": languagenplurals, "type": "text"},
                         {"name": "languagepluralequation-%s" % languagecode, "value": languagepluralequation, "type": "text"},
                         {"name": "languageremove-%s" % languagecode, "value": languageremove, "type": "checkbox", "label": removelabel}]
      languages.append({"code": languagecode, "options": languageoptions})
    return languages

class ProjectsAdminPage(pagelayout.PootlePage):
  """page for administering pootle..."""
  def __init__(self, request):
    self.potree = pan_app.get_po_tree()
    self.request = request
    templatename = "adminprojects"
    projectfiletypes = ["po","xlf"]
    self.allchecks = [{"value": check, "description": check} for check in checks.projectcheckers.keys()]
    self.allchecks.insert(0, {"value": "", "description": localize("Standard")})
    self.alltypes = [{"value": check, "description": check} for check in projectfiletypes]
    instancetitle = getattr(pan_app.prefs, "title", localize("Pootle Demo"))
    pagetitle = localize("Pootle Projects Admin Page")
    text = self.gettext(request)
    templatevars = {"pagetitle": pagetitle, "projects": self.getprojectsoptions(), "options": self.getoptions(), "instancetitle": instancetitle, "text": text}
    pagelayout.PootlePage.__init__(self, templatename, templatevars, request)

  def gettext(self, request):
    """Localize the text"""
    text = {}
    text["home"] = localize("Home")
    text["admin"] = localize("Main admin page")
    text["projects"] = localize("Projects")
    text["savechanges"] = localize("Save changes")
    return text

  def getoptions(self):
    options = [{"name": "code", "title": localize("Project Code"), "size": 6, "newvalue": ""},
               {"name": "name", "title": localize("Full Name"), 
                                "newvalue": localize("(add project here)")},
               {"name": "description", "title": localize("Project Description"), "newvalue": localize("(project description)")},
               {"name": "ignoredfiles", "title": localize("Ignored Files"), "newvalue": localize("(comma separated list)")},
               {"name": "checkerstyle", "title": localize("Checker Style"), "selectoptions": self.allchecks, "newvalue": ""},
               {"name": "filetype", "title": localize("File Type"), "selectoptions": self.alltypes, "newvalue": ""},
               {"name": "createmofiles", "title": localize("Create MO Files"), "type": "checkbox", "newvalue": "True"},
               {"name": "remove", "title": localize("Remove Project")}]
    for option in options:
      if "newvalue" in option:
        option["newname"] = "newproject" + option["name"]
      if "type" not in option and "selectoptions" not in option:
        option["type"] = "text"
    return options

  def getprojectsoptions(self):
    projects = []
    for project in Project.objects.all():
      projectadminlink = "../projects/%s/admin.html" % project.code
      if project.createmofiles:
        create_mo_files_checkbox = {"name": "projectcreatemofiles-%s" % project.code, "checked": "yes", "type": "checkbox"}
      else:
        create_mo_files_checkbox = {"name": "projectcreatemofiles-%s" % project.code, "type": "checkbox"}
      projectremove = None
      # l10n: The parameter is a languagecode, projectcode or username
      removelabel = localize("Remove %s", project.code)
      projectoptions = [{"name": "projectname-%s" % project.code, "value": project.fullname, "type": "text"},
                        {"name": "projectdescription-%s" % project.code, "value": project.description, "type": "text"},
                        {"name": "projectignoredfiles-%s" % project.code, "value": project.ignoredfiles, "type": "text"},
                        {"name": "projectcheckerstyle-%s" % project.code, "value": project.checkstyle, "selectoptions": self.allchecks},
                        {"name": "projectfiletype-%s" % project.code, "value": project.localfiletype, "selectoptions": self.alltypes},
                        create_mo_files_checkbox,
                        {"name": "projectremove-%s" % project.code, "value": projectremove, "type": "checkbox", "label": removelabel}]
      projects.append({"code": project.code, "adminlink": projectadminlink, "options": projectoptions})
    return projects

class UsersAdminPage(pagelayout.PootlePage):
  """page for administering pootle..."""
  def __init__(self, server, request):
    self.server = server
    self.request = request
    templatename = "adminusers"
    instancetitle = getattr(pan_app.prefs, "title", localize("Pootle Demo"))
    pagetitle = localize("Pootle User Admin Page")
    text = self.gettext(request)
    templatevars = {"pagetitle": pagetitle, "users": self.getusersoptions(), "options": self.getoptions(), "instancetitle": instancetitle, "text": text}
    pagelayout.PootlePage.__init__(self, templatename, templatevars, request)

  def gettext(self, request):
    """Localize the text"""
    text = {}
    text["home"] = localize("Home")
    text["admin"] = localize("Main admin page")
    text["users"] = localize("Users")
    text["savechanges"] = localize("Save changes")
    return text
    
  def getoptions(self):
    options = [{"name": "name", "title": localize("Username"), "newvalue": "", "size": 6},
               {"name": "fullname", "title": localize("Full Name"), 
                                    "newvalue": localize("(add full name here)")},
               {"name": "email", "title": localize("Email Address"), "newvalue": localize("(add email here)")},
               {"name": "password", "title": localize("Password"), "newvalue": localize("(add password here)")},
               {"name": "activated", "title": localize("Activated"), "type": "checkbox", "checked": "true", "newvalue": "", "label": localize("Activate New User")},
               {"name": "logintype", "title": localize("Login Type"), "newvalue": "hash"},
               {"name": "remove", "title": localize("Remove User"), "type": "checkbox"}]
    for option in options:
      if "newvalue" in option:
        # TODO: rationalize this in the form processing
        if option["name"] == "activated":
          option["newname"] = "newuseractivate"
        else:
          option["newname"] = "newuser" + option["name"]
    return options

  def getusersoptions(self):
    users = []
    q = User.objects.order_by('username')
    for usernode in q: 
      username = usernode.username
      fullname = usernode.first_name
      email    = usernode.email
      # TODO: Decide what to write here
      logintype = "XXX"
      activated = usernode.is_active
      if activated:
        activatedattr = "checked"
      else:
        activatedattr = ""
      userremove = None
      # l10n: The parameter is a languagecode, projectcode or username
      removelabel = localize("Remove %s", username)
      useroptions = [{"name": "username-%s" % username, "value": fullname, "type": "text"},
                     {"name": "useremail-%s" % username, "value": email, "type": "text"},
                     {"name": "userpassword-%s" % username, "value": None, "type": "text"},
                     {"name": "useractivated-%s" % username, "type": "checkbox", activatedattr: activatedattr},
                     {"name": "userlogintype-%s" % username, "value": logintype, "type": "text"},
                     {"name": "userremove-%s" % username, "value": None, "type": "checkbox", "label": removelabel}]
      users.append({"code": username, "options": useroptions})
    return users

class ProjectAdminPage(pagelayout.PootlePage):
  """list of languages belonging to a project"""
  def __init__(self, projectcode, request, argdict):
    self.potree = pan_app.get_po_tree()
    self.projectcode = projectcode
    self.request = request
    projectname = self.potree.getprojectname(self.projectcode)
    if request.user.is_superuser:
      if "doaddlanguage" in argdict:
        newlanguage = argdict.get("newlanguage", None)
        if not newlanguage:
          raise ValueError("You must select a new language")
        self.potree.addtranslationproject(newlanguage, self.projectcode)
      if "doupdatelanguage" in argdict:
        languagecodes = argdict.get("updatelanguage", None)
        if not languagecodes:
          raise ValueError("No languagecode given in doupdatelanguage")
        if isinstance(languagecodes, (str, unicode)):
          languagecodes = [languagecodes]
        for languagecode in languagecodes:
          translationproject = self.potree.getproject(languagecode, self.projectcode)
          translationproject.converttemplates(self.request)
      if "initialize" in argdict:
        languagecodes = argdict.get("updatelanguage", None)
        if not languagecodes:
          raise ValueError("No languagecode given in doupdatelanguage")
        if isinstance(languagecodes, (str, unicode)):
          languagecodes = [languagecodes]
        for languagecode in languagecodes:
          translationproject = self.potree.getproject(languagecode, self.projectcode)
          translationproject.initialize(self.request, languagecode)

    main_link = localize("Back to main page")
    existing_title = localize("Existing languages")
    existing_languages = self.getexistinglanguages()
    new_languages = self.getnewlanguages()
    # l10n: This refers to updating the translation files from the templates like with .pot files
    update_button = localize("Update Languages")
    pagetitle = localize("Pootle Admin: %s", projectname)
    norights_text = localize("You do not have the rights to administer this project.")
    iso_code = localize("ISO Code")
    full_name = localize("Full Name")
    # l10n: This refers to updating the translation files from the templates like with .pot files
    update_link = localize("Update from templates")
    # l10n: This refers to running an intialization script for the given project+locale
    initialize_link = localize("Initialize")
    templatename = "projectadmin"
    instancetitle = getattr(pan_app.prefs, "title", localize("Pootle Demo"))
    templatevars = {"pagetitle": pagetitle, "norights_text": norights_text,
        "project": {"code": projectcode, "name": projectname},
        "iso_code": iso_code, "full_name": full_name,
        "existing_title": existing_title, "existing_languages": existing_languages,
        "new_languages": new_languages,
        "update_button": update_button, "add_button": localize("Add Language"),
        "main_link": main_link, "update_link": update_link, 
        "initialize_link": initialize_link,
        "instancetitle": instancetitle}
    pagelayout.PootlePage.__init__(self, templatename, templatevars, request, bannerheight=80)

  def getexistinglanguages(self):
    """gets the info on existing languages"""
    languages = self.potree.getlanguages(self.projectcode)
    languageitems = [{"code": languagecode, "name": tr_lang(languagename)} for languagecode, languagename in languages]
    # rewritten for compatibility with Python 2.3
    # languageitems.sort(cmp=locale.strcoll, key=lambda dict: dict["name"])
    languageitems.sort(lambda x,y: locale.strcoll(x["name"], y["name"]))
    for n, item in enumerate(languageitems):
      item["parity"] = ["even", "odd"][n % 2]
    return languageitems

  def getnewlanguages(self):
    """returns a box that lets the user add new languages"""
    existingcodes = self.potree.getlanguagecodes(self.projectcode)
    allcodes = self.potree.getlanguagecodes()
    newcodes = [code for code in allcodes if not (code in existingcodes or code == "templates")]
    newoptions = [(self.potree.getlanguagename(code), code) for code in newcodes]
    newoptions.sort()
    newoptions = [{"code": code, "name": tr_lang(languagename)} for (languagename, code) in newoptions]
    # rewritten for compatibility with Python 2.3
    # newoptions.sort(cmp=locale.strcoll, key=lambda dict: dict["name"])
    newoptions.sort(lambda x,y: locale.strcoll(x["name"], y["name"]))
    return newoptions

def updaterights(project, request, argdict):
  if "admin" in project.getrights(request.user):
    if "doupdaterights" in request.POST:
      for key, value in request.POST.lists():
        if isinstance(key, str):
          key = key.decode("utf-8")
        if key.startswith("rights-"):
          username = key.replace("rights-", "", 1)
          user = User.objects.get(username=username)
          if isinstance(value, list):
            try:
              value.remove("existence")
            except:
              pass
          project.setrights(user, value)
        if key.startswith("rightsremove-"):
          username = key.replace("rightsremove-", "", 1)
          user = User.objects.get(username=username)
          project.delrights(user)
      username = request.POST.get("rightsnew-username", None)
      if username:
        username = username.strip()
        try:
          user = User.objects.get(username=username)
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
    nobodyrights = self.project.getrights(User.objects.get(username='nobody'))
    nobody_dict = self.getuserdict("nobody", delete=False)
    defaultrights = self.project.getrights(User.objects.get(username='default'))
    default_dict = self.getuserdict("default", delete=False)
    users_with_rights = ["nobody", "default"]
    rights = {"nobody": nobodyrights, "default": defaultrights}
    for username in self.project.getuserswithrights():
      if username in ("nobody", "default"): continue
      users_with_rights.append(username)
      rights[username] = self.project.getrights(User.objects.get(username=username))
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

