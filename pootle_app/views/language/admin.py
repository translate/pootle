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

from django import forms
from django.forms.formsets import formset_factory, BaseFormSet
from django.utils.translation import ugettext as _

from pootle_app.views.util  import render_to_kid, KidRequestContext
from pootle_app.models.profile import PootleProfile
from pootle_app.models.permissions import get_pootle_permissions, PermissionSet, \
    get_matching_permissions
from pootle_app import project_tree

class PermissionSetForm(forms.Form):
    """A PermissionSetForm represents a PermissionSet to the user.

    This form will be used in a formset, PermissionSetFormSet. This
    explains some of the more perculiar code in here.

    In t"""
    id          = forms.IntegerField(required=False, widget=forms.HiddenInput)
    profiles    = forms.ChoiceField(required=False)
    permissions = forms.MultipleChoiceField(required=False, widget=forms.SelectMultiple)
    delete      = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super(PermissionSetForm, self).__init__(*args, **kwargs)

        # 
        permission_choices = [(codename, permission.name) for codename, permission in get_pootle_permissions().iteritems()]
        # Used to render the correct choices
        self['permissions'].field.widget.choices = permission_choices
        # Used during validation to ensure that valid choices were selected
        self['permissions'].field.choices = permission_choices

        profile_choices = self.initial['profile_data']
        # Used to render the correct choices
        self['profiles'].field.widget.choices = profile_choices
        # Used during validation to ensure that valid choices were selected
        self['profiles'].field.choices = profile_choices
        # Remove 'profile_data' lest we have to deal with weird an
        # unexpected complaints from Django's data validation
        # machinery.
        del self.initial['profile_data']

    def as_table(self):
        params = {'id':          self['id'].as_widget(),
                  'permissions': self['permissions'].as_widget()}

        if not self.is_new_user():
            params.update({
                'username': self.initial['username'],
                'profiles': self['profiles'].as_hidden(),
                'delete':   self['delete'].as_widget()})
        else:
            params.update({
                'delete':   self['delete'].as_hidden(),})
            if 'new' in self.initial:
                params.update({ 'username': '',
                                'profiles': self['profiles'].as_widget() })
            else:
                params.update({ 'username': self.initial['username'],
                                'profiles': self['profiles'].as_hidden() })

        return '<tr><td>%(id)s%(username)s%(profiles)s</td><td>%(permissions)s</td><td>%(delete)s</td></tr>' % params

    def is_new_user(self):
        return self.initial['id'] is None

    #def clean(self):
    #    if self.is_new_user() and len(self.changed_data) > 0:
    #        return self['profiles'] != u'None'
    #    else:
    #        return True

class BasePermissionSetFormSet(BaseFormSet):
    def as_table(self):
        return "<tr><th>%s</th><th>%s</th><th>%s</th></tr>%s" % (
            _("Username"), _("Permissions"), _("Delete"),
            super(BasePermissionSetFormSet, self).as_table())

# See the comments in PermissionSetForm We don't want the
# formset_factory to create empty extra forms.  If extra > 0, then the
# associated forms will not receive any initial data (i.e. the data
# passed by the 'initial' parameter when creating a formset; for
# example,
# PermissionSetFormSet(initial=get_permission_data(translation_project))).
# This is problematic for us, since we need to pass the choices to be
# used in the dropdown boxes and selection boxes to the forms. The way
# that I chose to do this was to pass the choice data in via the
# initial parameter. This is then used in PermissionSetForm.__init__
# to set the choices of the choice widgets. In other words, we want
# extra==0, so that we can pass data to each form in the formset.
PermissionSetFormSet = formset_factory(PermissionSetForm, BasePermissionSetFormSet, extra=0)

def get_id(permission_set, profile_dict):
    if permission_set.profile in profile_dict:
        return permission_set.id
    else:
        return None

def get_permission_data(directory):
    # Get all the PermissionSet objects associated with the current directory
    permission_sets = PermissionSet.objects.filter(directory=directory)
    profile_permission_sets = dict((permission_set.profile, permission_set)
                                   for permission_set in permission_sets)

    # Get all profile objects which do not have PermissionSet objects
    # in the current 'translation_project' pointing to them.
    profiles_without_permissions = [profile for profile in PootleProfile.objects.all()
                                    if profile not in profile_permission_sets]

    # Build a list of initial data to be fed to a formset. Each entry
    # here corresponds to an actual PermissionSet. Thus, we set 'id'
    # to that of the PermissionSet in question. 'permissions' is a
    # list of Permission codenames which have been enabled for this
    # PermissionSet.
    #
    # profiles and profile_data are used to display a dropdown list of
    # users without PermissionSet objects for the current
    # 'translation_project'. Thus, they are used in the form which
    # creates PermissionSet objects for new users. So we don't care
    # about them for forms corresponding to existing PermissionSet
    # objects. We include them so that Django's validation machinery
    # won't complain that their values changed (this can quite
    # possibly be removed without having Django complain, but that's
    # for someone else to try).
    permission_data = [{'id':           get_id(permission_set, profile_permission_sets),
                        'permissions':  [permission.codename for permission in permission_set.positive_permissions.all()],
                        'username':     permission_set.profile.user.username,
                        'profiles':     permission_set.profile.id,
                        'profile_data': [(permission_set.profile.id, permission_set.profile.user.username)]}
                       for permission_set in permission_sets]

    # If there are any profiles which do not have PermissionSet
    # objects associated with the current 'translation_project', then
    # we want to display a form to make it possible to add them...
    if len(profiles_without_permissions) > 0:
        # Get the profile object for the user 'default'
        default_profile = PootleProfile.objects.get(user__username='default')
        default_permissions = get_matching_permissions(default_profile, directory)
        # The form to add a new profile doesn't yet correspond to a
        # PermissionSet object. Thus, 'id' can't have a valid
        # PermissionSet id value.
        # 
        # The selected 'permissions' should match the list of default
        # permissions
        permission_data.append({'id':           None,
                                'permissions':  [permission for permission in default_permissions],
                                'username':     '',
                                'profiles':     u'None',
                                'profile_data': [(u'None', '')] + [(profile.id, profile.user.username)
                                                                   for profile in profiles_without_permissions],
                                'new':          True})
    return permission_data

def process_update(request, directory):
    def find_updated_forms(formset):
        deleted_forms = []
        changed_forms = []
        for form in formset.forms:
            # If the user toggled the 'delete' checkbox, we'll roast
            # the corresponding PermissionSet
            if form['delete'].data:
                deleted_forms.append(form)
            # Otherwise, if the form contains any changed data, we'll
            # have to update and save it.
            elif len(form.changed_data) > 0:
                changed_forms.append(form)
        return deleted_forms, changed_forms

    def get_permission_set(form):
        if form.is_new_user():
            permission_set = PermissionSet(profile_id=int(form['profiles'].data), directory=directory)
            permission_set.save()
            return permission_set
        else:
            return PermissionSet.objects.get(pk=form['id'].data)

    if request.method == 'POST':
        permission_set_formset = PermissionSetFormSet(data=request.POST, initial=get_permission_data(directory))
        pootle_permissions = get_pootle_permissions()

        # Check whether there are any validation errors in the form
        # that the user submitted...
        if permission_set_formset.is_valid():
            deleted_forms, changed_forms = find_updated_forms(permission_set_formset)

            for form in deleted_forms:
                get_permission_set(form).delete()

            for form in changed_forms:
                permission_set = get_permission_set(form)
                # pootle_permissions is a (permission codename ->
                # PermissionSet) dict. We get the permission codenames
                # from form['permissions'].data.
                
                permission_set.positive_permissions = [pootle_permissions[codename] for codename in form['permissions'].data]
                permission_set.save()

            return PermissionSetFormSet(initial=get_permission_data(directory))
        else:
            # If the form validation failed, we'll return the old
            # form, which will automatically print validation errors
            # to the user when it's output again.
            return permission_set_formset
    else:
        return PermissionSetFormSet(initial=get_permission_data(directory))

def process_translation_project_update(request, translation_project):
    if 'scan_files' in request.GET:
        project_tree.scan_translation_project_files(translation_project)

def view(request, translation_project):
    language               = translation_project.language
    project                = translation_project.project
    process_translation_project_update(request, translation_project)
    permission_set_formset = process_update(request, translation_project.directory)
    if translation_project.file_style == "gnu":
        filestyle_text = _("This is a GNU-style project (one directory, files named per language).")
    else:
        filestyle_text = _("This is a standard style project (one directory per language).")
    template_vars = {
        "pagetitle":              _("Pootle Admin: %s %s", (language.fullname, project.fullname)),
        "norights_text":          _("You do not have the rights to administer this project."),
        "project":                project,
        "language":               language,
        "main_link":              _("Project home page"),
        "rescan_files_link":      _("Rescan project files"),
        "filestyle_text":         filestyle_text,
        "permissions_title":      _("User Permissions"),
        "username_title":         _("Username"),
        "rights_title":           _("Rights"),
        "permission_set_formset": permission_set_formset,
        "updaterights_text":      _("Update Rights"),
        "adduser_text":           _("(select to add user)")
    }
    return render_to_kid("language/projectlangadmin.html", KidRequestContext(request, template_vars))
