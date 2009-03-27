#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Zuza Software Foundation
#
# This file is part of Pootle.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

from django.contrib.auth.models import User

from pootle_app.views import pagelayout
from pootle_app.views.util import render_jtoolkit
from pootle_app.views.index.util import forcemessage
from pootle_app.models.profile import get_profile

from Pootle import pan_app

def view(request):
    return render_jtoolkit(activatepage(request))


def activatepage(request):
    """handle activation or return the Register page
    """

    username = None
    activationcode = None
    failedmessage = None
    
    if 'username' in request.GET:
        username = request.GET['username']
    if 'activationcode' in request.GET:
        activationcode = request.GET['activationcode'].strip().lower()
        
    if request.method == 'POST':
        if 'username' in request.POST:
            username = request.POST['username']
        if 'activationcode' in request.POST:
            activationcode = request.POST['activationcode'].strip().lower()

    if (username and activationcode):
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
