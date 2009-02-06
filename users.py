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

from Pootle import pagelayout
from translate.lang import data as langdata
from translate.lang import factory
from email.Header import Header
import locale
import Cookie
import re
import time

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.conf import settings
from django.utils.translation import ugettext as _
N_ = _

from pootle_app.profile import get_profile
from Pootle import pan_app
from Pootle.i18n.jtoolkit_i18n import localize, tr_lang

class RegistrationError(ValueError):
  def __init__(self, message):
    message = message.encode('utf-8')
    ValueError.__init__(self, message)

# This mimimum passwordlength is mandated by the interface when registering or 
# changing password
minpasswordlen = 6

def validatepassword(request, password, passwordconfirm):
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
  def __init__(self, request, languagenames=None, message=None):
    self.languagenames = languagenames
    pagetitle = localize("Login to Pootle")
    templatename = "login"
    message = forcemessage(message)
    instancetitle = pan_app.get_title()
    requestvars = {"status": get_profile(request.user).status, "isopen": not request.user.is_anonymous, "issiteadmin": request.user.is_superuser}
    templatevars = {"pagetitle": pagetitle, "introtext": message,
        "username_title": localize("Username:"),
        "username": getattr(request, 'username', ''),
        "password_title": localize("Password:"),
        "language_title": localize('Language:'),
        "languages": self.getlanguageoptions(request),
        "login_text": localize('Login'),
        "register_text": localize('Register'),
        "request": requestvars, "instancetitle": instancetitle}
    pagelayout.PootlePage.__init__(self, templatename, templatevars, request)

  def getlanguageoptions(self, request):
    """returns the language selector..."""
    tr_default = localize("Default")
    if tr_default != "Default":
        tr_default = u"%s | \u202dDefault" % tr_default
    languageoptions = [('', tr_default)]
    if isinstance(self.languagenames, dict):
      languageoptions += self.languagenames.items()
    else:
      languageoptions += self.languagenames
    if request.language in ["en", request.server.defaultlanguage]:
        preferredlanguage = ""
    else:
        preferredlanguage = request.language
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
  def __init__(self, request, message=None):
    if not message:
      introtext = localize("Please enter your registration details")
    else:
      introtext = forcemessage(message)
    pagetitle = localize("Pootle Registration")
    templatename = "register"
    instancetitle = pan_app.get_title()
    requestvars = {"status": get_profile(request.user).status, "isopen": not request.user.is_anonymous, "issiteadmin": request.user.is_superuser}
    templatevars = {
        "pagetitle":               pagetitle,
        "introtext":               introtext,
        "username_title":          localize("Username"),
        "username_tooltip":        localize("Your requested username"),
        "username":                request.POST.get("username", ""),
        "email_title":             localize("Email Address"),
        "email_tooltip":           localize("You must supply a valid email address"),
        "email":                   request.POST.get("email", ""),
        "fullname_title":          localize("Full Name"),
        "fullname_tooltip":        localize("Your full name"),
        "fullname":                request.POST.get("name", ""),
        "password_title":          localize("Password"),
        "password_tooltip":        localize("Your desired password"),
        "password":                request.POST.get("password", ""),
        "passwordconfirm_title":   localize("Confirm password"),
        "passwordconfirm_tooltip": localize("Type your password again to ensure it is entered correctly"),
        "passwordconfirm":         request.POST.get("passwordconfirm", ""),
        "register_text":           localize('Register Account'),
        "request":                 requestvars,
        "instancetitle":           instancetitle}
    pagelayout.PootlePage.__init__(self, templatename, templatevars, request)

class ActivatePage(pagelayout.PootlePage):
  """page for new registrations"""
  def __init__(self, request, title=None, message=None):
    if not message:
      introtext = localize("Please enter your activation details")
    else:
      introtext = forcemessage(message)
    if title is None:
      pagetitle = localize("Pootle Account Activation")
    else:
      pagetitle = title
    templatename = "activate"
    instancetitle = pan_app.get_title()
    requestvars = {"status": get_profile(request.user).status, "isopen": not request.user.is_anonymous, "issiteadmin": request.user.is_superuser}
    templatevars = {
        "pagetitle":        pagetitle,
        "introtext":        introtext,
        "username_title":   localize("Username"),
        "username_tooltip": localize("Your requested username"),
        "username":         request.POST.get("username", ""),
        "code_title":       localize("Activation Code"),
        "code_tooltip":     localize("The activation code you received"),
        "code":             request.POST.get("activationcode", ""),
        "activate_text":    localize('Activate Account'),
        "request":          requestvars,
        "instancetitle":    instancetitle}
    pagelayout.PootlePage.__init__(self, templatename, templatevars, request)

def with_user(username, f):
  try:
    user = User.objects.include_hidden().get(username=username)
    f(user)
    return user
  except User.DoesNotExist:
    return None

class OptionalLoginAppServer(object):
  """a server that enables login but doesn't require it except for specified pages"""
  def handle(self, req, pathwords, argdict):
    """handles the request and returns a page object in response"""
    request = None
    try:
      argdict = self.processargs(argdict)
      request = self.getrequest(req, argdict)
      if settings.BASE_URL[-1] == '/':
        request.currenturl = settings.BASE_URL[:-1] + req.path
      else:
        request.currenturl = settings.BASE_URL + req.path
      request.reqpath = req.path
      if req.path.find("?") >= 0:
        request.getsuffix = req.path[req.path.find("?"):]
      else:
        request.getsuffix = "" 
      if request.isopen:
        request.pagecount += 1
        request.remote_ip = self.getremoteip(req)
        request.localaddr = self.getlocaladdr(req)
      else:
        self.initlanguage(req, request)
      page = self.getpage(pathwords, request, argdict)
    except Exception, e:
      # Because of the exception, 'request' might not be initialised. So let's
      # play extra safe
      if not request:
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
      pagelayout.completetemplatevars(templatevars, request)
      page = server.Redirect(refreshurl, withtemplate=(templatename, templatevars))
    return page

  def initlanguage(self, req, request):
    """Initialises the request language from the request"""
    # This version doesn't know which languages we have, so we have to override
    # in PootleServer.
    request.setlanguage("en")
      
  def adduser(self, username, fullname, email, password, logintype="hash"):
    """adds the user with the given details"""
    user = User(username=username,
                first_name=fullname,
                email=email)
    user.set_password(password)
    user.save()
    return user

  def set_activation_code(self, user):
    """makes a new activation code for the user and returns it"""
    user.is_active = False
    user.save()
    profile = user.get_profile()
    profile.activation_code = self.generateactivationcode()
    profile.save()
    return profile.activation_code

  def changeusers(self, request):
    """handles multiple changes from the site admin"""
    # TODO: Move admin authentication to the view containing this
    for key, value in request.POST.iteritems():
      user = None
      if key.startswith("userremove-"):
        username = key.replace("userremove-", "", 1)
        def delete_user(user):
          user.delete()
        user = with_user(username, lambda user: user.delete())
      elif key.startswith("username-"):
        username = key.replace("username-", "", 1)
        def set_user_name(user):
          if user.first_name != value:
            user.first_name = value
        user = with_user(username, set_user_name)
      elif key.startswith("useremail-"):
        username = key.replace("useremail-", "", 1)
        def set_user_email(user):
          if user.email != value:
            user.email = value
          user = with_user(username, set_user_email)
      elif key.startswith("userpassword-"):
        username = key.replace("userpassword-", "", 1)
        def set_user_password(user):
          if value and value.strip():
            user.set_password(value.strip())
        user = with_user(username, set_user_password)
      elif key.startswith("useractivated-"):
        username = key.replace("useractivated-", "", 1)
        def set_user_active(user):
          user.is_active = value == 'checked'
        user = with_user(username, set_user_active)
      elif key == "newusername":
        username = value.lower()
        logintype = request.POST.get("newuserlogintype","")
        if not username:
          continue
        if logintype == "hash" and not (username[:1].isalpha() and username.replace("_","").isalnum()):
          raise ValueError("Login must be alphanumeric and start with an alphabetic character (got %r)" % username)
        if username in ["nobody", "default"]:
          raise ValueError('"%s" is a reserved username.' % username)
        if self.hasuser(username):
          raise ValueError("Already have user with the login: %s" % username)
        userpassword = request.POST.get("newuserpassword", None)
        if logintype == "hash" and (userpassword is None or userpassword == localize("(add password here)")):
          raise ValueError("You must specify a password")
        userfullname = request.POST.get("newuserfullname", None)
        if userfullname == localize("(add full name here)"):
          raise ValueError("Please set the users full name or leave it blank")
        useremail = request.POST.get("newuseremail", None)
        if useremail == localize("(add email here)"):
          raise ValueError("Please set the users email address or leave it blank")
        useractivate = "newuseractivate" in request.POST
        user = self.adduser(username, userfullname, useremail, userpassword, logintype)
        if useractivate:
          user.is_active = True
        else:
          self.set_activation_code(user)
      if user:
        user.save()

  def handleregistration(self, request):
    """handles the actual registration"""
    supportaddress = settings.SUPPORT_ADDRESS
    username = request.POST.get("username", "")
    if not username or not username.isalnum() or not username[0].isalpha():
      raise RegistrationError(localize("Username must be alphanumeric, and must start with an alphabetic character."))
    fullname = request.POST.get("name", "")
    email = request.POST.get("email", "")
    password = request.POST.get("password", "")
    passwordconfirm = request.POST.get("passwordconfirm", "")
    if " " in email or not (email and "@" in email and "." in email):
      raise RegistrationError(localize("You must supply a valid email address"))

    try:
      user = User.objects.get(username=username)
      # use the email address on file
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
    except User.DoesNotExist:
      validatepassword(request, password, passwordconfirm)
      user = self.adduser(username, fullname, email, password)
      activation_code = self.set_activation_code(user)
      activationlink = ""
      message = localize("A Pootle account has been created for you using this email address.\n")
      if settings.BASE_URL.startswith("http://"):
        message += localize("To activate your account, follow this link:\n")
        activationlink = settings.BASE_URL
        if not activationlink.endswith("/"):
          activationlink += "/"
        activationlink += "activate.html?username=%s&activationcode=%s" % (username, activation_code)
        message += "  %s  \n" % activationlink
      message += localize("Your activation code is:\n%s\n", activation_code)
      if activationlink:
        message += localize("If you are unable to follow the link, please enter the above code at the activation page.\n")
      message += localize("This message is sent to verify that the email address is in fact correct. If you did not want to register an account, you may simply ignore the message.\n")
      redirecturl = "activate.html?username=%s" % username
      displaymessage = localize("Account created. You will be emailed login details and an activation code. Please enter your activation code on the <a href='%s'>activation page</a>.", redirecturl)
      if activationlink:
        displaymessage += " " + localize("(Or simply click on the activation link in the email)")

    message += localize("Your user name is: %s\n", username)
    message += localize("Your registered email address is: %s\n", email)
    smtpserver = settings.REGISTRATION_SMTP_SERVER
    fromaddress = settings.REGISTRATION_FROM_ADDRESS
    subject = Header(localize("Pootle Registration"), "utf-8").encode()
    messagedict = {"from": fromaddress, "to": [email], "subject": subject, "body": message}
    if supportaddress:
      messagedict["reply-to"] = supportaddress
    fullmessage = mailer.makemessage(messagedict)
    if isinstance(fullmessage, unicode):
      fullmessage = fullmessage.encode("utf-8")
    errmsg = mailer.dosendmessage(fromemail=settings.REGISTRATION_FROM_ADDRESS, recipientemails=[email], message=fullmessage, smtpserver=smtpserver)
    if errmsg:
      raise RegistrationError("Error sending mail: %s" % errmsg)
    return displaymessage, redirecturl

  def registerpage(self, request):
    """handle registration or return the Register page"""
    if request.method == 'POST':
      try:
        displaymessage, redirecturl = self.handleregistration(request)
      except RegistrationError, message:
        return RegisterPage(request, message)
      redirectpage = pagelayout.PootlePage("Redirecting...", {}, request)
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
      return RegisterPage(request)

  def activatepage(self, request):
    """handle activation or return the Register page"""
    if request.method == 'POST':
      username = request.POST["username"]
      def activate_user(user):
        if user.get_profile().activation_code == request.POST["activationcode"].strip().lower():
          user.is_active = True
          user.save()
      user = with_user(username, activate_user)
      if user.is_active:
        redirectpage = pagelayout.PootlePage("Redirecting to login...", {}, request)
        redirectpage.templatename = "redirect"
        redirectpage.templatevars = {
            "pagetitle": localize("Redirecting to login Page..."),
            "refresh": 10,
            "refreshurl": "login.html?username=%s" % username,
            "message": localize("Your account has been activated! Redirecting to login..."),
            }
        redirectpage.completevars()
        return redirectpage
      else:
        failedmessage = localize("The activation information was not valid.")
        return ActivatePage(request, title=localize("Activation Failed"), message=failedmessage)
    else:
      return ActivatePage(request)

