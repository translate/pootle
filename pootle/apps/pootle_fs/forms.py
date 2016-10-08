# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django import forms
from django.utils.functional import cached_property

from pootle.i18n.gettext import ugettext_lazy as _

from .delegate import (
    fs_plugins, fs_translation_path_validator, fs_url_validator)


class ProjectFSAdminForm(forms.Form):
    fs_type = forms.ChoiceField(
        label=_("Filesystem backend"),
        help_text=_("Select a backend filesystem"),
        choices=())
    fs_url = forms.CharField(
        label=_("Backend URL or path"),
        help_text=_(
            "The URL or path to your translation files"))
    translation_path = forms.CharField(
        help_text=_(
            "The translation path mapping for your filesystem"))

    @property
    def fs_type_choices(self):
        return (
            (plugin_type, plugin.name or plugin.fs_type)
            for plugin_type, plugin
            in fs_plugins.gather().items())

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop("project")
        super(ProjectFSAdminForm, self).__init__(*args, **kwargs)
        self.fields["fs_type"].choices = self.fs_type_choices

        self.fields["fs_url"].initial = self.project.config.get("pootle_fs.fs_url")
        self.fields["fs_type"].initial = (
            self.project.config.get("pootle_fs.fs_type"))
        translation_path = (
            self.project.config.get("pootle_fs.translation_paths"))
        if translation_path:
            self.fields["translation_path"].initial = (
                translation_path.get("default"))

    @property
    def fs_path_validator(self):
        return fs_translation_path_validator.get()

    @cached_property
    def fs_plugin(self):
        if self.cleaned_data.get("fs_type"):
            return fs_plugins.gather()[self.cleaned_data["fs_type"]]

    @cached_property
    def fs_url_validator(self):
        validator = fs_url_validator.get(self.fs_plugin)
        return validator and validator()

    def clean(self):
        if not hasattr(self, "cleaned_data") or not self.cleaned_data:
            return
        if self.cleaned_data.get("translation_path"):
            try:
                self.fs_path_validator(
                    self.cleaned_data["translation_path"]).validate()
            except ValueError as e:
                self.add_error("translation_path", e.message)
        if not self.fs_url_validator or not self.cleaned_data.get("fs_url"):
            return
        try:
            self.fs_url_validator.validate(self.cleaned_data["fs_url"])
        except forms.ValidationError as e:
            self.add_error(
                "fs_url",
                forms.ValidationError(
                    "Incorrect URL or path ('%s') for plugin type '%s': %s"
                    % (self.cleaned_data.get("fs_url"),
                       self.cleaned_data.get("fs_type"),
                       e.message)))

    def save(self):
        self.project.config["pootle_fs.fs_type"] = self.cleaned_data["fs_type"]
        self.project.config["pootle_fs.fs_url"] = self.cleaned_data["fs_url"]
        self.project.config["pootle_fs.translation_paths"] = dict(
            default=self.cleaned_data["translation_path"])
