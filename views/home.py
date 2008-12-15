import locale

from Pootle import pagelayout, pan_app
from Pootle.pootle_app.models import get_profile
from Pootle.views.util import render_to_kid, KidRequestContext

class UserOptions(pagelayout.PootlePage):
  """page for user to change their options"""
  def __init__(self, request, message=None):
    self.potree = pan_app.get_po_tree()
    self.request = request
    self.localize = request.localize
    self.tr_lang = request.tr_lang
    #message = forcemessage(message)
    pagetitle = self.localize("Options for: %s", request.user.username)
    templatename = "options"
    instancetitle = getattr(pan_app.prefs, "title", request.localize("Pootle Demo"))
    enablealtsrc = getattr(pan_app.prefs, "enablealtsrc", False)
    templatevars = {"pagetitle": pagetitle, "introtext": message,
        "detailstitle": self.localize("Personal Details"),
        "fullname_title": self.localize("Name"),
        "fullname": self.request.user.first_name,
        "email_title": self.localize("Email"),
        "email": self.request.user.email,
        "password_title": self.localize("Password"),
        "passwordconfirm_title": self.localize("Confirm password"),
        "interface_title": self.localize("Translation Interface Configuration"),
        "uilanguage_heading": self.localize("User Interface language"),
        "projects_title": self.localize("My Projects"),
        "projects": self.getprojectoptions(),
        "languages_title": self.localize("My Languages"),
        "languages": self.getlanguageoptions(),
        "home_link": self.localize("Home page"),
        "submit_button": self.localize("Save changes"),
        "instancetitle": instancetitle,
        "enablealtsrc": enablealtsrc,
        "logintype": get_profile(self.request.user).login_type
        }
    if enablealtsrc == 'True':
      templatevars["altsrclanguage_title"] = self.localize("Alternative Source Language")
      templatevars["altsrclanguages"] = self.getaltsrcoptions()
    otheroptions = self.getotheroptions()
    templatevars.update(otheroptions)
    pagelayout.PootlePage.__init__(self, templatename, templatevars, request)

  def getprojectoptions(self):
    """gets the options box to change the user's projects"""
    projectoptions = []
    userprojects = get_profile(self.request.user).projects.all()
    for projectcode in self.potree.getprojectcodes():
      projectname = self.potree.getprojectname(projectcode)
      projectoptions.append({"code": projectcode, "name": projectname, "selected": projectcode in userprojects or None})
    return projectoptions

  def getlanguageoptions(self):
    """returns options for languages"""
    userlanguages = get_profile(self.request.user).languages.all()
    languageoptions = self.potree.getlanguages()
    languages = []
    for language, name in languageoptions:
      languages.append({"code": language, "name": self.tr_lang(name), "selected": language in userlanguages or None})
    # rewritten for compatibility with Python 2.3
    # languages.sort(cmp=locale.strcoll, key=lambda dict: dict["name"])
    languages.sort(lambda x,y: locale.strcoll(x["name"], y["name"]))
    return languages

  def getaltsrcoptions(self):
    """returns options for alternative source languages"""
    useraltsrc = self.request.getaltsrclanguage()
    languageoptions = self.potree.getlanguages()
    altsrclanguages = []
    for language, name in languageoptions:
      altsrclanguages.append({"code": language, "name": self.tr_lang(name), "selected": language in useraltsrc and 'selected' or None})
    # rewritten for compatibility with Python 2.3
    # altsrclanguages.sort(cmp=locale.strcoll, key=lambda dict: dict["name"])
    altsrclanguages.sort(lambda x,y: locale.strcoll(x["name"], y["name"]))
    # l10n: 'None' is displayed as the first item in the alternative source languages list and disables the feature.
    altsrclanguages.insert(0, {"code": '', "name": self.localize("None"), "selected": '' in useraltsrc and 'selected' or None})
    return altsrclanguages

  def getotheroptions(self):
    profile = get_profile(self.request.user)
    if profile.ui_lang:
        uilanguage = profile.ui_lang.fullname
    else:
        uilanguage = None

    languageoptions = [{"code": '', "name": ''}]
    for code, name in self.potree.getlanguages():
      if code == "templates":
        continue
      languageoptions.append({"code": code, "name": self.tr_lang(name), "selected": uilanguage == code or None})
    # rewritten for compatibility with Python 2.3
    # languageoptions.sort(cmp=locale.strcoll, key=lambda dict: dict["name"])
    languageoptions.sort(lambda x,y: locale.strcoll(x["name"], y["name"]))
    options = {"input_height": self.localize("Input Height (in lines)"), 
          "view_rows": self.localize("Number of rows in view mode"), 
          "translate_rows": self.localize("Number of rows in translate mode")}
    optionlist = []
    for option, description in options.items():
      optionvalue = getattr(profile, option, "")
      optionlist.append({"code": option, "description": description, "value": optionvalue})
    return {"uilanguage": uilanguage, "uilanguage_options": languageoptions, "other_options": optionlist}

def options(request):
    if request.method == 'GET':
        user_options = UserOptions(request)
        return render_to_kid("options.html", KidRequestContext(request, user_options.templatevars))
    elif request.method == 'POST':
        raise NotImplementedError()
