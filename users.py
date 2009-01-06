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
from Pootle.i18n.jtoolkit_i18n import localize, tr_lang

class RegistrationError(ValueError):
  def __init__(self, message):
    message = message.encode('utf-8')
    ValueError.__init__(self, message)

# This mimimum passwordlength is mandated by the interface when registering or 
# changing password
minpasswordlen = 6

def validatepassword(session, password, passwordconfirm):
  if not password or len(password) < minpasswordlen:
    raise RegistrationError(localize("You must supply a valid password of at least %d characters.", minpasswordlen))
  if not password == passwordconfirm:
    raise RegistrationError(localize("The password is not the same as the confirmation."))

def forcemessage(message):
  """Tries to extract some kind of message and converts to unicode"""
  if message and not isinstance(message, unicode):
    return str(message).decode('utf-8')
  else:
    return message

class LoginPage(pagelayout.PootlePage):
  """wraps the normal login page in a PootlePage layout"""
  def __init__(self, session, languagenames=None, message=None):
    self.languagenames = languagenames
    pagetitle = localize("Login to Pootle")
    templatename = "login"
    message = forcemessage(message)
    instancetitle = getattr(pan_app.prefs, "title", localize("Pootle Demo"))
    sessionvars = {"status": get_profile(request.user).status, "isopen": not request.user.is_anonymous, "issiteadmin": request.user.is_superuser}
    templatevars = {"pagetitle": pagetitle, "introtext": message,
        "username_title": localize("Username:"),
        "username": getattr(session, 'username', ''),
        "password_title": localize("Password:"),
        "language_title": localize('Language:'),
        "languages": self.getlanguageoptions(session),
        "login_text": localize('Login'),
        "register_text": localize('Register'),
        "session": sessionvars, "instancetitle": instancetitle}
    pagelayout.PootlePage.__init__(self, templatename, templatevars, session)

  def getlanguageoptions(self, session):
    """returns the language selector..."""
    tr_default = localize("Default")
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
        tr_name = tr_lang(value)
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
  def __init__(self, request, argdict, message=None):
    if not message:
      introtext = localize("Please enter your registration details")
    else:
      introtext = forcemessage(message)
    pagetitle = localize("Pootle Registration")
    self.argdict = argdict
    templatename = "register"
    instancetitle = getattr(pan_app.prefs, "title", localize("Pootle Demo"))
    sessionvars = {"status": get_profile(request.user).status, "isopen": not request.user.is_anonymous, "issiteadmin": request.user.is_superuser}
    templatevars = {"pagetitle": pagetitle, "introtext": introtext,
        "username_title": localize("Username"),
        "username_tooltip": localize("Your requested username"),
        "username": self.argdict.get("username", ""),
        "email_title": localize("Email Address"),
        "email_tooltip": localize("You must supply a valid email address"),
        "email": self.argdict.get("email", ""),
        "fullname_title": localize("Full Name"),
        "fullname_tooltip": localize("Your full name"),
        "fullname": self.argdict.get("name", ""),
        "password_title": localize("Password"),
        "password_tooltip": localize("Your desired password"),
        "password": self.argdict.get("password", ""),
        "passwordconfirm_title": localize("Confirm password"),
        "passwordconfirm_tooltip": localize("Type your password again to ensure it is entered correctly"),
        "passwordconfirm": self.argdict.get("passwordconfirm", ""),
        "register_text": localize('Register Account'),
        "session": sessionvars, "instancetitle": instancetitle}
    pagelayout.PootlePage.__init__(self, templatename, templatevars, request)

class ActivatePage(pagelayout.PootlePage):
  """page for new registrations"""
  def __init__(self, request, argdict, title=None, message=None):
    if not message:
      introtext = localize("Please enter your activation details")
    else:
      introtext = forcemessage(message)
    self.argdict = argdict
    if title is None:
      pagetitle = localize("Pootle Account Activation")
    else:
      pagetitle = title
    templatename = "activate"
    instancetitle = getattr(pan_app.prefs, "title", localize("Pootle Demo"))
    sessionvars = {"status": get_profile(request.user).status, "isopen": not request.user.is_anonymous, "issiteadmin": request.user.is_superuser}
    templatevars = {"pagetitle": pagetitle, "introtext": introtext,
        "username_title": localize("Username"),
        "username_tooltip": localize("Your requested username"),
        "username": self.argdict.get("username", ""),
        "code_title": localize("Activation Code"),
        "code_tooltip": localize("The activation code you received"),
        "code": self.argdict.get("activationcode", ""),
        "activate_text": localize('Activate Account'),
        "session": sessionvars, "instancetitle": instancetitle}
    pagelayout.PootlePage.__init__(self, templatename, templatevars, request)

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
          "pagetitle": localize("Error"),
          "refresh": 30,
          "refreshurl": refreshurl,
          "message": errormessage,
          "traceback": browsertraceback,
          "back": localize("Back"),
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
      raise ValueError(localize("You need to be siteadmin to change users"))
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
        if logintype == "hash" and (userpassword is None or userpassword == localize("(add password here)")):
          raise ValueError("You must specify a password")
        userfullname = argdict.get("newuserfullname", None)
        if userfullname == localize("(add full name here)"):
          raise ValueError("Please set the users full name or leave it blank")
        useremail = argdict.get("newuseremail", None)
        if useremail == localize("(add email here)"):
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
      raise RegistrationError(localize("Local registration is disable."))

    supportaddress = getattr(pan_app.prefs.registration, 'supportaddress', "")
    username = argdict.get("username", "")
    if not username or not username.isalnum() or not username[0].isalpha():
      raise RegistrationError(localize("Username must be alphanumeric, and must start with an alphabetic character."))
    fullname = argdict.get("name", "")
    email = argdict.get("email", "")
    password = argdict.get("password", "")
    passwordconfirm = argdict.get("passwordconfirm", "")
    if " " in email or not (email and "@" in email and "." in email):
      raise RegistrationError(localize("You must supply a valid email address"))

    if session.loginchecker.userexists(username):
      usernode = self.getusernode(username)
      # use the email address on file
      email = getattr(usernode, "email", email)
      password = ""
      # TODO: we can't figure out the password as we only store the md5sum. have a password reset mechanism
      message = localize("You (or someone else) attempted to register an account with your username.\n")
      message += localize("We don't store your actual password but only a hash of it.\n")
      if supportaddress:
        message += localize("If you have a problem with registration, please contact %s.\n", supportaddress)
      else:
        message += localize("If you have a problem with registration, please contact the site administrator.\n")
      displaymessage = localize("That username already exists. An email will be sent to the registered email address.\n")
      redirecturl = "login.html?username=%s" % username
      displaymessage += localize("Proceeding to <a href='%s'>login</a>\n", redirecturl)
    else:
      validatepassword(session, password, passwordconfirm)
      usernode = self.adduser(username, fullname, email, password)
      activationcode = self.makeactivationcode(usernode)
      get_profile(usernode).activation_code = activationcode
      activationlink = ""
      message = localize("A Pootle account has been created for you using this email address.\n")
      if pan_app.prefs.baseurl.startswith("http://"):
        message += localize("To activate your account, follow this link:\n")
        activationlink = pan_app.prefs.baseurl
        if not activationlink.endswith("/"):
          activationlink += "/"
        activationlink += "activate.html?username=%s&activationcode=%s" % (username, activationcode)
        message += "  %s  \n" % activationlink
      message += localize("Your activation code is:\n%s\n", activationcode)
      if activationlink:
        message += localize("If you are unable to follow the link, please enter the above code at the activation page.\n")
      message += localize("This message is sent to verify that the email address is in fact correct. If you did not want to register an account, you may simply ignore the message.\n")
      redirecturl = "activate.html?username=%s" % username
      displaymessage = localize("Account created. You will be emailed login details and an activation code. Please enter your activation code on the <a href='%s'>activation page</a>.", redirecturl)
      if activationlink:
        displaymessage += " " + localize("(Or simply click on the activation link in the email)")

      save_user(usernode)

    message += localize("Your user name is: %s\n", username)
    message += localize("Your registered email address is: %s\n", email)
    smtpserver = pan_app.prefs.registration.smtpserver
    fromaddress = pan_app.prefs.registration.fromaddress
    subject = Header(localize("Pootle Registration"), "utf-8").encode()
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
          "pagetitle": localize("Redirecting to Registration Page..."),
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
              "pagetitle": localize("Redirecting to login Page..."),
              "refresh": 10,
              "refreshurl": "login.html?username=%s" % username,
              "message": localize("Your account has been activated! Redirecting to login..."),
              }
          redirectpage.completevars()
          return redirectpage
      failedmessage = localize("The activation information was not valid.")
      return ActivatePage(session, argdict, title=localize("Activation Failed"), message=failedmessage)
    else:
      return ActivatePage(session, argdict)

