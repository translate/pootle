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

import locale

class AdminPage(pagelayout.PootlePage):
  """page for administering pootle..."""
  def __init__(self, potree, session, instance):
    self.potree = potree
    self.session = session
    self.instance = instance
    self.localize = session.localize
    templatename = "adminindex"
    sessionvars = {"status": self.session.status, "isopen": self.session.isopen, "issiteadmin": self.session.issiteadmin()}
    instancetitle = getattr(self.instance, "title", session.localize("Pootle Demo"))
    text = self.gettext(session)
    templatevars = {"options": self.getoptions(), "session": sessionvars, "instancetitle": instancetitle, "text": text}
    pagelayout.PootlePage.__init__(self, templatename, templatevars, session)

  def gettext(self, session):
    """Localize the text"""
    text = {}
    text["home"] = session.localize("Home")
    text["users"] = session.localize("Users")
    text["languages"] = session.localize("Languages")
    text["projects"] = session.localize("Projects")
    text["generaloptions"] = session.localize("General options")
    text["option"] = session.localize("Option")
    text["currentvalue"] = session.localize("Current value")
    text["savechanges"] = session.localize("Save changes")
    return text
    
  def getoptions(self):
    optiontitles = {"title": self.localize("Title"), 
                    "description": self.localize("Description"),
                    "baseurl": self.localize("Base URL"),
                    "homepage": self.localize("Home Page")}
    options = []
    for optionname, optiontitle in optiontitles.items():
      optionvalue = getattr(self.instance, optionname, "")
      option = {"name": "option-%s" % optionname, "title": optiontitle, "value": optionvalue}
      options.append(option)
    return options

class LanguagesAdminPage(pagelayout.PootlePage):
  """page for administering pootle..."""
  def __init__(self, potree, session, instance):
    self.potree = potree
    self.session = session
    self.instance = instance
    self.localize = session.localize
    templatename = "adminlanguages"
    sessionvars = {"status": self.session.status, "isopen": self.session.isopen, "issiteadmin": self.session.issiteadmin()}
    instancetitle = getattr(self.instance, "title", session.localize("Pootle Demo"))
    text = self.gettext(session)
    templatevars = {"languages": self.getlanguagesoptions(), "options": self.getoptions(), "session": sessionvars, "instancetitle": instancetitle, "text": text}
    pagelayout.PootlePage.__init__(self, templatename, templatevars, session)

  def gettext(self, session):
    """Localize the text"""
    text = {}
    text["home"] = session.localize("Home")
    text["admin"] = session.localize("Main admin page")
    text["languages"] = session.localize("Languages")
    text["savechanges"] = session.localize("Save changes")
    return text
    
  def getoptions(self):
    options = [{"name": "code", "title": self.localize("ISO Code"), "size": 6, "newvalue": ""},
               {"name": "name", "title": self.localize("Full Name"), 
                                "newvalue": self.localize("(add language here)")},
               {"name": "specialchars", "title": self.localize("Special Chars"), "newvalue": self.localize("(special characters)")},
               {"name": "nplurals", "title": self.localize("Number of Plurals"), "newvalue": self.localize("(number of plurals)")},
               {"name": "pluralequation", "title": self.localize("Plural Equation"), "newvalue": self.localize("(plural equation)")},
               {"name": "remove", "title": self.localize("Remove Language")}]
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
      removelabel = self.localize("Remove %s", languagecode)
      languageoptions = [{"name": "languagename-%s" % languagecode, "value": languagename, "type": "text"},
                         {"name": "languagespecialchars-%s" % languagecode, "value": languagespecialchars, "type": "text"},
                         {"name": "languagenplurals-%s" % languagecode, "value": languagenplurals, "type": "text"},
                         {"name": "languagepluralequation-%s" % languagecode, "value": languagepluralequation, "type": "text"},
                         {"name": "languageremove-%s" % languagecode, "value": languageremove, "type": "checkbox", "label": removelabel}]
      languages.append({"code": languagecode, "options": languageoptions})
    return languages

class ProjectsAdminPage(pagelayout.PootlePage):
  """page for administering pootle..."""
  def __init__(self, potree, session, instance):
    self.potree = potree
    self.session = session
    self.instance = instance
    self.localize = session.localize
    templatename = "adminprojects"
    projectfiletypes = ["po","xlf"]
    self.allchecks = [{"value": check, "description": check} for check in checks.projectcheckers.keys()]
    self.allchecks.insert(0, {"value": "", "description": self.localize("Standard")})
    self.alltypes = [{"value": check, "description": check} for check in projectfiletypes]
    sessionvars = {"status": self.session.status, "isopen": self.session.isopen, "issiteadmin": self.session.issiteadmin()}
    instancetitle = getattr(self.instance, "title", session.localize("Pootle Demo"))
    text = self.gettext(session)
    templatevars = {"projects": self.getprojectsoptions(), "options": self.getoptions(), "session": sessionvars, "instancetitle": instancetitle, "text": text}
    pagelayout.PootlePage.__init__(self, templatename, templatevars, session)

  def gettext(self, session):
    """Localize the text"""
    text = {}
    text["home"] = session.localize("Home")
    text["admin"] = session.localize("Main admin page")
    text["projects"] = session.localize("Projects")
    text["savechanges"] = session.localize("Save changes")
    return text

  def getoptions(self):
    options = [{"name": "code", "title": self.localize("Project Code"), "size": 6, "newvalue": ""},
               {"name": "name", "title": self.localize("Full Name"), 
                                "newvalue": self.localize("(add project here)")},
               {"name": "description", "title": self.localize("Project Description"), "newvalue": self.localize("(project description)")},
               {"name": "checkerstyle", "title": self.localize("Checker Style"), "selectoptions": self.allchecks, "newvalue": ""},
               {"name": "filetype", "title": self.localize("File Type"), "selectoptions": self.alltypes, "newvalue": ""},
               {"name": "createmofiles", "title": self.localize("Create MO Files"), "type": "checkbox", "newvalue": ""},
               {"name": "remove", "title": self.localize("Remove Project")}]
    for option in options:
      if "newvalue" in option:
        option["newname"] = "newproject" + option["name"]
      if "type" not in option and "selectoptions" not in option:
        option["type"] = "text"
    return options

  def getprojectsoptions(self):
    projects = []
    for projectcode in self.potree.getprojectcodes():
      projectadminlink = "../projects/%s/admin.html" % projectcode
      projectname = self.potree.getprojectname(projectcode)
      projectdescription = self.potree.getprojectdescription(projectcode)
      projectname = self.potree.getprojectname(projectcode)
      projectcheckerstyle = self.potree.getprojectcheckerstyle(projectcode)
      projectfiletype = self.potree.getprojectlocalfiletype(projectcode)
      if self.potree.getprojectcreatemofiles(projectcode):
        projectcreatemofiles = "checked"
      else:
        projectcreatemofiles = ""
      projectremove = None
      # l10n: The parameter is a languagecode, projectcode or username
      removelabel = self.localize("Remove %s", projectcode)
      projectoptions = [{"name": "projectname-%s" % projectcode, "value": projectname, "type": "text"},
                        {"name": "projectdescription-%s" % projectcode, "value": projectdescription, "type": "text"},
                        {"name": "projectcheckerstyle-%s" % projectcode, "value": projectcheckerstyle, "selectoptions": self.allchecks},
                        {"name": "projectfiletype-%s" % projectcode, "value": projectfiletype, "selectoptions": self.alltypes},
                        {"name": "projectcreatemofiles-%s" % projectcode, "value": projectcreatemofiles, "type": "checkbox", projectcreatemofiles: projectcreatemofiles},
                        {"name": "projectremove-%s" % projectcode, "value": projectremove, "type": "checkbox", "label": removelabel}]
      projects.append({"code": projectcode, "adminlink": projectadminlink, "options": projectoptions})
    return projects

class UsersAdminPage(pagelayout.PootlePage):
  """page for administering pootle..."""
  def __init__(self, server, users, session, instance):
    self.server = server
    self.users = users
    self.session = session
    self.instance = instance
    self.localize = session.localize
    templatename = "adminusers"
    sessionvars = {"status": self.session.status, "isopen": self.session.isopen, "issiteadmin": self.session.issiteadmin()}
    instancetitle = getattr(self.instance, "title", session.localize("Pootle Demo"))
    text = self.gettext(session)
    templatevars = {"users": self.getusersoptions(), "options": self.getoptions(), "session": sessionvars, "instancetitle": instancetitle, "text": text}
    pagelayout.PootlePage.__init__(self, templatename, templatevars, session)

  def gettext(self, session):
    """Localize the text"""
    text = {}
    text["home"] = session.localize("Home")
    text["admin"] = session.localize("Main admin page")
    text["users"] = session.localize("Users")
    text["savechanges"] = session.localize("Save changes")
    return text
    
  def getoptions(self):
    options = [{"name": "name", "title": self.localize("Login"), "newvalue": "", "size": 6},
               {"name": "fullname", "title": self.localize("Full Name"), 
                                    "newvalue": self.localize("(add full name here)")},
               {"name": "email", "title": self.localize("Email Address"), "newvalue": self.localize("(add email here)")},
               {"name": "password", "title": self.localize("Password"), "newvalue": self.localize("(add password here)")},
               {"name": "activated", "title": self.localize("Activated"), "type": "checkbox", "checked": "true", "newvalue": "", "label": self.localize("Activate New User")},
               {"name": "remove", "title": self.localize("Remove User"), "type": "checkbox"}]
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
    for usercode, usernode in self.users.iteritems(sorted=True):
      fullname = getattr(usernode, "name", "")
      email = getattr(usernode, "email", "")
      activated = getattr(usernode, "activated", 0) == 1
      if activated:
        activatedattr = "checked"
      else:
        activatedattr = ""
      userremove = None
      # l10n: The parameter is a languagecode, projectcode or username
      removelabel = self.localize("Remove %s", usercode)
      useroptions = [{"name": "username-%s" % usercode, "value": fullname, "type": "text"},
                     {"name": "useremail-%s" % usercode, "value": email, "type": "text"},
                     {"name": "userpassword-%s" % usercode, "value": None, "type": "text"},
                     {"name": "useractivated-%s" % usercode, "type": "checkbox", activatedattr: activatedattr},
                     {"name": "userremove-%s" % usercode, "value": None, "type": "checkbox", "label": removelabel}]
      users.append({"code": usercode, "options": useroptions})
    return users

class ProjectAdminPage(pagelayout.PootlePage):
  """list of languages belonging to a project"""
  def __init__(self, potree, projectcode, session, argdict):
    self.potree = potree
    self.projectcode = projectcode
    self.session = session
    self.localize = session.localize
    self.tr_lang = session.tr_lang
    projectname = self.potree.getprojectname(self.projectcode)
    if self.session.issiteadmin():
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
          translationproject.converttemplates(self.session)
    main_link = self.localize("Back to main page")
    existing_title = self.localize("Existing languages")
    existing_languages = self.getexistinglanguages()
    new_languages = self.getnewlanguages()
    # l10n: This refers to updating the translation files from the templates like with .pot files
    update_button = self.localize("Update Languages")
    pagetitle = self.localize("Pootle Admin: %s", projectname)
    norights_text = self.localize("You do not have the rights to administer this project.")
    iso_code = self.localize("ISO Code")
    full_name = self.localize("Full Name")
    # l10n: This refers to updating the translation files from the templates like with .pot files
    update_link = self.localize("Update from templates")
    templatename = "projectadmin"
    sessionvars = {"status": self.session.status, "isopen": self.session.isopen, "issiteadmin": self.session.issiteadmin()}
    instancetitle = getattr(self.session.instance, "title", session.localize("Pootle Demo"))
    templatevars = {"pagetitle": pagetitle, "norights_text": norights_text,
        "project": {"code": projectcode, "name": projectname},
        "iso_code": iso_code, "full_name": full_name,
        "existing_title": existing_title, "existing_languages": existing_languages,
        "new_languages": new_languages,
        "update_button": update_button, "add_button": self.localize("Add Language"),
        "main_link": main_link, "update_link": update_link,
        "session": sessionvars, "instancetitle": instancetitle}
    pagelayout.PootlePage.__init__(self, templatename, templatevars, session, bannerheight=80)

  def getexistinglanguages(self):
    """gets the info on existing languages"""
    languages = self.potree.getlanguages(self.projectcode)
    languageitems = [{"code": languagecode, "name": self.tr_lang(languagename)} for languagecode, languagename in languages]
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
    newoptions = [{"code": code, "name": self.tr_lang(languagename)} for (languagename, code) in newoptions]
    # rewritten for compatibility with Python 2.3
    # newoptions.sort(cmp=locale.strcoll, key=lambda dict: dict["name"])
    newoptions.sort(lambda x,y: locale.strcoll(x["name"], y["name"]))
    return newoptions

class TranslationProjectAdminPage(pagelayout.PootlePage):
  """admin page for a translation project (project+language)"""
  def __init__(self, potree, project, session, argdict):
    self.potree = potree
    self.project = project
    self.session = session
    self.localize = session.localize
    self.rightnames = self.project.getrightnames(session)
    # l10n: This is the page title. The first parameter is the language name, the second parameter is the project name
    pagetitle = self.localize("Pootle Admin: %s %s", self.project.languagename, self.project.projectname)
    main_link = self.localize("Project home page")
    if "admin" in self.project.getrights(self.session):
      if "doupdaterights" in argdict:
        for key, value in argdict.iteritems():
          if isinstance(key, str):
            key = key.decode("utf-8")
          if key.startswith("rights-"):
            username = key.replace("rights-", "", 1)
            self.project.setrights(username, value)
          if key.startswith("rightsremove-"):
            username = key.replace("rightsremove-", "", 1)
            self.project.delrights(self.session, username)
        username = argdict.get("rightsnew-username", None)
        if username:
          username = username.strip()
          if self.session.loginchecker.userexists(username):
            self.project.setrights(username, argdict.get("rightsnew", ""))
          else:
            raise IndexError(self.localize("Cannot set rights for username %s - user does not exist", username))
    norights_text = self.localize("You do not have the rights to administer this project.")
    templatename = "projectlangadmin"
    sessionvars = {"status": self.session.status, "isopen": self.session.isopen, "issiteadmin": self.session.issiteadmin()}
    instancetitle = getattr(self.session.instance, "title", session.localize("Pootle Demo"))
    templatevars = {"pagetitle": pagetitle, "norights_text": norights_text,
        "project": {"code": self.project.projectcode, "name": self.project.projectname},
        "language": {"code": self.project.languagecode, "name": self.project.languagename},
        "main_link": main_link,
        "session": sessionvars, "instancetitle": instancetitle}
    templatevars.update(self.getoptions())
    pagelayout.PootlePage.__init__(self, templatename, templatevars, session, bannerheight=80)

  def getoptions(self):
    """returns a box that describes the options"""
    self.project.readprefs()
    if self.project.filestyle == "gnu":
      filestyle_text = self.localize("This is a GNU-style project (one directory, files named per language).")
    else:
      filestyle_text = self.localize("This is a standard style project (one directory per language).")
    permissions_title = self.localize("User Permissions")
    username_title = self.localize("Username")
    adduser_text = self.localize("(select to add user)")
    rights_title = self.localize("Rights")
    remove_title = self.localize("Remove")
    nobodyrights = self.project.getrights(username=None)
    nobody_dict = self.getuserdict("nobody", delete=False)
    defaultrights = self.project.getrights(username="default")
    default_dict = self.getuserdict("default", delete=False)
    users_with_rights = ["nobody", "default"]
    rights = {"nobody": nobodyrights, "default": defaultrights}
    for username in self.project.getuserswithrights():
      if username in ("nobody", "default"): continue
      users_with_rights.append(username)
      rights[username] = self.project.getrights(username=username)
    users = self.project.getuserswithinterest(self.session)
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
    updaterights_text = self.localize("Update Rights")
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
    remove_text = self.localize("Remove %s", username)
    description = getattr(usernode, "description", None) or username
    userdict = {"username": username, "delete": delete or None, "remove_text": remove_text, "description": description}
    return userdict

