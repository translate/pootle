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

import sys

from django.core.exceptions import PermissionDenied
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.db.models import Q

from pootle.i18n.gettext import tr_lang

from pootle_app.models import Directory
from pootle_app.models.permissions import get_matching_permissions, check_permission, check_profile_permission
from pootle_app.views.language import navbar_dict
from pootle_language.models import Language
from pootle_notifications.models import Notice, NoticeForm
from pootle_translationproject.models import TranslationProject
from pootle_project.models import Project
from pootle_profile.models import get_profile, PootleProfile
from pootle.settings import DEFAULT_FROM_EMAIL

def view(request, path):
    #FIXME: why do we have leading and trailing slashes in pootle_path?
    pootle_path = '/%s' % path

    directory = get_object_or_404(Directory, pootle_path=pootle_path)

    request.permissions = get_matching_permissions(get_profile(request.user), directory)

    if not check_permission('view', request):
        raise PermissionDenied

    template_vars = {'path': path,
                     'directory': directory}

    # Find language and project defaults, passed to handle_form
    proj = None
    lang = None
    if not directory.is_language() and not directory.is_project():
        try:
            translation_project = directory.get_translationproject()
            lang = translation_project.language
            proj = translation_project.project
        except:
            pass
    else:
        if directory.is_language():
            lang = directory.language
            proj = None
        if directory.is_project():
            lang = None
            proj = directory.project


    if check_permission('administrate', request):
        # Thus, form is only set for the template if the user has 'administrate' permission
        template_vars['form'] = handle_form(request, directory, proj, lang, template_vars)
        template_vars['title'] = directory_to_title(directory)
    else:
        template_vars['form'] = None

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

def directory_to_title(directory):
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


def create_notice(creator, message, directory):
    profile = get_profile(creator)
    if not check_profile_permission(profile, 'administrate', directory):
        raise PermissionDenied
    new_notice = Notice()
    new_notice.message = message
    new_notice.directory = directory
    new_notice.save()
    return new_notice


def handle_form(request, current_directory, current_project, current_language, template_vars):

    current_project_pk = None
    if current_project != None:
        current_project_pk = current_project.pk

    current_language_pk = None
    if current_language != None:
        current_language_pk = current_language.pk

    # Check if the user submitted the form
    if request.method != 'POST':
        # Not a POST method. Return a default starting state of the form
        form = NoticeForm(initial = noticeform_initial_dict(current_directory,\
                current_project_pk, current_language_pk) )
        return form


    # Reconstruct the NoticeForm with the user data.
    form = NoticeForm(request.POST)
    template_vars['notices_published'] = None

    # Basic validation, only proceed if the form data is valid.
    if form.is_valid():
        message = form.cleaned_data['message']

        # Lets save this NoticeForm as a Notice (an RSS item on the website)
        # if it is requsted we do that - ie 'publish_rss' is true.
        if form.cleaned_data['publish_rss'] == True:

            lang_filter = Q()
            # Find the Projects we want to publish this news to.
            if form.cleaned_data['project_all'] == True:
                projs = Project.objects.all()
            else:
                projs = form.cleaned_data['project_selection']

            # Find the Languages we want to publish this news to.
            if form.cleaned_data['language_all'] == True:
                langs = Language.objects.all()
            else:
                langs = form.cleaned_data['language_selection']
            # construct the language OR filter
            for lang in langs:
                lang_filter |= Q(language__exact=lang)

            # We use all the projects that we want to publish this News to.
            # For each project, depending on language selection, publish
            # news into that Directory.
            for p in projs:
                # If the user selected no language, and not "every lang", then
                # just use the project's directory.
                if form.cleaned_data['language_selection'] == [] and \
                        form.cleaned_data['language_all'] == False:
                    # Publish this Notice, using the project's Directory object
                    create_notice(request.user, message, p.directory)

                    if template_vars['notices_published'] == None:
                        template_vars['notices_published'] = []
                    template_vars['notices_published'].append(
                            _("Published to Project %s", p.fullname)
                    )

                else:
                    # Find the languages we want to restrict publishing News to,
                    # for this particular Project. Let's find the
                    # TranslationProject to find the directory object to use.
                    tps = TranslationProject.objects.filter(lang_filter, project__exact=p).distinct()
                    for tp in tps:
                        # Publish this Notice, using the translation project's
                        # Directory object
                        create_notice(request.user, message, tp.directory)

                        if template_vars['notices_published'] == None:
                            template_vars['notices_published'] = []
                        template_vars['notices_published'].append(
                                _("Published to Translation Project %s", tp.fullname)
                        )

            # We use all the languages that we want to publish this News to, and
            # for each lang, publish news into that Directory. We only need to
            # check if the user selected no projects - the case of selected
            # projects and languages is covered above.

            # If the user selected no project, and not "every proj", then just
            # use the languages's directory.
            if form.cleaned_data['project_selection'] == [] and \
                    form.cleaned_data['project_all'] == False:
                for l in langs:
                    # Publish this Notice using the languages's Directory object
                    create_notice(request.user, message, l.directory)

                    if template_vars['notices_published'] == None:
                        template_vars['notices_published'] = []
                    template_vars['notices_published'].append(
                            _("Published to Language %s", l.fullname)
                    )


        # If we want to email it, then do that.
        if form.cleaned_data['send_email'] == True:

            email_header = form.cleaned_data['email_header']
            proj_filter = Q()
            lang_filter = Q()
            # Find users to send email too, based on project
            if form.cleaned_data['project_all'] == True:
                projs = Project.objects.all()
            else:
                projs = form.cleaned_data['project_selection']
            # Construct the project OR filter
            for proj in projs:
                proj_filter |= Q(projects__exact=proj)

            # Find users to send email too, based on language
            if form.cleaned_data['language_all'] == True:
                langs = Language.objects.all()
            else:
                langs = form.cleaned_data['language_selection']
            # construct the language OR filter
            for lang in langs:
                lang_filter |= Q(languages__exact=lang)

            # Generate a list of pootleprofile objects which are linked to
            # Users and their emails.
            to_list = PootleProfile.objects.filter(lang_filter, proj_filter)
            to_list = to_list.distinct()
            # Take into account 'only active users' flag from the form.
            if form.cleaned_data['restrict_to_active_users'] == True:
                to_list = to_list.exclude(submission=None)
                to_list = to_list.exclude(suggestion=None)
                to_list = to_list.exclude(suggester=None)

            to_list_emails = []
            for person in to_list:
                #Check if the User object here as permissions
                directory = form.cleaned_data['directory']
                if not check_profile_permission(person, 'view', directory):
                    continue
                if person.user.email != '':
                    to_list_emails.append(person.user.email)
                    if template_vars['notices_published'] == None:
                        template_vars['notices_published'] = []
                    template_vars['notices_published'].append(
                            _("Sent an email to %s", person.user.email)
                    )

            # The rest of the email settings
            from_email = DEFAULT_FROM_EMAIL
            message = form.cleaned_data['message']

            # Send the email to the list of people
            send_mail(email_header, message, from_email, to_list_emails, fail_silently=True)

    # Finally return a blank Form to allow user to continue publishing notices
    # with our defaults
    form = NoticeForm(initial = noticeform_initial_dict(current_directory,\
            current_project_pk, current_language_pk) )

    return form


def noticeform_initial_dict(current_directory, current_project_pk, current_language_pk):
    return  {
            'publish_rss': True ,
            'directory' : current_directory.pk,
            'project_all': False,
            'language_all': False,
            'project_selection':(current_project_pk,),
            'language_selection':(current_language_pk,),
    }


def view_notice_item(request, path, notice_id):
    notice = get_object_or_404(Notice, id=notice_id)
    template_vars = {
            "title": _("View News Item"),
            "notice_message": notice.message,
            }

    return render_to_response('viewnotice.html', template_vars,
                              context_instance=RequestContext(request))
