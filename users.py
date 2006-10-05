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

from jToolkit.web import server
from jToolkit.web import session
from jToolkit import mailer
from jToolkit import prefs
from Pootle import pagelayout

class RegistrationError(ValueError):
  def __init__(self, message):
    message = message.encode('utf-8')
    ValueError.__init__(self, message)

# This mimimum passwordlength is mandated by the interface when registering or 
# changing password
minpasswordlen = 6

def validatepassword(session, password, passwordconfirm):
  if not password or len(password) < minpasswordlen:
    raise RegistrationError(session.localize("You must supply a valid password of at least %d characters.", minpasswordlen))
  if not password == passwordconfirm:
    raise RegistrationError(session.localize("The password is not the same as the confirmation."))

def forcemessage(message):
  """Tries to extract some kind of message and converts to unicode"""
  if message and not isinstance(message, unicode):
    return str(message).decode('utf-8')
  else:
    return message

class LoginPage(pagelayout.PootlePage):
  """wraps the normal login page in a PootlePage layout"""
  def __init__(self, session, languagenames=None, message=None):
    self.localize = session.localize
    self.languagenames = languagenames
    pagetitle = self.localize("Login to Pootle")
    templatename = "login"
    message = forcemessage(message)
    instancetitle = getattr(session.instance, "title", session.localize("Pootle Demo"))
    sessionvars = {"status": session.status, "isopen": session.isopen, "issiteadmin": session.issiteadmin()}
    templatevars = {"pagetitle": pagetitle, "introtext": message,
        "username_title": self.localize("Username:"),
        "username": getattr(session, 'username', ''),
        "password_title": self.localize("Password:"),
        "language_title": self.localize('Language:'),
        "languages": self.getlanguageoptions(session),
        "login_text": self.localize('Login'),
        "session": sessionvars, "instancetitle": instancetitle}
    pagelayout.PootlePage.__init__(self, templatename, templatevars, session)

  def getlanguageoptions(self, session):
    """returns the language selector..."""
    # TODO: work out how we handle localization of language names...
    languageoptions = [('', session.localize("Default"))]
    if isinstance(self.languagenames, dict):
      languageoptions += self.languagenames.items()
    else:
      languageoptions += self.languagenames
    return [{"code": key, "name": value, "selected": key==session.language or None} for key, value in languageoptions]

class RegisterPage(pagelayout.PootlePage):
  """page for new registrations"""
  def __init__(self, session, argdict, message=None):
    self.localize = session.localize
    if not message:
      introtext = self.localize("Please enter your registration details")
    else:
      introtext = forcemessage(message)
    pagetitle = self.localize("Pootle Registration")
    self.argdict = argdict
    templatename = "register"
    instancetitle = getattr(session.instance, "title", session.localize("Pootle Demo"))
    sessionvars = {"status": session.status, "isopen": session.isopen, "issiteadmin": session.issiteadmin()}
    templatevars = {"pagetitle": pagetitle, "introtext": introtext,
        "username_title": self.localize("Username"),
        "username_tooltip": self.localize("Your requested username"),
        "username": self.argdict.get("username", ""),
        "email_title": self.localize("Email Address"),
        "email_tooltip": self.localize("You must supply a valid email address"),
        "email": self.argdict.get("email", ""),
        "fullname_title": self.localize("Full Name"),
        "fullname_tooltip": self.localize("Your full name"),
        "fullname": self.argdict.get("name", ""),
        "password_title": self.localize("Password"),
        "password_tooltip": self.localize("Your desired password"),
        "password": self.argdict.get("password", ""),
        "passwordconfirm_title": self.localize("Confirm password"),
        "passwordconfirm_tooltip": self.localize("Type your password again to ensure it is entered correctly"),
        "passwordconfirm": self.argdict.get("passwordconfirm", ""),
        "register_text": self.localize('Register Account'),
        "session": sessionvars, "instancetitle": instancetitle}
    pagelayout.PootlePage.__init__(self, templatename, templatevars, session)

class ActivatePage(pagelayout.PootlePage):
  """page for new registrations"""
  def __init__(self, session, argdict, title=None, message=None):
    self.localize = session.localize
    if not message:
      introtext = self.localize("Please enter your activation details")
    else:
      introtext = forcemessage(message)
    self.argdict = argdict
    if title is None:
      pagetitle = self.localize("Pootle Account Activation")
    else:
      pagetitle = title
    templatename = "activate"
    instancetitle = getattr(session.instance, "title", session.localize("Pootle Demo"))
    sessionvars = {"status": session.status, "isopen": session.isopen, "issiteadmin": session.issiteadmin()}
    templatevars = {"pagetitle": pagetitle, "introtext": introtext,
        "username_title": self.localize("Username"),
        "username_tooltip": self.localize("Your requested username"),
        "username": self.argdict.get("username", ""),
        "code_title": self.localize("Activation Code"),
        "code_tooltip": self.localize("The activation code you received"),
        "code": self.argdict.get("activationcode", ""),
        "activate_text": self.localize('Activate Account'),
        "session": sessionvars, "instancetitle": instancetitle}
    pagelayout.PootlePage.__init__(self, templatename, templatevars, session)

class UserOptions(pagelayout.PootlePage):
  """page for user to change their options"""
  def __init__(self, potree, session, message=None):
    self.potree = potree
    self.session = session
    self.localize = session.localize
    message = forcemessage(message)
    pagetitle = self.localize("Options for: %s", session.username)
    templatename = "options"
    instancetitle = getattr(session.instance, "title", session.localize("Pootle Demo"))
    sessionvars = {"status": session.status, "isopen": session.isopen, "issiteadmin": session.issiteadmin()}
    templatevars = {"pagetitle": pagetitle, "introtext": message,
        "detailstitle": self.localize("Personal Details"),
        "option_heading": self.localize("Option"),
        "value_heading": self.localize("Current value"),
        "fullname_title": self.localize("Name"),
        "fullname": self.session.prefs.name,
        "email_title": self.localize("Email"),
        "email": self.session.prefs.email,
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
        "session": sessionvars, "instancetitle": instancetitle}
    otheroptions = self.getotheroptions()
    templatevars.update(otheroptions)
    pagelayout.PootlePage.__init__(self, templatename, templatevars, session)

  def getprojectoptions(self):
    """gets the options box to change the user's projects"""
    projectoptions = []
    userprojects = self.session.getprojects()
    for projectcode in self.potree.getprojectcodes():
      projectname = self.potree.getprojectname(projectcode)
      projectoptions.append({"code": projectcode, "name": projectname, "selected": projectcode in userprojects or None})
    return projectoptions

  def getlanguageoptions(self):
    """returns options for languages"""
    userlanguages = self.session.getlanguages()
    languageoptions = self.potree.getlanguages()
    languages = []
    for language, name in languageoptions:
      languages.append({"code": language, "name": name, "selected": language in userlanguages or None})
    return languages

  def getotheroptions(self):
    uilanguage = getattr(self.session.prefs, "uilanguage", "")
    if not uilanguage:
      userlanguages = self.session.getlanguages()
      if userlanguages:
        uilanguage = userlanguages[0]
    languageoptions = [{"code": '', "name": ''}]
    for code, name in self.potree.getlanguages():
      languageoptions.append({"code": code, "name": name, "selected": uilanguage == code or None})
    options = {"inputheight": self.localize("Input Height (in lines)"), "inputwidth": self.localize("Input Width (in characters)"),
          "viewrows": self.localize("Number of rows in view mode"), 
          "translaterows": self.localize("Number of rows in translate mode")}
    optionlist = []
    for option, description in options.items():
      optionvalue = getattr(self.session.prefs, option, "")
      optionlist.append({"code": option, "description": description, "value": optionvalue})
    return {"uilanguage": uilanguage, "uilanguage_options": languageoptions, "other_options": optionlist}

class OptionalLoginAppServer(server.LoginAppServer):
  """a server that enables login but doesn't require it except for specified pages"""
  def handle(self, req, pathwords, argdict):
    """handles the request and returns a page object in response"""
    try:
      argdict = self.processargs(argdict)
      session = self.getsession(req, argdict)
      if session.isopen:
        session.pagecount += 1
        session.remote_ip = self.getremoteip(req)
      else:
        self.initlanguage(req, session)
      page = self.getpage(pathwords, session, argdict)
    except Exception, e:
      exceptionstr = self.errorhandler.exception_str()
      errormessage = str(e).decode("utf-8")
      traceback = self.errorhandler.traceback_str().decode('utf-8')
      browsertraceback = ""
      options = getattr(self, "options", None)
      # with unit tests we might not have self.options, therefore this test
      if options:
        if self.options.browsererrors == 'traceback':
          browsertraceback = traceback
        if self.options.logerrors == 'traceback':
          self.errorhandler.logerror(traceback)
        elif self.options.logerrors == 'exception':
          self.errorhandler.logerror(exceptionstr)
        elif self.options.logerrors == 'message':
          self.errorhandler.logerror(errormessage)
      else:
        self.errorhandler.logerror(traceback)
      
      refreshurl = req.headers_in.getheader('Referer') or "/"
      templatename = "error"
      templatevars = {
          "pagetitle": session.localize("Error"),
          "refresh": 30,
          "refreshurl": refreshurl,
          "message": errormessage,
          "traceback": browsertraceback,
          "back": session.localize("Back"),
          }
      pagelayout.completetemplatevars(templatevars, session)
      page = server.Redirect(refreshurl, withtemplate=(templatename, templatevars))
    return page

  def initlanguage(self, req, session):
    """Initialises the session language from the request"""
    # This version doesn't know which languages we have, so we have to override
    # in PootleServer.
    session.setlanguage("en")
      
  def hasuser(self, users, username):
    """returns whether the user exists in users"""
    return users.__hasattr__(username)

  def getusernode(self, users, username):
    """gets the node for the given user"""
    if not self.hasuser(users, username):
      usernode = prefs.PrefNode(users, username)
      users.__setattr__(username, usernode)
    else:
      usernode = users.__getattr__(username)
    return usernode

  def adduser(self, users, username, fullname, email, password):
    """adds the user with the given details"""
    usernode = self.getusernode(users, username)
    usernode.name = fullname
    usernode.email = email
    usernode.passwdhash = session.md5hexdigest(password)

  def makeactivationcode(self, users, username):
    """makes a new activation code for the user and returns it"""
    usernode = self.getusernode(users, username)
    usernode.activated = 0
    activationcode = self.generateactivationcode()
    usernode.activationcode = activationcode
    return activationcode

  def activate(self, users, username):
    """sets the user as activated"""
    self.getusernode(users, username).activated = 1

  def changeusers(self, session, argdict):
    """handles multiple changes from the site admin"""
    if not session.issiteadmin():
      raise ValueError(session.localize("You need to be siteadmin to change users"))
    users = session.loginchecker.users
    for key, value in argdict.iteritems():
      if key.startswith("userremove-"):
        usercode = key.replace("userremove-", "", 1)
        if self.hasuser(users, usercode):
          raise NotImplementedError("Can't remove users")
      elif key.startswith("username-"):
        username = key.replace("username-", "", 1)
        if self.hasuser(users, username):
          usernode = self.getusernode(users, username)
          fullname = getattr(usernode, "name", None)
          if fullname != value:
            usernode.name = value
      elif key.startswith("useremail-"):
        username = key.replace("useremail-", "", 1)
        if self.hasuser(users, username):
          usernode = self.getusernode(users, username)
          useremail = getattr(usernode, "email", None)
          if useremail != value:
            usernode.email = value
      elif key.startswith("userpassword-"):
        username = key.replace("userpassword-", "", 1)
        if self.hasuser(users, username):
          usernode = self.getusernode(users, username)
          if value and value.strip():
            usernode.passwdhash = session.md5hexdigest(value.strip())
      elif key.startswith("useractivated-"):
        username = key.replace("useractivated-", "", 1)
        self.activate(users, username)
      elif key == "newusername":
        username = value.lower()
        if not username:
          continue
        if not (username[:1].isalpha() and username.replace("_","").isalnum()):
          raise ValueError("Login must be alphanumeric and start with an alphabetic character (got %r)" % username)
        if username in ["nobody", "default"]:
          raise ValueError('"%s" is a reserved username.' % username)
        if self.hasuser(users, username):
          raise ValueError("Already have user with the login: %s" % username)
        userpassword = argdict.get("newuserpassword", None)
        if userpassword is None or userpassword == session.localize("(add password here)"):
          raise ValueError("You must specify a password")
        userfullname = argdict.get("newuserfullname", None)
        if userfullname == session.localize("(add full name here)"):
          raise ValueError("Please set the users full name or leave it blank")
        useremail = argdict.get("newuseremail", None)
        if useremail == session.localize("(add email here)"):
          raise ValueError("Please set the users email address or leave it blank")
        useractivate = "newuseractivate" in argdict
        self.adduser(users, username, userfullname, useremail, userpassword)
        if useractivate:
          self.activate(users, username)
        else:
          activationcode = self.makeactivationcode(users, username)
          print "user activation code for %s is %s" % (username, activationcode)
    session.saveprefs()

  def handleregistration(self, session, argdict):
    """handles the actual registration"""
    #TODO: Fix layout, punctuation, spacing and correlation of messages
    supportaddress = getattr(self.instance.registration, 'supportaddress', "")
    username = argdict.get("username", "")
    if not username or not username.isalnum() or not username[0].isalpha():
      raise RegistrationError(session.localize("Username must be alphanumeric, and must start with an alphabetic character."))
    fullname = argdict.get("name", "")
    email = argdict.get("email", "")
    password = argdict.get("password", "")
    passwordconfirm = argdict.get("passwordconfirm", "")
    if " " in email or not (email and "@" in email and "." in email):
      raise RegistrationError(session.localize("You must supply a valid email address"))
    userexists = session.loginchecker.userexists(username)
    users = session.loginchecker.users
    if userexists:
      usernode = self.getusernode(users, username)
      # use the email address on file
      email = getattr(usernode, "email", email)
      password = ""
      # TODO: we can't figure out the password as we only store the md5sum. have a password reset mechanism
      message = session.localize("You (or someone else) attempted to register an account with your username.\n")
      message += session.localize("We don't store your actual password but only a hash of it.\n")
      if supportaddress:
        message += session.localize("If you have a problem with registration, please contact %s.\n", supportaddress)
      else:
        message += session.localize("If you have a problem with registration, please contact the site administrator.\n")
      displaymessage = session.localize("That username already exists. An email will be sent to the registered email address.\n")
      redirecturl = "login.html?username=%s" % username
      displaymessage += session.localize("Proceeding to <a href='%s'>login</a>\n", redirecturl)
    else:
      validatepassword(session, password, passwordconfirm)
      self.adduser(users, username, fullname, email, password)
      activationcode = self.makeactivationcode(users, username)
      activationlink = ""
      message = session.localize("A Pootle account has been created for you using this email address.\n")
      if session.instance.baseurl.startswith("http://"):
        message += session.localize("To activate your account, follow this link:\n")
        activationlink = session.instance.baseurl
        if not activationlink.endswith("/"):
          activationlink += "/"
        activationlink += "activate.html?username=%s&activationcode=%s" % (username, activationcode)
        message += "  %s  \n" % activationlink
      message += session.localize("Your activation code is:\n%s\n", activationcode)
      if activationlink:
        message += session.localize("If you are unable to follow the link, please enter the above code at the activation page.\n")
      message += session.localize("This message is sent to verify that the email address is in fact correct. If you did not want to register an account, you may simply ignore the message.\n")
      redirecturl = "activate.html?username=%s" % username
      displaymessage = session.localize("Account created. You will be emailed login details and an activation code. Please enter your activation code on the <a href='%s'>activation page</a>.", redirecturl)
      if activationlink:
        displaymessage += " " + session.localize("(Or simply click on the activation link in the email)")
    session.saveprefs()
    message += session.localize("Your user name is: %s\n", username)
    if password.strip():
      message += session.localize("Your password is: %s\n", password)
    message += session.localize("Your registered email address is: %s\n", email)
    smtpserver = self.instance.registration.smtpserver
    fromaddress = self.instance.registration.fromaddress
    messagedict = {"from": fromaddress, "to": [email], "subject": session.localize("Pootle Registration"), "body": message}
    if supportaddress:
      messagedict["reply-to"] = supportaddress
    fullmessage = mailer.makemessage(messagedict)
    if isinstance(fullmessage, unicode):
      fullmessage = fullmessage.encode("utf-8")
    errmsg = mailer.dosendmessage(fromemail=self.instance.registration.fromaddress, recipientemails=[email], message=fullmessage, smtpserver=smtpserver)
    if errmsg:
      raise RegistrationError("Error sending mail: %s" % errmsg)
    return displaymessage, redirecturl

  def registerpage(self, session, argdict):
    """handle registration or return the Register page"""
    if "username" in argdict:
      try:
        displaymessage, redirecturl = self.handleregistration(session, argdict)
      except RegistrationError, message:
        return RegisterPage(session, argdict, message)
      redirectpage = pagelayout.PootlePage("Redirecting...", {}, session)
      redirectpage.templatename = "redirect"
      redirectpage.templatevars = {
          "pagetitle": session.localize("Redirecting to Registration Page..."),
          "refresh": 10,
          "refreshurl": redirecturl,
          "message": displaymessage,
          }
      redirectpage.completevars()
      return redirectpage
    else:
      return RegisterPage(session, argdict)

  def activatepage(self, session, argdict):
    """handle activation or return the Register page"""
    if "username" in argdict and "activationcode" in argdict:
      username = argdict["username"]
      activationcode = argdict["activationcode"]
      if self.hasuser(session.loginchecker.users, username):
        usernode = self.getusernode(session.loginchecker.users, username)
        correctcode = getattr(usernode, "activationcode", "")
        if correctcode and correctcode.strip().lower() == activationcode.strip().lower():
          setattr(usernode, "activated", 1)
          session.saveprefs()
          redirectpage = pagelayout.PootlePage("Redirecting to login...", {}, session)
          redirectpage.templatename = "redirect"
          redirectpage.templatevars = {
              "pagetitle": session.localize("Redirecting to login Page..."),
              "refresh": 10,
              "refreshurl": "login.html?username=%s" % username,
              "message": session.localize("Your account has been activated! Redirecting to login..."),
              }
          redirectpage.completevars()
          return redirectpage
      failedmessage = session.localize("The activation information was not valid.")
      return ActivatePage(session, argdict, title=session.localize("Activation Failed"), message=failedmessage)
    else:
      return ActivatePage(session, argdict)

class PootleSession(session.LoginSession):
  """a session object that knows about Pootle"""
  def __init__(self, sessioncache, server, sessionstring = None, loginchecker = None):
    """sets up the session and remembers the users prefs"""
    super(PootleSession, self).__init__(sessioncache, server, sessionstring, loginchecker)
    self.getprefs()

  def getprefs(self):
    """gets the users prefs into self.prefs"""
    if self.isopen:
      self.prefs = self.loginchecker.users.__getattr__(self.username)
      uilanguage = getattr(self.prefs, "uilanguage", None)
      if uilanguage and not self.language:
        self.setlanguage(uilanguage)
    else:
      self.prefs = None

  def saveprefs(self):
    """saves changed preferences back to disk"""
    # TODO: this is a hack, fix it up nicely :-)
    prefsfile = self.loginchecker.users.__root__.__dict__["_setvalue"].im_self
    prefsfile.savefile()

  def open(self):
    """opens the session, along with the users prefs"""
    super(PootleSession, self).open()
    self.getprefs()
    return self.isopen

  def close(self, req):
    """opens the session, along with the users prefs"""
    super(PootleSession, self).close(req)
    self.getprefs()

  def setlanguage(self, language):
    """sets the language for the session"""
    self.language_set = language or ""
    if language:
      self.language = language
    elif not getattr(self, "language", None):
      if self.isopen:
        self.language = getattr(self.prefs, "uilanguage", "") or self.server.defaultlanguage
      else:
        self.language = self.server.defaultlanguage
    if self.isopen:
      if not getattr(self.prefs, "uilanguage", "") and self.language_set:
        self.setinterfaceoptions({"option-uilanguage": self.language_set})
    self.translation = self.server.gettranslation(self.language)

  def validate(self):
    """checks if this session is valid (which means the user must be activated)"""
    if not super(PootleSession, self).validate():
      return False
    if self.loginchecker.users.__hasattr__(self.username):
      usernode = self.loginchecker.users.__getattr__(self.username)
      if getattr(usernode, "activated", 0):
        return self.isvalid
    self.isvalid = False
    self.status = "username has not yet been activated"
    return self.isvalid

  def setoptions(self, argdict):
    """sets the user options"""
    userprojects = argdict.get("projects", [])
    if isinstance(userprojects, (str, unicode)):
      userprojects = [userprojects]
    setattr(self.prefs, "projects", ",".join(userprojects))
    userlanguages = argdict.get("languages", [])
    if isinstance(userlanguages, (str, unicode)):
      userlanguages = [userlanguages]
    setattr(self.prefs, "languages", ",".join(userlanguages))
    self.saveprefs()

  def setpersonaloptions(self, argdict):
    """sets the users personal details"""
    name = argdict.get("option-name", "")
    email = argdict.get("option-email", "")
    password = argdict.get("option-password", "")
    passwordconfirm = argdict.get("option-passwordconfirm", "")

    if password or passwordconfirm:
      validatepassword(self, password, passwordconfirm)
    setattr(self.prefs, "name", name)
    setattr(self.prefs, "email", email)
    if password:
      passwdhash = session.md5hexdigest(argdict.get("option-password", ""))
      setattr(self.prefs, "passwdhash", passwdhash)
    self.saveprefs()

  def setinterfaceoptions(self, argdict):
    """sets the users interface details"""
    value = argdict.get("option-uilanguage", "")
    if value:
      self.prefs.uilanguage = value
      self.setlanguage(value)
    def setinterfacevalue(name, errormessage):
      value = argdict.get("option-%s" % name, "")
      if value != "":
        if not value.isdigit():
          raise ValueError(errormessage)
        setattr(self.prefs, name, value)
    setinterfacevalue("inputheight", self.localize("Input height must be numeric"))
    setinterfacevalue("inputwidth", self.localize("Input width must be numeric"))
    setinterfacevalue("viewrows", self.localize("The number of rows displayed in view mode must be numeric"))
    setinterfacevalue("translaterows", self.localize("The number of rows displayed in translate mode must be numeric"))
    self.saveprefs()

  def getprojects(self):
    """gets the user's projects"""
    userprojects = getattr(self.prefs, "projects", "")
    return [projectcode.strip() for projectcode in userprojects.split(',') if projectcode.strip()]

  def getlanguages(self):
    """gets the user's languages"""
    userlanguages = getattr(self.prefs, "languages", "")
    return [languagecode.strip() for languagecode in userlanguages.split(',') if languagecode.strip()]

  def getrights(self):
    """gets the user's rights"""
    return getattr(self.prefs, "rights", None)

  def issiteadmin(self):
    """returns whether the user can administer the site"""
    return getattr(self.getrights(), "siteadmin", False)

