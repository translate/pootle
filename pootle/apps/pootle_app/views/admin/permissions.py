# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django import forms
from django.contrib.auth import get_user_model

from pootle.i18n.gettext import ugettext as _
from pootle_app.models import Directory
from pootle_app.models.permissions import (PermissionSet,
                                           get_permission_contenttype)
from pootle_app.views.admin import util
from pootle_misc.forms import GroupedModelChoiceField


User = get_user_model()

PERMISSIONS = {
    'positive': [
        'view', 'suggest', 'translate', 'review',
        'administrate', 'create_project'
    ],
    'negative': ['hide'],
}


class PermissionFormField(forms.ModelMultipleChoiceField):

    def label_from_instance(self, instance):
        return _(instance.name)


def admin_permissions(request, current_directory, template, ctx):
    language = ctx.get('language', None)

    negative_permissions_excl = list(PERMISSIONS['negative'])
    positive_permissions_excl = list(PERMISSIONS['positive'])

    # Don't provide means to alter access permissions under /<lang_code>/*
    # In other words: only allow setting access permissions for the root
    # and the `/projects/<code>/` directories
    if language is not None:
        access_permissions = ['view', 'hide']
        negative_permissions_excl.extend(access_permissions)
        positive_permissions_excl.extend(access_permissions)

    content_type = get_permission_contenttype()

    positive_permissions_qs = content_type.permission_set.exclude(
        codename__in=negative_permissions_excl,
    )
    negative_permissions_qs = content_type.permission_set.exclude(
        codename__in=positive_permissions_excl,
    )

    base_queryset = User.objects.filter(is_active=1).exclude(
        id__in=current_directory.permission_sets.values_list('user_id',
                                                             flat=True),)
    choice_groups = [(None, base_queryset.filter(
        username__in=('nobody', 'default')
    ))]

    choice_groups.append((
        _('All Users'),
        base_queryset.exclude(username__in=('nobody',
                                            'default')).order_by('username'),
    ))

    class PermissionSetForm(forms.ModelForm):

        class Meta(object):
            model = PermissionSet
            fields = ('user', 'directory', 'positive_permissions',
                      'negative_permissions')

        directory = forms.ModelChoiceField(
            queryset=Directory.objects.filter(pk=current_directory.pk),
            initial=current_directory.pk,
            widget=forms.HiddenInput,
        )
        user = GroupedModelChoiceField(
            label=_('Username'),
            choice_groups=choice_groups,
            queryset=User.objects.all(),
            required=True,
            widget=forms.Select(attrs={
                'class': 'js-select2 select2-username',
            }),
        )
        positive_permissions = PermissionFormField(
            label=_('Add Permissions'),
            queryset=positive_permissions_qs,
            required=False,
            widget=forms.SelectMultiple(attrs={
                'class': 'js-select2 select2-multiple',
                'data-placeholder': _('Select one or more permissions'),
            }),
        )
        negative_permissions = PermissionFormField(
            label=_('Revoke Permissions'),
            queryset=negative_permissions_qs,
            required=False,
            widget=forms.SelectMultiple(attrs={
                'class': 'js-select2 select2-multiple',
                'data-placeholder': _('Select one or more permissions'),
            }),
        )

        def __init__(self, *args, **kwargs):
            super(PermissionSetForm, self).__init__(*args, **kwargs)

            # Don't display extra negative permissions field where they
            # are not applicable
            if language is not None:
                del self.fields['negative_permissions']

    link = lambda instance: unicode(instance.user)
    directory_permissions = current_directory.permission_sets \
                                             .order_by('user').all()

    return util.edit(request, template, PermissionSet, ctx, link,
                     linkfield='user', queryset=directory_permissions,
                     can_delete=True, form=PermissionSetForm)
