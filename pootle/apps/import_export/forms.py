# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django import forms


class UploadForm(forms.Form):
    file = forms.FileField(required=True)
    user_id = forms.ChoiceField(
        required=False,
        widget=forms.Select(
            attrs={'class': 'js-select2'}))

    def __init__(self, *args, **kwargs):
        self.uploader_list = kwargs.pop("uploader_list", [])
        super(UploadForm, self).__init__(*args, **kwargs)
        self.fields["file"].widget.attrs["id"] = "js-file-upload-input"
        self.fields["user_id"].choices = self.uploader_list
        self.fields["user_id"].widget.attrs["id"] = "js-user-upload-input"
