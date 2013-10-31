#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Zuza Software Foundation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# Pootle is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# Pootle; if not, see <http://www.gnu.org/licenses/>.

import re

from django import forms
from django.utils.translation import ugettext as _

from taggit.models import Tag

from .models import Goal, slugify_tag_name


def check_name(name):
    """Perform extra validations and normalizations on tag name.

    * Tag names must be alphanumeric strings that can have (but not begin
      or end with, and don't have two or more consecutive) the following
      characters:

        * space,
        * colon (:),
        * hyphen (-),
        * underscore (_),
        * slash (/) or
        * period (.)

    * Tag names must be case insensitive (displayed as lowercase).
    """
    if name != name.strip(" -_/:."):
        msg = _("Tag names cannot have leading nor trailing spaces, colons "
                "(:), hyphens (-), underscores (_), slashes (/) or "
                "periods (.)!")
        raise forms.ValidationError(msg)

    if name != re.sub(r'\s{2,}|:{2,}|-{2,}|_{2,}|/{2,}|\.{2,}', "-", name):
        msg = _("Tag names cannot contain two or more consecutive: spaces, "
                "colons (:), hyphens (-), underscores (_), slashes (/) or "
                "periods (.)!")
        raise forms.ValidationError(msg)

    #TODO Unicode alphanumerics must be allowed.
    if name != re.sub(r'[^\w _/:.-]', "-", name):
        msg = _("Tag names must be an alphanumeric lowercase string with no "
                "trailing nor leading (but yes on the middle): spaces, colons "
                "(:), hyphens (-), underscores (_), slashes (/) or "
                "periods (.)!")
        raise forms.ValidationError(msg)

    # Lowercase since all tags must be case insensitive.
    return name.lower()


def check_goal_name(name):
    name = name.lstrip("goal:")

    if name != name.lstrip(" -_/:."):
        msg = _("Name cannot contain just after 'goal:' any of these "
                "characters: spaces, colons (:), hyphens (-), underscores "
                "(_), slashes (/) or periods (.)")
        raise forms.ValidationError(msg)


class TagForm(forms.ModelForm):

    class Meta:
        model = Tag
        widgets = {
            'name': forms.TextInput(attrs={
                'id': 'js-tag-form-name',
            }),
            'slug': forms.HiddenInput(attrs={
                'id': 'js-tag-form-slug',
            }),
        }

    def __init__(self, *args, **kwargs):
        super(TagForm, self).__init__(*args, **kwargs)
        self.fields['slug'].label = ''  # Blank label to don't see it.

    def save(self, commit=True):
        # If this form is saving a goal and not a tag, then replace the tag
        # instance with a goal instance using the same values.
        if self.instance.name.startswith("goal:"):
            params = {
                'name': self.instance.name,
                'slug': self.instance.slug,
            }
            self.instance = Goal(**params)

        return super(TagForm, self).save(commit)

    def clean_name(self):
        """Perform extra validations and normalizations on tag name.

        * Tag names must be alphanumeric strings that can have (but not begin
          or end with, and don't have two or more consecutive) the following
          characters:

            * space,
            * colon (:),
            * hyphen (-),
            * underscore (_),
            * slash (/) or
            * period (.)

        * Tag names must be case insensitive (displayed as lowercase).
        * Also if the name corresponds to a goal name it must be checked that
          the name is not used for any existing goal.
        """
        name = check_name(self.cleaned_data['name'])

        if name.startswith("goal:"):
            check_goal_name(name)

            if Goal.objects.filter(name=name):
                msg = _("A goal with that name already exists. Please pick "
                        "another name.")
                raise forms.ValidationError(msg)

        # Always return the cleaned data, whether you have changed it or not.
        return name

    def clean_slug(self):
        """Perform extra validations and normalizations on tag slug.

        * Tag slugs must be equal to the corresponding tag name, but replacing
          with a hyphen (-) the following characters:

            * space,
            * colon (:),
            * underscore (_),
            * slash (/) or
            * period (.)

        * Tag slugs can't have two or more consecutive hyphens, nor start nor
          end with hyphens.
        * Also if the slug corresponds to a goal slug it must be checked that
          the slug is not used for any existing goal.
        """
        # Get the tag name.
        tag_name = self.cleaned_data.get('name', "")

        # If there is no tag name, maybe because it failed to validate.
        if not tag_name:
            # Return any non-empty string to avoid showing an error message for
            # the slug field.
            return "slug"

        # Calculate the slug from the tag name.
        test_slug = slugify_tag_name(tag_name)

        # Get the actual slug provided to the form.
        slug = self.cleaned_data['slug']

        if slug != test_slug:
            msg = _("Tag slugs must be equal to the tag name, but replacing "
                    "with a hyphen the single or multiple occurrences of the "
                    "following characters: spaces, colons (:), hyphens (-), "
                    "underscores (_), slashes (/) or periods (.)!")
            raise forms.ValidationError(msg)

        if slug.startswith("goal-") and Goal.objects.filter(slug=slug):
            raise forms.ValidationError(_("A goal with this slug already "
                                          "exists."))

        # Always return the cleaned data, whether you have changed it or not.
        return slug


class GoalForm(forms.ModelForm):

    class Meta:
        model = Goal

    def __init__(self, *args, **kwargs):
        super(GoalForm, self).__init__(*args, **kwargs)
        help_text = _("Warning: Changing the name also changes the slug, so "
                      "it won't be possible to view this goal on this page!")
        self.fields['name'].help_text = help_text
        self.fields['slug'].widget = forms.HiddenInput()
        self.fields['slug'].label = ''  # Blank label to don't see it.

    def clean_name(self):
        name = check_name(self.cleaned_data['name'])
        check_goal_name(name)
        # Always return the cleaned data, whether you have changed it or not.
        return name

    def clean(self):
        cleaned_data = super(GoalForm, self).clean()
        goal_name = cleaned_data.get("name", "")

        if goal_name:
            # Create a slug from the goal name.
            cleaned_data["slug"] = slugify_tag_name(goal_name)

            # Remove errors for slug field, if any.
            try:
                self.errors.pop("slug")
            except KeyError:
                pass

        # Always return the full collection of cleaned data.
        return cleaned_data
