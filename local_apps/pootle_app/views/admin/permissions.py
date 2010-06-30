#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Zuza Software Foundation
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

from django.utils.translation import ugettext as _
from django import forms
from django.contrib.contenttypes.models import ContentType

from pootle_app.models import Directory, PermissionSet

from pootle_app.views.admin import util

class PermissionFormField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, instance):
        return instance.name

def admin_permissions(request, current_directory, template, context):
    content_type = ContentType.objects.get(name='pootle', app_label='pootle_app')
    permission_queryset = content_type.permission_set.exclude(codename__in=['add_directory', 'change_directory', 'delete_directory'])

    context['submitname'] = 'changepermissions'
    context['formid'] = 'permission-manage'

    class PermissionSetForm(forms.ModelForm):
        class Meta:
            model = PermissionSet
            exclude = ['negative_permissions']

        directory = forms.ModelChoiceField(queryset=Directory.objects.filter(pk=current_directory.pk),
                                           initial=current_directory.pk, widget=forms.HiddenInput)
        positive_permissions = PermissionFormField(label=_('Permissions'), queryset=permission_queryset, required=False)
    link = lambda instance: unicode(instance.profile)
    return util.edit(request, template, PermissionSet, context, link, linkfield='profile',
              queryset=current_directory.permission_sets.order_by('profile').all(), can_delete=True,
              form=PermissionSetForm)
