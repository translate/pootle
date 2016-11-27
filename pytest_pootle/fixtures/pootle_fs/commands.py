# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.utils.functional import cached_property
from django.utils.lru_cache import lru_cache


DUMMY_RESPONSE_MAP = dict(
    add="added_from_pootle",
    resolve="staged_for_merge_fs",
    rm="remove",
    sync="merged_from_pootle")


def add_dummy_api_call(response, call_type, **kwargs):
    from pootle_fs.state import FSItemState

    call_type = DUMMY_RESPONSE_MAP[call_type]
    for k, v in sorted(kwargs.items()):
        response.add(
            "%s_args" % call_type,
            fs_state=FSItemState(
                state=response.context,
                state_type="%s_args" % call_type,
                pootle_path=k,
                fs_path=v))


@lru_cache()
def _get_dummy_api_plugin():
    from pootle.core.state import State
    from pootle_fs.plugin import Plugin
    from pootle_fs.response import ProjectFSResponse

    class DummyResponse(ProjectFSResponse):
        made_changes = True

        response_types = [
            "remove", "remove_args",
            "added_from_fs", "added_from_fs_args",
            "added_from_pootle", "added_from_pootle_args", "staged_for_merge_fs",
            "staged_for_merge_pootle", "staged_for_merge_pootle_args",
            "merged_from_pootle", "merged_from_pootle_args"]

    class DummyCommandPlugin(Plugin):

        @cached_property
        def dummy_response(self):
            return DummyResponse(State(self))

        def _api_called(self, call_type, **kwargs):
            add_dummy_api_call(
                self.dummy_response,
                call_type,
                **kwargs)

        def add(self, **kwargs):
            self._api_called("add", **kwargs)
            return self.dummy_response

        def resolve(self, **kwargs):
            self._api_called("resolve", **kwargs)
            return self.dummy_response

        def rm(self, **kwargs):
            self._api_called("rm", **kwargs)
            return self.dummy_response

        def sync(self, **kwargs):
            self._api_called("sync", **kwargs)
            return self.dummy_response

    return DummyResponse, DummyCommandPlugin


@pytest.fixture
def dummy_cmd_response():
    from pootle.core.plugin import provider
    from pootle.core.state import State
    from pootle_fs.delegate import fs_plugins
    from pootle_fs.utils import FSPlugin
    from pootle_project.models import Project

    DummyResponse, DummyCommandPlugin = _get_dummy_api_plugin()

    @provider(fs_plugins, sender=Project, weak=False)
    def plugins_provider_(**kwargs_):
        return dict(dummy_cmd=DummyCommandPlugin)

    project = Project.objects.get(code="project0")
    project.config["pootle_fs.fs_type"] = "dummy_cmd"
    plugin = FSPlugin(project)
    dummy_response = DummyResponse(State(plugin))
    return dummy_response, add_dummy_api_call


@lru_cache()
def _get_dummy_state_plugin():
    from pootle.core.state import State
    from pootle_fs.plugin import Plugin

    class DummyState(State):

        @property
        def states(self):
            return ["pootle_staged"]

        def state_pootle_staged(self, **kwargs):
            yield dict(
                pootle_path=kwargs.get("pootle_path"),
                fs_path=kwargs.get("fs_path"))

    class DummyCommandPlugin(Plugin):

        def state(self, **kwargs):
            return DummyState(self, **kwargs)

    return DummyState, DummyCommandPlugin


@pytest.fixture
def dummy_cmd_state():
    from pootle.core.plugin import provider
    from pootle_fs.delegate import fs_plugins
    from pootle_fs.utils import FSPlugin
    from pootle_project.models import Project

    DummyState, DummyCommandPlugin = _get_dummy_state_plugin()

    @provider(fs_plugins, sender=Project, weak=False)
    def plugins_provider_(**kwargs_):
        return dict(dummy_state_cmd=DummyCommandPlugin)

    project = Project.objects.get(code="project0")
    project.config["pootle_fs.fs_type"] = "dummy_state_cmd"
    return FSPlugin(project), DummyState
