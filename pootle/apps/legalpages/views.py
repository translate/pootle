#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2012 Zuza Software Foundation
#
# This file is part of Pootle.
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

from django.shortcuts import get_object_or_404, redirect, render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext as _

from legalpages.forms import LegalPageForm
from legalpages.models import LegalPage
from pootle_app.views.admin.util import user_is_admin


@user_is_admin
def admin_page(request, page_id):
    """Administration view."""
    lp = get_object_or_404(LegalPage, id=page_id)

    if request.method == 'POST':

        if '_delete' in request.POST:
            lp.delete()
            return redirect('legalpages.views.admin')

        form = LegalPageForm(request.POST, instance=lp)

        if form.is_valid():
            form.save()
            return redirect('legalpages.views.admin')

    else:
        form = LegalPageForm(instance=lp)

    return render_to_response('legalpages/admin/edit.html',
            {'form': form, 'show_delete': True},
            RequestContext(request))


@user_is_admin
def admin(request):
    """Lists available pages in the administration."""
    msg = ''

    if request.method == 'POST':
        form = LegalPageForm(request.POST)

        if form.is_valid():
            form.save()
            form = LegalPageForm()
            msg = _("Legal Page created.")
    else:
        form = LegalPageForm()

    lps = LegalPage.objects.all()

    return render_to_response('legalpages/admin/list.html',
            {'legalpages': lps, 'form': form, 'message': msg,
             'show_delete': False},
            RequestContext(request))


def legalpage(request, slug):
    """The actual Legal Page."""
    lp = get_object_or_404(LegalPage, active=True, slug=slug)

    if lp.url:
        return redirect(lp.url)

    template_name = 'legalpages/legalpage.html'
    if 'HTTP_X_FANCYBOX' in request.META:
        template_name = 'legalpages/legalpage_body.html'

    return render_to_response(template_name, {'lp': lp},
            RequestContext(request))
