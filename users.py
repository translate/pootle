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

from jToolkit import web
from jToolkit.web import server
from jToolkit.web import session
from jToolkit import mailer
from jToolkit import prefs
from Pootle import pagelayout
from translate.lang import data as langdata
from translate.lang import factory
from email.Header import Header
import locale
import Cookie
import re
import time

from django.contrib.auth.models import User
from Pootle.pootle_app.profile import make_pootle_user, get_profile, save_user
from Pootle import pan_app

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
    self.tr_lang = session.tr_lang
    self.languagenames = languagenames
    pagetitle = self.localize("Login to Pootle")
    templatename = "login"
    message = forcemessage(message)
    instancetitle = getattr(pan_app.prefs, "title", session.localize("Pootle Demo"))
    sessionvars = {"status": session.status, "isopen": session.isopen, "issiteadmin": session.issiteadmin()}
    templatevars = {"pagetitle": pagetitle, "introtext": message,
        "username_title": self.localize("Username:"),
        "username": getattr(session, 'username', ''),
        "password_title": self.localize("Password:"),
        "language_title": self.localize('Language:'),
        "languages": self.getlanguageoptions(session),
        "login_text": self.localize('Login'),
        "register_text": self.localize('Register'),
        "session": sessionvars, "instancetitle": instancetitle}
    pagelayout.PootlePage.__init__(self, templatename, templatevars, session)

  def getlanguageoptions(self, session):
    """returns the language selector..."""
    tr_default = session.localize("Default")
    if tr_default != "Default":
        tr_default = u"%s | \u202dDefault" % tr_default
    languageoptions = [('', tr_default)]
    if isinstance(self.languagenames, dict):
      languageoptions += self.languagenames.items()
    else:
      languageoptions += self.languagenames
    if session.language in ["en", session.server.defaultlanguage]:
        preferredlanguage = ""
    else:
        preferredlanguage = session.language
    finallist = []
    for key, value in languageoptions:
        if key == 'templates':
            continue
        tr_name = session.tr_lang(value)
        if tr_name != value:
            # We have to use the LRO (left-to-right override) to ensure that 
            # brackets in the English part of the name is rendered correctly
            # in an RTL layout like Arabic. We can't use markup because this 
            # is used inside an option tag.
            value = u"%s | \u202d%s" % (tr_name, value)
        selected = key==preferredlanguage or None
        finallist.append({"code": key, "name": value, "selected": selected})
    # rewritten for compatibility with Python 2.3
    # finallist.sort(cmp=locale.strcoll, key=lambda dict: dict["name"])
    finallist.sort(lambda x,y: locale.strcoll(x["name"], y["name"]))
    return finallist

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
    instancetitle = getattr(pan_app.prefs, "title", session.localize("Pootle Demo"))
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
    instancetitle = getattr(pan_app.prefs, "title", session.localize("Pootle Demo"))
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
  def __init__(self, session, message=None):
    self.potree = pan_app.get_po_tree()
    self.session = session
    self.localize = session.localize
    self.tr_lang = session.tr_lang
    message = forcemessage(message)
    pagetitle = self.localize("Options for: %s", session.username)
    templatename = "options"
    instancetitle = getattr(pan_app.prefs, "title", session.localize("Pootle Demo"))
    enablealtsrc = getattr(pan_app.prefs, "enablealtsrc", False)
    sessionvars = {"status": session.status, "isopen": session.isopen, "issiteadmin": session.issiteadmin()}
    templatevars = {"pagetitle": pagetitle, "introtext": message,
        "detailstitle": self.localize("Personal Details"),
        "fullname_title": self.localize("Name"),
        "fullname": self.session.user.first_name,
        "email_title": self.localize("Email"),
        "email": self.session.user.email,
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
        "session": sessionvars,
        "instancetitle": instancetitle,
        "enablealtsrc": enablealtsrc,
        "logintype": get_profile(self.session.user).login_type
        }
    if enablealtsrc == 'True':
      templatevars["altsrclanguage_title"] = self.localize("Alternative Source Language")
      templatevars["altsrclanguages"] = self.getaltsrcoptions()
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
      languages.append({"code": language, "name": self.tr_lang(name), "selected": language in userlanguages or None})
    # rewritten for compatibility with Python 2.3
    # languages.sort(cmp=locale.strcoll, key=lambda dict: dict["name"])
    languages.sort(lambda x,y: locale.strcoll(x["name"], y["name"]))
    return languages

  def getaltsrcoptions(self):
    """returns options for alternative source languages"""
    useraltsrc = self.session.getaltsrclanguage()
    languageoptions = self.potree.getlanguages()
    altsrclanguages = []
    for language, name in languageoptions:
      altsrclanguages.append({"code": language, "name": self.tr_lang(name), "selected": language in useraltsrc and 'selected' or None})
    # rewritten for compatibility with Python 2.3
    # altsrclanguages.sort(cmp=locale.strcoll, key=lambda dict: dict["name"])
    altsrclanguages.sort(lambda x,y: locale.strcoll(x["name"], y["name"]))
    # l10n: 'None' is displayed as the first item in the alternative source languages list and disables the feature.
    altsrclanguages.insert(0, {"code": '', "name": self.session.localize("None"), "selected": '' in useraltsrc and 'selected' or None})
    return altsrclanguages

  def getotheroptions(self):
    profile = get_profile(self.session.user)
    uilanguage = profile.ui_lang.fullname
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

class OptionalLoginAppServer(object):
  """a server that enables login but doesn't require it except for specified pages"""
  def handle(self, req, pathwords, argdict):
    """handles the request and returns a page object in response"""
    session = None
    try:
      argdict = self.processargs(argdict)
      session = self.getsession(req, argdict)
      if pan_app.prefs.baseurl[-1] == '/':
        session.currenturl = pan_app.prefs.baseurl[:-1]+req.path
      else:
        session.currenturl = pan_app.prefs.baseurl+req.path
      session.reqpath = req.path
      if req.path.find("?") >= 0:
        session.getsuffix = req.path[req.path.find("?"):]
      else:
        session.getsuffix = "" 
      if session.isopen:
        session.pagecount += 1
        session.remote_ip = self.getremoteip(req)
        session.localaddr = self.getlocaladdr(req)
      else:
        self.initlanguage(req, session)
      page = self.getpage(pathwords, session, argdict)
    except Exception, e:
      # Because of the exception, 'session' might not be initialised. So let's
      # play extra safe
      if not session:
          raise

      exceptionstr = self.errorhandler.exception_str()
      errormessage = str(e).decode("utf-8")
      traceback = self.errorhandler.traceback_str().decode('utf-8')
      browsertraceback = ""
      options = getattr(self, "options", None)
      # with unit tests we might not have self.options, therefore this test
      if options:
        if options.browsererrors == 'traceback':
          browsertraceback = traceback
        if options.logerrors == 'traceback':
          self.errorhandler.logerror(traceback)
        elif options.logerrors == 'exception':
          self.errorhandler.logerror(exceptionstr)
        elif options.logerrors == 'message':
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
      
  def hasuser(self, username):
    """returns whether the user exists in users"""
    return User.objects.filter(username=username).count() > 0

  def getusernode(self, username):
    """gets the node for the given user"""
    if not self.hasuser(username):
      usernode = make_pootle_user(username)
    else:
      usernode = User.objects.filter(username=username)[0]
    return usernode

  def adduser(self, username, fullname, email, password, logintype="hash"):
    """adds the user with the given details"""
    if logintype == "ldap":
      return self.addldapuser(username)
    usernode = self.getusernode(username)
    usernode.first_name = fullname
    usernode.email = email
    get_profile(usernode).login_type = logintype
    usernode.password = web.session.md5hexdigest(password)
    return usernode

  def addldapuser(self, username):
    email = username
    import mozldap 
    c = mozldap.MozillaLdap(pan_app.prefs.ldap.cn, pan_app.prefs.ldap.dn, pan_app.prefs.ldap.pw)
    fullname = c.getFullName(email)
    usernode = self.getusernode(username)
    usernode.first_name = fullname
    usernode.email = email
    get_profile(usernode).login_type = "ldap" 
    return usernode

  def makeactivationcode(self, usernode):
    """makes a new activation code for the user and returns it"""
    activationcode = self.generateactivationcode()
    usernode.is_active = False
    get_profile(usernode).activation_code = activationcode
    save_user(usernode)
    return activationcode

  def activate(self, username):
    """sets the user as activated"""
    if self.hasuser(username):
      usernode = self.getusernode(username)
      usernode.is_active = True
      save_user(usernode)

  def changeusers(self, session, argdict):
    """handles multiple changes from the site admin"""
    if not session.issiteadmin():
      raise ValueError(session.localize("You need to be siteadmin to change users"))
    for key, value in argdict.iteritems():
      usernode = None
      if key.startswith("userremove-"):
        username = key.replace("userremove-", "", 1)
        if self.hasuser(username):
          User.objects.filter(username=username)[0].delete()
      elif key.startswith("username-"):
        username = key.replace("username-", "", 1)
        if self.hasuser(username):
          usernode = self.getusernode(username)
          fullname = getattr(usernode, "name", None)
          if fullname != value:
            usernode.first_name = value
      elif key.startswith("useremail-"):
        username = key.replace("useremail-", "", 1)
        if self.hasuser(username):
          usernode = self.getusernode(username)
          useremail = getattr(usernode, "email", None)
          if useremail != value:
            usernode.email = value
      elif key.startswith("userpassword-"):
        username = key.replace("userpassword-", "", 1)
        if self.hasuser(username):
          usernode = self.getusernode(username)
          if value and value.strip():
            usernode.passwdhash = web.session.md5hexdigest(value.strip())
      elif key.startswith("useractivated-"):
        # FIXME This only activates users, cannot deactivate them
        username = key.replace("useractivated-", "", 1)
        self.activate(username)
      elif key == "newusername":
        username = value.lower()
        logintype = argdict.get("newuserlogintype","")
        if not username:
          continue
        if logintype == "hash" and not (username[:1].isalpha() and username.replace("_","").isalnum()):
          raise ValueError("Login must be alphanumeric and start with an alphabetic character (got %r)" % username)
        if username in ["nobody", "default"]:
          raise ValueError('"%s" is a reserved username.' % username)
        if self.hasuser(username):
          raise ValueError("Already have user with the login: %s" % username)
        userpassword = argdict.get("newuserpassword", None)
        if logintype == "hash" and (userpassword is None or userpassword == session.localize("(add password here)")):
          raise ValueError("You must specify a password")
        userfullname = argdict.get("newuserfullname", None)
        if userfullname == session.localize("(add full name here)"):
          raise ValueError("Please set the users full name or leave it blank")
        useremail = argdict.get("newuseremail", None)
        if useremail == session.localize("(add email here)"):
          raise ValueError("Please set the users email address or leave it blank")
        useractivate = "newuseractivate" in argdict
        usernode = self.adduser(username, userfullname, useremail, userpassword, logintype)
        if useractivate:
          usernode.activate = 1
        else:
          get_profile(usernode).activation_code = self.makeactivationcode(usernode)
      if usernode:
        save_user(usernode)
    session.saveuser()

  def handleregistration(self, session, argdict):
    """handles the actual registration"""
    #TODO: Fix layout, punctuation, spacing and correlation of messages
    if not hasattr(pan_app.prefs, 'hash'):
      raise RegistrationError(session.localize("Local registration is disable."))

    supportaddress = getattr(pan_app.prefs.registration, 'supportaddress', "")
    username = argdict.get("username", "")
    if not username or not username.isalnum() or not username[0].isalpha():
      raise RegistrationError(session.localize("Username must be alphanumeric, and must start with an alphabetic character."))
    fullname = argdict.get("name", "")
    email = argdict.get("email", "")
    password = argdict.get("password", "")
    passwordconfirm = argdict.get("passwordconfirm", "")
    if " " in email or not (email and "@" in email and "." in email):
      raise RegistrationError(session.localize("You must supply a valid email address"))

    if session.loginchecker.userexists(username):
      usernode = self.getusernode(username)
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
      usernode = self.adduser(username, fullname, email, password)
      activationcode = self.makeactivationcode(usernode)
      get_profile(usernode).activation_code = activationcode
      activationlink = ""
      message = session.localize("A Pootle account has been created for you using this email address.\n")
      if pan_app.prefs.baseurl.startswith("http://"):
        message += session.localize("To activate your account, follow this link:\n")
        activationlink = pan_app.prefs.baseurl
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

      save_user(usernode)

    message += session.localize("Your user name is: %s\n", username)
    message += session.localize("Your registered email address is: %s\n", email)
    smtpserver = pan_app.prefs.registration.smtpserver
    fromaddress = pan_app.prefs.registration.fromaddress
    subject = Header(session.localize("Pootle Registration"), "utf-8").encode()
    messagedict = {"from": fromaddress, "to": [email], "subject": subject, "body": message}
    if supportaddress:
      messagedict["reply-to"] = supportaddress
    fullmessage = mailer.makemessage(messagedict)
    if isinstance(fullmessage, unicode):
      fullmessage = fullmessage.encode("utf-8")
    errmsg = mailer.dosendmessage(fromemail=pan_app.prefs.registration.fromaddress, recipientemails=[email], message=fullmessage, smtpserver=smtpserver)
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
          # BUG: We won't redirect to registration page, we will go to 
          # activation or login
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
      if self.hasuser(username):
        usernode = self.getusernode(username)
        correctcode = getattr(usernode, "activationcode", "")
        if correctcode and correctcode.strip().lower() == activationcode.strip().lower():
          usernode.is_active = True
          save_user(usernode)
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

class PootleSession(object):
  """a session object that knows about Pootle"""
  def __init__(self, request, loginchecker = None):
    """sets up the session and remembers the users prefs"""

    # In LoginSession's __init__, it defaults loginchecker to LoginChecker;
    # hence, we default it to ProgressiveLoginChecker first, before we call
    # LoginSession's __init__.
    self.messages = []
    if loginchecker == None:
      import login
      logindict = {}
      if hasattr(pan_app.prefs, 'hash'):
        logindict['hash'] = login.HashLoginChecker(self)
      if hasattr(pan_app.prefs, 'ldap'):
        logindict['ldap'] = login.LDAPLoginChecker(self)
      loginchecker = login.ProgressiveLoginChecker(self, logindict)
    self.user = request.user

  def saveuser(self):
    """saves changed preferences back to disk"""
    if self.user == None:
      return
    save_user(self.user)

  def open(self):
    """opens the session, along with the users prefs"""
    raise NotImplementedError() # This should no longer be called
    #self.getuser()
    #return self.isopen

  def close(self, req):
    """closes the session, along with the users prefs"""
    raise NotImplementedError() # This should not longer be called
    #super(PootleSession, self).close(req)
    #self.getuser()

  def addMessage(self, message):
    self.messages.append(message)

  def getMessages(self, clear=True):
    messages = self.messages
    if clear:
      self.messages = []
    return messages

  def old_validate(self):
    """DEPRECATED: Checks if this session is valid (which means the user must be activated).
    
    This is an older (but sqlalchemy aware) implimentation of validate() that
    doesn't support LDAP, but might be useful for comparisson."""
    if not super(PootleSession, self).validate():
      return False
    usernode = User.objects.filter(username=self.username)[0]
    if usernode != None:
      if usernode.is_active:
        return self.isvalid
    self.isvalid = False
    self.status = "username has not yet been activated"
    return self.isvalid

  def setoptions(self, argdict):
    """sets the user options"""
    profile = get_profile(self.user)
    userprojects = argdict.get("projects", []) # A list of the codes
    profile.projects = map(lambda code: pan_app.get_po_tree().projects[code], userprojects)
    userlanguages = argdict.get("languages", []) # A list of the codes
    profile.languages = map(lambda code: pan_app.get_po_tree().languages[code], userlanguages)
    self.saveuser()

  def setpersonaloptions(self, argdict):
    """sets the users personal details"""
    profile = get_profile(self.user)
    name = argdict.get("option-name", "")
    email = argdict.get("option-email", "")
    password = argdict.get("option-password", "")
    passwordconfirm = argdict.get("option-passwordconfirm", "")

    if password or passwordconfirm:
      validatepassword(self, password, passwordconfirm)
    self.user.first_name = name
    self.user.email = email
    if password:
      passwdhash = web.session.md5hexdigest(argdict.get("option-password", ""))
      self.user.password = passwdhash
    self.saveuser()

  def setinterfaceoptions(self, argdict):
    """sets the users interface details"""
    profile = get_profile(self.user)
    value = argdict.get("option-uilanguage", "")
    if value:
      self.user.uilanguage = value
      self.setlanguage(value)
    def setinterfacevalue(name, errormessage):
      value = argdict.get("option-%s" % name, "")
      if value != "":
        if not value.isdigit():
          raise ValueError(errormessage)
        setattr(profile, name, value)
    setinterfacevalue("input_height", self.localize("Input height must be numeric"))
    setinterfacevalue("input_width", self.localize("Input width must be numeric"))
    setinterfacevalue("view_rows", self.localize("The number of rows displayed in view mode must be numeric"))
    setinterfacevalue("translate_rows", self.localize("The number of rows displayed in translate mode must be numeric"))
    useraltsrclanguage = argdict.get("altsrclanguage", "")
    if isinstance(useraltsrclanguage, (str, unicode)) and useraltsrclanguage != "":
      setattr(self.user, "altsrclanguage", useraltsrclanguage)
    self.saveuser()

  def getprojects(self):
    """gets the user's projects"""
    userprojects = get_profile(self.user).projects.all()
    return [p.code for p in userprojects]

  def getlanguages(self):
    """gets the user's languages"""
    userlanguages = get_profile(self.user).languages.all()
    return [l.code for l in userlanguages] 

  def getaltsrclanguage(self):
    """gets the user's alternative source language"""
    # TODO: Update for Django
    useraltsrclanguage = getattr(self.user, "altsrclanguage", "")
    return useraltsrclanguage.strip()

  def issiteadmin(self):
    """returns whether the user can administer the site"""
    if self.user is not None:
      return self.user.is_superuser
    else:
      return False

