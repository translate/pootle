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
        """
        name = self.cleaned_data['name']

        if name != name.strip(" -_/:."):
            raise forms.ValidationError(_("Tag names cannot have leading or "
                                          "trailing spaces, colons (:), "
                                          "hyphens (-), underscores (_), "
                                          "slashes (/) or periods (.)!"))

        if name != re.sub(r'\s{2,}|:{2,}|-{2,}|_{2,}|/{2,}|\.{2,}', "-", name):
            raise forms.ValidationError(_("Tag names cannot contain two or "
                                          "more consecutive: spaces, colons "
                                          "(:), hyphens (-), underscores (_), "
                                          "slashes (/) or periods (.)!"))

        #TODO Unicode alphanumerics must be allowed.
        if name != re.sub(r'[^\w _/:.-]', "-", name):
            raise forms.ValidationError(_("Tag names must be an alphanumeric "
                                          "lowercase string with no trailing "
                                          "nor leading (but yes on the "
                                          "middle): spaces, colons (:), "
                                          "hyphens (-), underscores (_), "
                                          "slashes (/) or periods (.)!"))

        # Lowercase since all tags must be case insensitive.
        name = name.lower()

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

          Also tag slugs can't have two or more consecutive hyphens, nor start
          nor end with hyphens.
        """
        # Get the tag name.
        tag_name = self.cleaned_data.get('name', "").lower()

        # If there is no tag name, maybe because it failed to validate.
        if not tag_name:
            # Return any non-empty string to avoid showing an error message for
            # the slug field.
            return "slug"

        # Replace invalid characters for slug with hyphens.
        test_slug = re.sub(r'[^a-z0-9-]', "-", tag_name)

        # Replace groups of hyphens with a single hyphen.
        test_slug = re.sub(r'-{2,}', "-", test_slug)

        # Remove leading and trailing hyphens.
        test_slug = test_slug.strip("-")

        # Get the actual slug provided to the form.
        slug = self.cleaned_data['slug']

        if slug != test_slug:
            msg = _("Tag slugs must be equal to the tag name, but replacing "
                    "with a hyphen the single or multiple occurrences of the "
                    "following characters: spaces, colons (:), hyphens (-), "
                    "underscores (_), slashes (/) or periods (.)!")
            raise forms.ValidationError(msg)

        # Always return the cleaned data, whether you have changed it or not.
        return slug
