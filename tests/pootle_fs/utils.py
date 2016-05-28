#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle.core.exceptions import MissingPluginError, NotConfiguredError
from pootle.core.plugin import provider
from pootle_fs.delegate import fs_plugins
from pootle_fs.utils import FSPlugin
from pootle_project.models import Project


class DummyFSPlugin(object):

    def __str__(self):
        return (
            "<%s(%s)>"
            % (self.__class__.__name__, self.project))

    def __init__(self, project):
        self.project = project

    @property
    def plugin_property(self):
        return "Plugin property"

    def plugin_method(self, foo):
        return "Plugin method called with: %s" % foo


@pytest.mark.django_db
def test_project_fs_instance():

    @provider(fs_plugins, sender=Project)
    def provide_fs_plugin(**kwargs):
        return dict(dummyfs=DummyFSPlugin)

    project = Project.objects.get(code="project0")
    project.config["pootle_fs.fs_type"] = "dummyfs"
    project.config["pootle_fs.fs_url"] = "/foo/bar"
    plugin = FSPlugin(project)
    assert str(plugin) == "<DummyFSPlugin(Project 0)>"
    assert plugin.project == project
    assert plugin.plugin_property == "Plugin property"
    assert plugin.plugin_method("bar") == "Plugin method called with: bar"
    assert plugin == FSPlugin(project)


@pytest.mark.django_db
def test_project_fs_instance_bad():

    # needs a Project
    with pytest.raises(TypeError):
        FSPlugin()
    project = Project.objects.get(code="project0")
    # project is not configured
    with pytest.raises(NotConfiguredError):
        FSPlugin(project)
    project.config["pootle_fs.fs_type"] = "foo"
    with pytest.raises(NotConfiguredError):
        FSPlugin(project)
    project.config["pootle_fs.fs_type"] = None
    project.config["pootle_fs.fs_url"] = "bar"
    with pytest.raises(NotConfiguredError):
        FSPlugin(project)
    project.config["pootle_fs.fs_type"] = "foo"
    with pytest.raises(MissingPluginError):
        FSPlugin(project)

    @provider(fs_plugins, sender=Project)
    def provide_fs_plugin(**kwargs):
        return dict(dummyfs=DummyFSPlugin)

    with pytest.raises(MissingPluginError):
        FSPlugin(project)
