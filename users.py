#!/usr/bin/python
# -*- coding: utf-8 -*-
#  Copyright 2004-2009 Zuza Software Foundation
#
# This file is part of Pootle.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, see <http://www.gnu.org/licenses/>.

from Pootle import pagelayout
from email.Header import Header
from django.core.mail import EmailMessage
from django.contrib.auth.models import User
from django.conf import settings
from django.utils.translation import ugettext as _
N_ = _
from pootle_app.models.profile import get_profile
from Pootle import pan_app
from pootle_app.lib.util import l
import md5
import random


class RegistrationError(ValueError):
    def __init__(self, message):
        message = message.encode('utf-8')
        ValueError.__init__(self, message)


# This mimimum passwordlength is mandated by the interface when
# registering or changing password
minpasswordlen = 6


def validatepassword(request, password, passwordconfirm):
    if not password or len(password) < minpasswordlen:
        raise RegistrationError(_('You must supply a valid password of at least %d characters.'
                                 % minpasswordlen))
    if not password == passwordconfirm:
        raise RegistrationError(_('The password is not the same as the confirmation.'))


def forcemessage(message):
    """Tries to extract some kind of message and converts to unicode
    """

    if message and not isinstance(message, unicode):
        return str(message).decode('utf-8')
    else:
        return message


class RegisterPage(pagelayout.PootlePage):
    """page for new registrations
    """

    def __init__(self, request, message=None):
        if not message:
            introtext = _('Please enter your registration details')
        else:
            introtext = forcemessage(message)
        pagetitle = _('Pootle Registration')
        templatename = 'index/register.html'
        instancetitle = pan_app.get_title()
        requestvars = {'status': get_profile(request.user).status,
                       'isopen': not request.user.is_anonymous,
                       'issiteadmin': request.user.is_superuser}
        templatevars = {
            'pagetitle': pagetitle,
            'introtext': introtext,
            'username_title': _('Username'),
            'username_tooltip': _('Your requested username'),
            'username': request.POST.get('username', ''),
            'email_title': _('Email Address'),
            'email_tooltip': _('You must supply a valid email address'),
            'email': request.POST.get('email', ''),
            'fullname_title': _('Full Name'),
            'fullname_tooltip': _('Your full name'),
            'fullname': request.POST.get('name', ''),
            'password_title': _('Password'),
            'password_tooltip': _('Your desired password'),
            'password': request.POST.get('password', ''),
            'passwordconfirm_title': _('Confirm password'),
            'passwordconfirm_tooltip': _('Type your password again to ensure it is entered correctly'
                    ),
            'passwordconfirm': request.POST.get('passwordconfirm', ''),
            'register_text': _('Register Account'),
            'request': requestvars,
            'instancetitle': instancetitle,
            }
        pagelayout.PootlePage.__init__(self, templatename, templatevars,
                                       request)


class ActivatePage(pagelayout.PootlePage):
    """page for new registrations
    """

    def __init__(self, request, title=None, message=None):
        if not message:
            introtext = _('Please enter your activation details')
        else:
            introtext = forcemessage(message)
        if title is None:
            pagetitle = _('Pootle Account Activation')
        else:
            pagetitle = title
        templatename = 'index/activate.html'
        instancetitle = pan_app.get_title()
        requestvars = {'status': get_profile(request.user).status,
                       'isopen': not request.user.is_anonymous,
                       'issiteadmin': request.user.is_superuser}
        templatevars = {
            'pagetitle': pagetitle,
            'introtext': introtext,
            'username_title': _('Username'),
            'username_tooltip': _('Your requested username'),
            'username': request.POST.get('username', ''),
            'code_title': _('Activation Code'),
            'code_tooltip': _('The activation code you received'),
            'code': request.POST.get('activationcode', ''),
            'activate_text': _('Activate Account'),
            'request': requestvars,
            'instancetitle': instancetitle,
            }
        pagelayout.PootlePage.__init__(self, templatename, templatevars,
                                       request)


def with_user(username, f):
    try:
        user = User.objects.include_hidden().get(username=username)
        f(user)
        return user
    except User.DoesNotExist:
        return None


def set_activation_code(user):
    """makes a new activation code for the user and returns it
    """

    user.is_active = False
    user.save()
    profile = user.get_profile()
    profile.activation_code = generateactivationcode()
    profile.save()
    return profile.activation_code


def handleregistration(request):
    """handles the actual registration
    """

    supportaddress = settings.SUPPORT_ADDRESS
    username = request.POST.get('username', '')
    if not username or not username.isalnum() or not username[0].isalpha():
        raise RegistrationError(_('Username must be alphanumeric, and must start with an alphabetic character.'
                                ))
    fullname = request.POST.get('name', '')
    email = request.POST.get('email', '')
    password = request.POST.get('password', '')
    passwordconfirm = request.POST.get('passwordconfirm', '')
    if ' ' in email or not (email and '@' in email and '.' in email):
        raise RegistrationError(_('You must supply a valid email address'))
    try:
        user = User.objects.get(username=username)
        # use the email address on file TODO: we can't figure out the
        # password as we only store the md5sum. have a password reset
        # mechanism
        message = \
            _('You (or someone else) attempted to register an account with your username.\n'
              )
        message += \
            _("We don't store your actual password but only a hash of it.\n")
        if supportaddress:
            message += \
                _('If you have a problem with registration, please contact %s.\n'
                   % supportaddress)
        else:
            message += \
                _('If you have a problem with registration, please contact the site administrator.\n'
                  )
        displaymessage = \
            _('That username already exists. An email will be sent to the registered email address.\n'
              )
        redirecturl = 'login.html?username=%s' % username
        displaymessage += _("Proceeding to <a href='%s'>login</a>\n"
                             % redirecturl)
    except User.DoesNotExist:
        validatepassword(request, password, passwordconfirm)
        user = User(username=username, first_name=fullname, email=email,
                    password=md5.new(password).hexdigest())
        activation_code = set_activation_code(user)
        activationlink = ''
        message = \
            _('A Pootle account has been created for you using this email address.\n'
              )
        if settings.BASE_URL.startswith('http://'):
            message += _('To activate your account, follow this link:\n')
            activationlink = settings.BASE_URL
            if not activationlink.endswith('/'):
                activationlink += '/'
            activationlink += l('/activate.html?username=%s&activationcode=%s'
                                 % (username, activation_code))
            message += '  %s  \n' % activationlink
        message += _("Your activation code is:\n %s" % activation_code)
        if activationlink:
            message += \
                _('If you are unable to follow the link, please enter the above code at the activation page.\n')
        message += \
            _('This message is sent to verify that the email address is in fact correct. If you did not want to register an account, you may simply ignore the message.\n')
        redirecturl = 'activate.html?username=%s' % username
        displaymessage = \
            _("Account created. You will be emailed login details and an activation code. Please enter your activation code on the <a href='%s'>activation page</a>."
               % redirecturl)
        if activationlink:
            displaymessage += ' '\
                 + _('(Or simply click on the activation link in the email)')
        user.save()
    message += _('Your user name is: %s\n' % username)
    message += _('Your registered email address is: %s\n' % email)
    smtpserver = settings.REGISTRATION_SMTP_SERVER
    fromaddress = settings.REGISTRATION_FROM_ADDRESS
    subject = Header(_('Pootle Registration'), 'utf-8').encode()
    messagedict = {
        'from': fromaddress,
        'to': [email],
        'subject': subject,
        'body': message,
        }
    mail_headers = {}
    if supportaddress:
        mail_headers['reply-to'] = supportaddress
    message = EmailMessage(messagedict['subject'], messagedict['body'],
                           messagedict['from'], messagedict['to'],
                           headers=mail_headers)
    errmsg = message.send()
    # if errmsg: raise RegistrationError("Error sending mail: %s" %
    # errmsg)
    return (displaymessage, redirecturl)


def registerpage(request):
    """handle registration or return the Register page
    """

    if request.method == 'POST':
        try:
            (displaymessage, redirecturl) = handleregistration(request)
        except RegistrationError, message:
            return RegisterPage(request, message)
        redirectpage = pagelayout.PootlePage('Redirecting...', {}, request)
        redirectpage.templatename = 'index/redirect.html'
        redirectpage.templatevars = {
            'pagetitle': _('Redirecting to Registration Page...'),
            'refresh': 10,
            'refreshurl': redirecturl,
            'message': displaymessage,
            }
        redirectpage.completevars()
        return redirectpage
    else:
        return RegisterPage(request)


def activatepage(request):
    """handle activation or return the Register page
    """

    if 'username' in request.GET:
        username = request.GET['username']
        activationcode = request.GET['activationcode'].strip().lower()
    if request.method == 'POST':
        username = request.POST['username']
        activationcode = request.POST['activationcode'].strip().lower()
    user = User.objects.get(username=username)
    if user.get_profile().activation_code == activationcode:
        user.is_active = True
        user.save()
        redirectpage = pagelayout.PootlePage('Redirecting to login...', {}, request)
        redirectpage.templatename = 'index/redirect.html'
        redirectpage.templatevars = {
            'pagetitle': _('Redirecting to login page...'),
            'refresh': 10,
            'refreshurl': 'login.html?username=%s' % username,
            'message': _('Your account has been activated! Redirecting to login...'),
            }
        redirectpage.completevars()
        return redirectpage
    else:
        failedmessage = _('The activation information was not valid.')
        return ActivatePage(request, title=_('Activation Failed'),
                            message=failedmessage)


def generateactivationcode():
    """generates a unique activation code
    """

    return ''.join(['%02x' % int(random.random() * 0x100) for i in range(16)])


