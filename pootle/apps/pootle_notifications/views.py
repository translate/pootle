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

from django import forms
from django.contrib.formtools.preview import FormPreview
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext as _

from pootle.i18n.gettext import tr_lang
from pootle_app.models import Directory
from pootle_app.models.permissions import (get_matching_permissions,
                                           check_permission,
                                           check_profile_permission)
from pootle_misc.mail import send_mail
from pootle_notifications.forms import form_factory
from pootle_notifications.models import Notice
from pootle_profile.models import get_profile, PootleProfile
from pootle_translationproject.models import TranslationProject


class NoticeFormPreview(FormPreview):
    form_template = 'notices.html'
    preview_template = 'notices_preview.html'

    def __init__(self, form=forms.Form):
        # Since when instantiating this class in urls.py it is impossible to
        # provide the appropiate Form class because it is created in a form
        # factory using data extracted (the directory) from the URL from which
        # it is called. Thus it is necessary to perform black magic and
        # overwrite the __init__ method in order to provide a dummy Form just
        # for allowing instantiating this class. Once instantiated, that dummy
        # form class is overriden in the parse_params() method with the right
        # Form class created using the form factory .
        super(NoticeFormPreview, self).__init__(form)

    def get_auto_id(self):
        """Hook to override the ``auto_id`` kwarg for the form. Needed when
        rendering two form previews in the same template.
        """
        return "id_%s"

    def parse_params(self, *args, **kwargs):
        """Handle captured args/kwargs from the URLconf"""
        self.path = kwargs["path"]
        #FIXME: why do we have leading and trailing slashes in pootle_path?
        pootle_path = '/%s' % self.path
        self.directory = get_object_or_404(Directory, pootle_path=pootle_path)

        # Get language and project defaults.
        if not self.directory.is_language() and not self.directory.is_project():
            self.language = self.directory.translation_project.language
            self.project = self.directory.translation_project.project
        elif self.directory.is_language():
            self.language = self.directory.language
        elif self.directory.is_project():
            self.project = self.directory.project

        # Set the correct form class after the fact, because the form class set
        # in the __init__ method is just an empty form class. Explanation on
        # __init__ docstring.
        self.form = form_factory(self.directory)

    def get_context(self, request, form):
        """Provide context for template rendering. This is called when
        displaying the initial page and when displaying the preview page.
        """
        # Set permissions on request in order to allow checking them later.
        request.permissions = get_matching_permissions(
            get_profile(request.user), self.directory
        )
        # If the user doesn't have permission to see the form then don't add it
        # to the context, or in other words, don't use context returned by the
        # get_context() method.
        if check_permission('administrate', request):
            context = super(NoticeFormPreview, self).get_context(request, form)
        else:
            context = {}

        # Add extra fields to context.
        if request.GET.get('all', False):
            criteria = {
                'directory__pootle_path__startswith': \
                    self.directory.pootle_path,
            }
        else:
            criteria = {
                'directory': self.directory,
            }

        context.update({
            'path': self.path,
            'directory': self.directory,
            'title': directory_to_title(self.directory),
            'notices': Notice.objects.filter(**criteria) \
                                     .select_related('directory')[:30],
        })

        # FIXME remove this if clause when these variables are not needed
        # anymore for the breadcrumbs or tp_menu.html.
        if not self.directory.is_language() and not self.directory.is_project():
            context.update({
                'language': self.language,
                'project': self.project,
            })

        return context

    def process_preview(self, request, form, context):
        """Given a validated form, performs any extra processing before
        displaying the preview page, and saves any extra data in context.
        """
        context['preview_message'] = form.cleaned_data['message']

    def _get_recipients(self, restrict_to_active_users, directory):
        """Retrieve the list of recipients to whom will be sent the email."""
        to_list = PootleProfile.objects.all()

        # Take into account 'only active users' flag from the form.
        if restrict_to_active_users:
            to_list = to_list.exclude(submission=None) \
                             .exclude(suggestion=None).exclude(suggester=None)
        recipients = []
        for person in to_list:
            # Check if the User profile has permissions in the directory.
            if not check_profile_permission(person, 'view', directory):
                continue
            if person.user.email:
                recipients.append(person.user.email)
        return recipients

    def _create_notice(self, creator, message, directory):
        """Create the news item."""
        profile = get_profile(creator)
        if not check_profile_permission(profile, 'administrate', directory):
            raise PermissionDenied
        new_notice = Notice(directory=directory, message=message)
        new_notice.save()
        return new_notice

    def done(self, request, cleaned_data):
        """If the form was valid, performs any extra processing after
        displaying the preview page.
        """
        # Get fresh context for response.
        f = self.form(auto_id=self.get_auto_id(),
                      initial=self.get_initial(request))
        context = self.get_context(request, f)

        # Process the form.
        context['notices_published'] = []
        publish_dirs = []
        message = cleaned_data['message']
        languages = cleaned_data.get('language_selection', [])
        projects = cleaned_data.get('project_selection', [])

        # Figure out which directories, projects, and languages are involved.
        if not self.directory.is_language() and not self.directory.is_project():
            # The current translation project.
            publish_dirs = [self.directory]
            languages = [self.language]
            projects = [self.project]
        elif self.directory.is_language():
            languages = [self.language]
            if cleaned_data['project_all']:
                # The current language.
                publish_dirs = [self.language.directory]
            else:
                # Certain projects in the current language.
                translation_projects = TranslationProject.objects.filter(
                        language=self.language, project__in=projects)
                publish_dirs = [tp.directory for tp in translation_projects]
        elif self.directory.is_project():
            projects = [self.project]
            if cleaned_data['language_all']:
                # The current project.
                publish_dirs = [self.project.directory]
            else:
                # Certain languages in the current project.
                translation_projects = TranslationProject.objects.filter(
                        language__in=languages, project=self.project)
                publish_dirs = [tp.directory for tp in translation_projects]
        else:
            # The form is top-level (server-wide)
            if cleaned_data['project_all']:
                if cleaned_data['language_all']:
                    # Publish at server root
                    publish_dirs = [self.directory]
                else:
                    # Certain languages
                    publish_dirs = [l.directory for l in languages]
            else:
                if cleaned_data['language_all']:
                    # Certain projects
                    publish_dirs = [p.directory for p in projects]
                else:
                    # Specific translation projects
                    translation_projects = TranslationProject.objects.filter(
                            language__in=languages, project__in=projects)
                    publish_dirs = [tp.directory for tp in translation_projects]

        # RSS (notices).
        if cleaned_data['publish_rss']:
            for d in publish_dirs:
                new_notice = self._create_notice(request.user, message, d)
                context['notices_published'].append(new_notice)

        # E-mail.
        if cleaned_data['send_email']:
            email_header = cleaned_data['email_header']
            recipients = self._get_recipients(
                cleaned_data['restrict_to_active_users'],
                cleaned_data['directory']
            )
            # Send the email to the recipients, ensuring addresses are hidden.
            send_mail(email_header, message, bcc=recipients,
                      fail_silently=True, html_message=True)

        return render_to_response(self.form_template, context,
                                  context_instance=RequestContext(request))


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


def view_notice_item(request, path, notice_id):
    notice = get_object_or_404(Notice, id=notice_id)
    template_vars = {
        "title": _("View News Item"),
        "notice_message": notice.message,
    }
    return render_to_response('viewnotice.html', template_vars,
                              context_instance=RequestContext(request))
