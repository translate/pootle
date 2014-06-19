#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2014 Zuza Software Foundation
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

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.template import RequestContext
from django.utils.translation import ugettext as _

from pootle.core.decorators import get_path_obj
from pootle.i18n.gettext import tr_lang
from pootle_app.models import Directory
from pootle_app.models.permissions import (check_permission,
                                           check_user_permission,
                                           get_matching_permissions)
from pootle_misc.mail import send_mail
from pootle_notifications.forms import form_factory
from pootle_notifications.models import Notice
from pootle_translationproject.models import TranslationProject


@get_path_obj
def view(request, path_obj):
    directory = path_obj.directory

    # Find language and project defaults, passed to handle_form.
    proj = None
    lang = None
    if directory.is_translationproject():
        trans_proj = path_obj
        lang = path_obj.language
        proj = path_obj.project
    elif directory.is_language():
        lang = path_obj
    elif directory.is_project():
        proj = path_obj
    else:
        # Notices lists are only shown for languages, projects or TPs.
        raise Http404

    # Set permissions on request in order to allow check them later using
    # different functions.
    request.permissions = get_matching_permissions(request.user, directory)

    if request.GET.get('all', False):
        criteria = {
            'directory__pootle_path__startswith': directory.pootle_path,
        }
    else:
        criteria = {
            'directory': directory,
        }

    ctx = {
        'page': 'news',

        'notification_url': reverse('pootle-notifications-feed',
                                    args=[path_obj.pootle_path[:1]]),
        'directory': directory,
        'title': directory_to_title(directory),
        'notices': Notice.objects.filter(**criteria) \
                                 .select_related('directory')[:30],
        'language': lang,
        'project': proj,
    }

    if check_permission('administrate', request):
        ctx['form'] = handle_form(request, directory, proj, lang, ctx)

    return render(request, "notifications/notices.html", ctx)


def directory_to_title(directory):
    """Figures out if directory refers to a Language or TranslationProject and
    returns appropriate string for use in titles.
    """
    if directory.is_language():
        trans_vars = {
            'language': tr_lang(directory.language.fullname),
        }
        return _('News for %(language)s', trans_vars)
    elif directory.is_project():
        trans_vars = {
            'project': directory.project.fullname,
        }
        return _('News for %(project)s', trans_vars)
    elif directory.is_translationproject():
        trans_vars = {
            'language': tr_lang(directory.translationproject.language.fullname),
            'project': directory.translationproject.project.fullname,
        }
        return _('News for the %(project)s project in %(language)s', trans_vars)
    return _('News for %(path)s', {'path': directory.pootle_path})


def create_notice(creator, message, directory):
    if not check_user_permission(creator, "administrate", directory):
        raise PermissionDenied
    new_notice = Notice(directory=directory, message=message)
    new_notice.save()
    return new_notice


def get_recipients(restrict_to_active_users, directory):
    User = get_user_model()
    to_list = User.objects.all()

    # Take into account 'only active users' flag from the form.
    if restrict_to_active_users:
        to_list = to_list.exclude(submission=None).exclude(suggestions=None)

    recipients = []
    for user in to_list:
        # Check if the User has permissions in the directory.
        if not check_user_permission(user, "view", directory, check_default=False):
            continue

        if user.email:
            recipients.append(user.email)

    return recipients


def handle_form(request, current_directory, current_project, current_language,
                ctx):
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
    ctx['notices_published'] = []

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
            ctx['notices_published'].append(new_notice)

    # E-mail
    if form.cleaned_data['send_email']:
        email_header = form.cleaned_data['email_header']
        recipients = get_recipients(
            form.cleaned_data['restrict_to_active_users'],
            form.cleaned_data['directory']
        )
        # Send the email to the recipients, ensuring addresses are hidden
        send_mail(email_header, message, bcc=recipients, fail_silently=True)

    form = form_factory(current_directory)()

    return form


def view_notice_item(request, path, notice_id):
    notice = get_object_or_404(Notice, id=notice_id)
    ctx = {
        "title": _("View News Item"),
        "notice_message": notice.message,
    }
    return render(request, "notifications/view_notice.html", ctx)
