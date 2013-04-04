#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2012 Zuza Software Foundation
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

from django.db.models import Q
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext as _

from pootle.i18n.gettext import tr_lang
from pootle_app.models import Directory
from pootle_app.models.permissions import (get_matching_permissions,
                                           check_permission,
                                           check_profile_permission)
from pootle_language.models import Language
from pootle_misc.mail import send_mail
from pootle_notifications.models import Notice
from pootle_project.models import Project
from pootle_profile.models import get_profile, PootleProfile
from pootle_translationproject.models import TranslationProject


def view(request, path):
    #FIXME: why do we have leading and trailing slashes in pootle_path?
    pootle_path = '/%s' % path

    directory = get_object_or_404(Directory, pootle_path=pootle_path)

    request.permissions = get_matching_permissions(get_profile(request.user),
                                                   directory)

    if not check_permission('view', request):
        raise PermissionDenied

    template_vars = {'path': path,
                     'directory': directory}

    # Find language and project defaults, passed to handle_form
    proj = None
    lang = None
    if not directory.is_language() and not directory.is_project():
        translation_project = directory.translation_project
        lang = translation_project.language
        proj = translation_project.project
    else:
        if directory.is_language():
            lang = directory.language
            proj = None
        if directory.is_project():
            lang = None
            proj = directory.project


    if check_permission('administrate', request):
        # Thus, form is only set for the template if the user has
        # 'administrate' permission
        template_vars['form'] = handle_form(request, directory, proj, lang,
                                            template_vars)
        template_vars['title'] = directory_to_title(directory)
    else:
        template_vars['form'] = None

    if request.GET.get('all', False):
        template_vars['notices'] = Notice.objects.filter(directory__pootle_path__startswith=directory.pootle_path).select_related('directory')[:30]
    else:
        template_vars['notices'] = Notice.objects.filter(directory=directory).select_related('directory')[:30]

    if not directory.is_language() and not directory.is_project():
        request.translation_project = directory.translation_project
        template_vars['translation_project'] = request.translation_project
        template_vars['language'] = request.translation_project.language
        template_vars['project'] = request.translation_project.project

    return render_to_response('notices.html', template_vars,
                              context_instance=RequestContext(request))


def directory_to_title(directory):
    """Figures out if directory refers to a Language or TranslationProject and
    returns appropriate string for use in titles."""

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


def create_notice(creator, message, directory):
    profile = get_profile(creator)
    if not check_profile_permission(profile, 'administrate', directory):
        raise PermissionDenied
    new_notice = Notice()
    new_notice.message = message
    new_notice.directory = directory
    new_notice.save()
    return new_notice


def form_factory(current_directory):
    from django.forms import ModelForm
    from django import forms
    is_root = current_directory.pootle_path == '/'

    class _NoticeForm(ModelForm):
        directory = forms.ModelChoiceField(
            queryset=Directory.objects.filter(pk=current_directory.pk),
            initial=current_directory.pk,
            widget=forms.HiddenInput,
        )
        publish_rss = forms.BooleanField(label=_('Publish on news feed'),
                required=False, initial=True)
        send_email = forms.BooleanField(label=_('Send email'), required=False)
        email_header = forms.CharField(label=_('Title'), required=False)
        restrict_to_active_users = forms.BooleanField(
                label=_('Email only to recently active users'),
                required=False,
                initial=True,
        )

        # Project selection
        if current_directory.is_language() or is_root:
            project_all = forms.BooleanField(
                    label=_('All Projects'),
                    required=False,
            )
            project_selection = forms.ModelMultipleChoiceField(
                    label=_("Project Selection"),
                    queryset=Project.objects.all(),
                    required=False,
            )

        # Language selection
        if current_directory.is_project() or is_root:
            language_all = forms.BooleanField(
                    label=_('All Languages'),
                    required=False,
            )
            language_selection = forms.ModelMultipleChoiceField(
                    label=_("Language Selection"),
                    queryset=current_directory.project.languages,
                    required=False,
            )

        class Meta:
            model = Notice

    return _NoticeForm


def handle_form(request, current_directory, current_project,
                current_language, template_vars):
    if request.method != 'POST':
        # Not a POST method. Return a default starting state of the form
        return form_factory(current_directory)()

    # Reconstruct the NoticeForm with the user data.
    form = form_factory(current_directory)(request.POST)
    if not form.is_valid():
        return form

    message = form.cleaned_data['message']
    languages = form.cleaned_data.get('language_selection', [])
    projects = form.cleaned_data.get('project_selection', [])
    publish_dirs = []
    template_vars['notices_published'] = []

    # Figure out which directories, projects, and languages are involved
    if current_language and current_project:
        # The current translation project
        publish_dirs = [current_directory]
        languages = [current_language]
        projects = [current_project]
    elif current_language:
        languages = [current_language]
        if form.cleaned_data['project_all']:
            # The current language
            publish_dirs = [current_language.directory]
        else:
            # Certain projects in the current language
            translation_projects = TranslationProject.objects.filter(
                    language=current_language, project__in=projects)
            publish_dirs = [tp.directory for tp in translation_projects]
    elif current_project:
        projects = [current_project]
        if form.cleaned_data['language_all']:
            # The current project
            publish_dirs = [current_project.directory]
        else:
            # Certain languages in the current project
            translation_projects = TranslationProject.objects.filter(
                    language__in=languages, project=current_project)
            publish_dirs = [tp.directory for tp in translation_projects]
    else:
        # The form is top-level (server-wide)
        if form.cleaned_data['project_all']:
            if form.cleaned_data['language_all']:
                # Publish at server root
                publish_dirs = [current_directory]
            else:
                # Certain languages
                publish_dirs = [l.directory for l in languages]
        else:
            if form.cleaned_data['language_all']:
                # Certain projects
                publish_dirs = [p.directory for p in projects]
            else:
                # Specific translation projects
                translation_projects = TranslationProject.objects.filter(
                        language__in=languages, project__in=projects)
                publish_dirs = [tp.directory for tp in translation_projects]

    # RSS (notices)
    if form.cleaned_data['publish_rss']:
        for d in publish_dirs:
            new_notice = create_notice(request.user, message, d)
            template_vars['notices_published'].append(new_notice)

    # E-mail
    if form.cleaned_data['send_email']:
        email_header = form.cleaned_data['email_header']

        if languages:
            lang_filter = Q(languages__in=languages)
        else:
            lang_filter = Q(languages__isnull=False)

        if projects:
            proj_filter = Q(projects__in=projects)
        else:
            proj_filter = Q(projects__isnull=False)

        to_list = PootleProfile.objects.filter(lang_filter, proj_filter)
        to_list = to_list.distinct()

        # Take into account 'only active users' flag from the form.
        if form.cleaned_data['restrict_to_active_users']:
            to_list = to_list.exclude(submission=None)
            to_list = to_list.exclude(suggestion=None)
            to_list = to_list.exclude(suggester=None)

        recipients = []
        for person in to_list:
            # Check if the User object here as permissions
            directory = form.cleaned_data['directory']

            if not check_profile_permission(person, 'view', directory):
                continue

            if person.user.email != '':
                recipients.append(person.user.email)

        # Send the email to the recipients, ensuring addresses are hidden
        send_mail(email_header, message, bcc=recipients, fail_silently=True)

    form = form_factory(current_directory)()

    return form


def view_notice_item(request, path, notice_id):
    notice = get_object_or_404(Notice, id=notice_id)
    template_vars = {
            "title": _("View News Item"),
            "notice_message": notice.message,
            }

    return render_to_response('viewnotice.html', template_vars,
                              context_instance=RequestContext(request))
