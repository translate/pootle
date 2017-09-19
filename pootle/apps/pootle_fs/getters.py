# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.core.exceptions import ValidationError

from pootle.core.delegate import response, state
from pootle.core.plugin import getter
from pootle_config.delegate import (
    config_should_not_be_set, config_should_not_be_appended)
from pootle_project.models import Project

from .delegate import (
    fs_file, fs_finder, fs_matcher, fs_plugins, fs_resources,
    fs_translation_mapping_validator, fs_url_validator)
from .files import FSFile
from .finder import TranslationFileFinder, TranslationMappingValidator
from .localfs import LocalFSPlugin, LocalFSUrlValidator
from .matcher import FSPathMatcher
from .resources import FSProjectResources
from .response import ProjectFSResponse
from .state import ProjectFSState


@getter(state, sender=LocalFSPlugin)
def fs_plugin_state_getter(**kwargs_):
    return ProjectFSState


@getter(response, sender=ProjectFSState)
def fs_plugin_response_getter(**kwargs_):
    return ProjectFSResponse


@getter(fs_file, sender=LocalFSPlugin)
def fs_file_getter(**kwargs_):
    return FSFile


@getter(fs_resources, sender=LocalFSPlugin)
def fs_resources_getter(**kwargs_):
    return FSProjectResources


@getter(fs_finder, sender=LocalFSPlugin)
def fs_finder_getter(**kwargs_):
    return TranslationFileFinder


@getter(fs_matcher, sender=LocalFSPlugin)
def fs_matcher_getter(**kwargs_):
    return FSPathMatcher


@getter(fs_url_validator, sender=LocalFSPlugin)
def fs_url_validator_getter(**kwargs_):
    return LocalFSUrlValidator


@getter(fs_translation_mapping_validator)
def fs_translation_mapping_validator_getter(**kwargs_):
    return TranslationMappingValidator


@getter([config_should_not_be_set, config_should_not_be_appended], sender=Project)
def fs_url_config_validator(**kwargs):
    if kwargs["key"] == "pootle_fs.fs_type":
        plugin_class = fs_plugins.gather(Project).get(kwargs["value"])
        if not plugin_class:
            raise ValidationError("Unrecognised fs_type")
    if kwargs["key"] == "pootle_fs.fs_url":
        fs_type = kwargs["instance"].config.get("pootle_fs.fs_type")
        if not fs_type:
            raise ValidationError("You cannot set fs_url until fs_type is set")
        plugin_class = fs_plugins.gather(Project).get(fs_type)
        if plugin_class:
            validator = fs_url_validator.get(plugin_class)
            if validator:
                validator().validate(kwargs["value"])
    if kwargs["key"] == "pootle_fs.translation_mapping":
        validator = fs_translation_mapping_validator.get()
        for path in kwargs["value"].values():
            validator(path).validate()
