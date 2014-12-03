#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2014 Zuza Software Foundation
# Copyright 2013 Evernote Corporation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Pootle is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Pootle; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext as _

from pootle_app.models import Directory
from pootle_app.models.permissions import (get_permission_contenttype,
                                           PermissionSet)
from pootle_app.views.admin import util
from pootle_misc.forms import GroupedModelChoiceField
from pootle_statistics.models import Submission


User = get_user_model()


class PermissionFormField(forms.ModelMultipleChoiceField):

    def label_from_instance(self, instance):
        return _(instance.name)


def admin_permissions(request, current_directory, template, context):
    User = get_user_model()
    project = context.get('project', None)
    language = context.get('language', None)

    # FIXME: Shouldn't we just remove unused permissions from the DB?
    excluded_permissions = [
        'add_directory', 'change_directory', 'delete_directory',
    ]
    # Don't provide means to add `view` permissions under /<lang_code>/*
    # In other words: only allow setting `view` permissions for the root
    # and the `/projects/<code>/` directories
    if language is not None:
        excluded_permissions.append('view')

    content_type = get_permission_contenttype()
    permission_queryset = content_type.permission_set.exclude(
        codename__in=excluded_permissions,
    )

    base_queryset = User.objects.filter(is_active=True).exclude(
        id__in=current_directory.permission_sets.values_list('user_id', flat=True)
    )
    querysets = [(None, base_queryset.filter(
        username__in=('nobody', 'default')
    ))]

    if project is not None:
        if language is not None:
            group_label = _('Translation Project Contributors')
            tp_path = '/%s/%s/' % (language.code, project.code)
            contributions = Submission.objects.filter(
                    translation_project__pootle_path=tp_path,
                )
        else:
            group_label = _('Project Contributors')
            contributions = Submission.objects.filter(
                    translation_project__project__code=project.code,
                )

        querysets.append((
            group_label,
            base_queryset.filter(submission__in=contributions)
                         .distinct()
                         .order_by('username'),
        ))

    if language is not None:
        contributions = Submission.objects.filter(
                translation_project__language__code=language.code,
            )
        querysets.append((
            _('Language Contributors'),
            base_queryset.filter(submission__in=contributions)
                         .distinct()
                         .order_by('username'),
        ))

    querysets.append((
        _('All Users'),
        base_queryset.exclude(username__in=('nobody', 'default'))
                     .order_by('username'),
    ))


    class PermissionSetForm(forms.ModelForm):

        class Meta:
            model = PermissionSet

        directory = forms.ModelChoiceField(
                queryset=Directory.objects.filter(pk=current_directory.pk),
                initial=current_directory.pk,
                widget=forms.HiddenInput,
        )
        user = GroupedModelChoiceField(
                label=_('Username'),
                querysets=querysets,
                queryset=User.objects.all(),
                required=True,
                widget=forms.Select(attrs={
                    'class': 'js-select2 select2-username',
                }),
        )
        positive_permissions = PermissionFormField(
                label=_('Permissions'),
                queryset=permission_queryset,
                required=False,
                widget=forms.SelectMultiple(attrs={
                    'class': 'js-select2 select2-multiple',
                    'data-placeholder': _('Select one or more permissions'),
                }),
        )

    link = lambda instance: unicode(instance.user)
    queryset = current_directory.permission_sets.order_by('user').all()

    return util.edit(request, template, PermissionSet, context, link,
                     linkfield='user', queryset=queryset,
                     can_delete=True, form=PermissionSetForm)
