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

from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.shortcuts import get_object_or_404
from django import forms
from django.forms import ModelForm

from pootle.i18n.gettext import tr_lang

from pootle_app.models import Directory
from pootle_app.models.permissions import get_matching_permissions, check_permission
from pootle_app.views.language import navbar_dict
from pootle_profile.models import get_profile

from pootle_notifications.models import Notice

def view(request, path):
    #FIXME: why do we have leading and trailing slashes in pootle_path?
    pootle_path = '/%s' % path

    directory = get_object_or_404(Directory, pootle_path=pootle_path)

    request.permissions = get_matching_permissions(get_profile(request.user), directory)

    if not check_permission('view', request):
        raise PermissionDenied

    template_vars = {'path': path,
                     'directory': directory}

    if check_permission('administrate', request):
        template_vars['form'] = handle_form(request, directory)
        template_vars['title'] = directory_to_title(request, directory)
    if request.GET.get('all', False):
        template_vars['notices'] = Notice.objects.filter(directory__pootle_path__startswith=directory.pootle_path).select_related('directory')[:30]
    else:
        template_vars['notices'] = Notice.objects.filter(directory=directory).select_related('directory')[:30]

    if not directory.is_language() and not directory.is_project():
        try:
            request.translation_project = directory.get_translationproject()
            template_vars['navitems'] = [navbar_dict.make_directory_navbar_dict(request, directory)]
            template_vars['translation_project'] = request.translation_project
            template_vars['language'] = request.translation_project.language
            template_vars['project'] = request.translation_project.project
        except:
            pass

    return render_to_response('notices.html', template_vars, context_instance=RequestContext(request))

def directory_to_title(request, directory):
    """figures out if directory refers to a Language or
    TranslationProject and returns appropriate string for use in
    titles"""

    if directory.is_language():
        trans_vars = {
            'language': tr_lang(directory.language.fullname),
            }
        return _('News for %(language)s', trans_vars)
    elif directory.is_project():
        return _('News for %(project)s', {'project': directory.project.fullname})
    elif directory.is_translationproject():
        trans_vars = {
            'language': tr_lang(directory.translationproject.language.fullname),
            'project': directory.translationproject.project.fullname,
            }
        return _('News for the %(project)s project in %(language)s', trans_vars)
    return _('News for %(path)s',
             {'path': directory.pootle_path})

def handle_form(request, current_directory):
    class NoticeForm(ModelForm):
        directory = forms.ModelChoiceField(
            queryset=Directory.objects.filter(pk=current_directory.pk),
            initial=current_directory.pk, widget=forms.HiddenInput)

        class Meta:
            model = Notice

    if request.method == 'POST':
        form = NoticeForm(request.POST)
        if form.is_valid():
            form.save()
            form = NoticeForm()
    else:
        form = NoticeForm()

    return form


def view_notice_item(request, path, notice_id):
    notice = get_object_or_404(Notice, id=notice_id)
    template_vars = {
            "title" : _("View News Item"),
            "notice_message"  : notice.message,
            }

    return render_to_response('viewnotice.html', template_vars,
                              context_instance=RequestContext(request))
