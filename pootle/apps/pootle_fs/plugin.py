# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging
import os
import shutil

from django.contrib.auth import get_user_model
from django.utils.functional import cached_property
from django.utils.lru_cache import lru_cache

from pootle.core.delegate import (
    config, response as pootle_response, state as pootle_state)
from pootle_store.models import FILE_WINS, POOTLE_WINS, Store
from pootle_project.models import Project

from .decorators import emits_state, responds_to_state
from .delegate import fs_finder, fs_matcher, fs_resources
from .signals import fs_pre_push, fs_post_push, fs_pre_pull, fs_post_pull


logger = logging.getLogger(__name__)


class Plugin(object):
    """Base Plugin implementation"""

    name = None

    def __init__(self, project):
        if not isinstance(project, Project):
            raise TypeError(
                "pootle_fs.Plugin expects a Project")
        self.project = project

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__)
            and self.project == other.project
            and self.name == other.name)

    def __str__(self):
        return "<%s(%s)>" % (self.__class__.__name__, self.project)

    @property
    def is_cloned(self):
        return os.path.exists(self.project.local_fs_path)

    @property
    def finder_class(self):
        return fs_finder.get(self.__class__)

    @property
    def fs_url(self):
        return self.project.config["pootle_fs.fs_url"]

    @property
    def response_class(self):
        return pootle_response.get(self.state_class)

    @cached_property
    def matcher_class(self):
        return fs_matcher.get(self.__class__)

    @property
    def store_fs_class(self):
        from .models import StoreFS

        return StoreFS

    @cached_property
    def matcher(self):
        return self.matcher_class(self)

    @cached_property
    def pootle_user(self):
        User = get_user_model()
        username = config.get(
            self.project.__class__,
            instance=self.project,
            key="pootle_fs.pootle_user")
        if username:
            try:
                return User.objects.get(username=username)
            except User.DoesNotExist:
                logger.warning(
                    "Misconfigured pootle_fs user: %s"
                    % username)

    @cached_property
    def resources(self):
        return fs_resources.get(self.__class__)(self.project)

    @cached_property
    def state_class(self):
        return pootle_state.get(self.__class__)

    @lru_cache(maxsize=None)
    def get_fs_path(self, pootle_path):
        """
        Reverse match an FS filepath from a ``Store.pootle_path``.

        :param pootle_path: A ``Store.pootle_path``
        :returns: An filepath relative to the FS root.
        """
        return self.matcher.reverse_match(pootle_path)

    def clear_repo(self):
        if self.is_cloned:
            shutil.rmtree(self.project.local_fs_path)

    def create_store_fs(self, fs_path=None, pootle_path=None, store=None):
        return self.store_fs_class.objects.create(
            project=self.project,
            pootle_path=pootle_path,
            path=fs_path,
            store=store)

    def find_translations(self, fs_path=None, pootle_path=None):
        """
        Find translation files from the file system

        :param fs_path: Path glob to filter translations matching FS path
        :param pootle_path: Path glob to filter translations to add matching
          ``pootle_path``
        :yields pootle_path, fs_path: Where `pootle_path` and `fs_path` are
          matched paths.
        """
        return self.matcher.matches(fs_path, pootle_path)

    def pull(self):
        """
        Pull the FS from external source if required.
        """
        raise NotImplementedError

    def push(self, paths=None, message=None, response=None):
        """
        Push the FS to an external source if required.
        """
        raise NotImplementedError

    def reload(self):
        self.project.config.reload()
        if "matcher" in self.__dict__:
            del self.__dict__["matcher"]
        if "pootle_user" in self.__dict__:
            del self.__dict__["pootle_user"]

    def response(self, state):
        return self.response_class(state)

    def state(self, fs_path=None, pootle_path=None):
        """
        Get a state object for showing current state of FS/Pootle

        :param fs_path: FS path glob to filter translations
        :param pootle_path: Pootle path glob to filter translations
          ``pootle_path``
        :returns state: Where ``state`` is an instance of self.state_class
        """
        self.pull()
        return self.state_class(
            self, fs_path=fs_path, pootle_path=pootle_path)

    @responds_to_state
    def add(self, state, response,
            fs_path=None, pootle_path=None, force=False):
        """
        Stage translations from Pootle into the FS

        If ``force``=``True`` is present it will also:
        - stage untracked conflicting files from Pootle
        - stage tracked conflicting files to update from Pootle

        :param force: Add conflicting translations.
        :param fs_path: FS path glob to filter translations
        :param pootle_path: Pootle path glob to filter translations
        :returns response: Where ``response`` is an instance of self.respose_class
        """
        to_add = state["pootle_untracked"]
        if force:
            to_add = (
                to_add
                + state["conflict_untracked"]
                + state["fs_removed"]
                + state["conflict"])
        for fs_state in to_add:
            if fs_state.state_type in ["pootle_untracked", "conflict_untracked"]:
                fs_state.kwargs["store_fs"] = self.create_store_fs(
                    pootle_path=fs_state.pootle_path,
                    fs_path=fs_state.fs_path)
            fs_state.store_fs.file.add()
            response.add("added_from_pootle", fs_state=fs_state)
        return response

    @responds_to_state
    def fetch(self, state, response,
              fs_path=None, pootle_path=None, force=False):
        """
        Stage translations from FS into Pootle

        If ``force``=``True`` is present it will also:
        - stage untracked conflicting files from FS
        - stage tracked conflicting files to update from FS

        :param force: Fetch conflicting translations.
        :param fs_path: FS path glob to filter translations
        :param pootle_path: Pootle path glob to filter translations
        :returns response: Where ``response`` is an instance of self.respose_class
        """
        to_fetch = state["fs_untracked"]
        if force:
            to_fetch = (
                to_fetch
                + state["conflict_untracked"]
                + state["pootle_removed"]
                + state["conflict"])
        for fs_state in to_fetch:
            if fs_state.state_type in ["fs_untracked", "conflict_untracked"]:
                fs_state.kwargs["store_fs"] = self.create_store_fs(
                    pootle_path=fs_state.pootle_path,
                    fs_path=fs_state.fs_path)
            fs_state.store_fs.file.fetch()
            response.add("fetched_from_fs", fs_state=fs_state)
        return response

    @responds_to_state
    def merge(self, state, response,
              fs_path=None, pootle_path=None, pootle_wins=False):
        """
        Stage translations for merge.

        :param pootle_wins: Prefer Pootle where there are conflicting units
        :param fs_path: FS path glob to filter translations
        :param pootle_path: Pootle path glob to filter translations
        :returns response: Where ``response`` is an instance of self.respose_class
        """
        for fs_state in state["conflict"] + state["conflict_untracked"]:
            if fs_state.state_type == "conflict_untracked":
                fs_state.kwargs["store_fs"] = self.create_store_fs(
                    store=Store.objects.get(pootle_path=fs_state.pootle_path),
                    fs_path=fs_state.fs_path)
            fs_state.store_fs.file.merge(pootle_wins)
            if pootle_wins:
                response.add("staged_for_merge_pootle", fs_state=fs_state)
            else:
                response.add("staged_for_merge_fs", fs_state=fs_state)
        return response

    @responds_to_state
    def rm(self, state, response, fs_path=None, pootle_path=None, force=False):
        """
        Stage translations for removal.

        If ``force``=``True`` is present it will also:
        - stage untracked files from FS
        - stage untracked Stores

        :param force: Fetch conflicting translations.
        :param fs_path: FS path glob to filter translations
        :param pootle_path: Pootle path glob to filter translations
        :returns response: Where ``response`` is an instance of self.respose_class
        """
        removed = (
            state["pootle_removed"]
            + state["fs_removed"]
            + state["both_removed"])
        if force:
            removed = (
                removed
                + state["conflict_untracked"]
                + state["fs_untracked"]
                + state["pootle_untracked"])
        for fs_state in removed:
            if fs_state.state_type.endswith("_untracked"):
                fs_state.kwargs["store_fs"] = self.create_store_fs(
                    pootle_path=fs_state.pootle_path,
                    fs_path=fs_state.fs_path)
            fs_state.store_fs.file.rm()
            response.add("staged_for_removal", fs_state=fs_state)
        return response

    @responds_to_state
    def unstage(self, state, response, fs_path=None, pootle_path=None):
        """
        Unstage files staged for addition, merge or removal
        """
        to_unstage = (
            state["remove"]
            + state["merge_pootle_wins"]
            + state["merge_fs_wins"]
            + state["pootle_ahead"]
            + state["fs_ahead"]
            + state["pootle_staged"]
            + state["fs_staged"])
        for fs_state in to_unstage:
            staged = (
                fs_state.state_type not in ["fs_ahead", "pootle_ahead"]
                or fs_state.store_fs.resolve_conflict in [FILE_WINS, POOTLE_WINS])
            if staged:
                fs_state.store_fs.file.unstage()
                response.add("unstaged", fs_state=fs_state)
        return response

    @responds_to_state
    def sync_merge(self, state, response, fs_path=None, pootle_path=None):
        """
        Perform merge between Pootle and working directory

        :param fs_path: FS path glob to filter translations
        :param pootle_path: Pootle path glob to filter translations
        :returns response: Where ``response`` is an instance of self.respose_class
        """
        for fs_state in (state["merge_pootle_wins"] + state["merge_fs_wins"]):
            pootle_wins = (fs_state.state_type == "merge_pootle_wins")
            store_fs = fs_state.store_fs
            store_fs.file.pull(
                merge=True,
                pootle_wins=pootle_wins,
                user=self.pootle_user)
            store_fs.file.push()
            if pootle_wins:
                response.add("merged_from_pootle", fs_state=fs_state)
            else:
                response.add("merged_from_fs", fs_state=fs_state)
        return response

    @responds_to_state
    @emits_state(pre=fs_pre_pull, post=fs_post_pull)
    def sync_pull(self, state, response, fs_path=None, pootle_path=None):
        """
        Pull translations from working directory to Pootle

        :param fs_path: FS path glob to filter translations
        :param pootle_path: Pootle path glob to filter translations
        :returns response: Where ``response`` is an instance of self.respose_class
        """
        for fs_state in (state['fs_staged'] + state['fs_ahead']):
            fs_state.store_fs.file.pull(user=self.pootle_user)
            response.add("pulled_to_pootle", fs_state=fs_state)
        return response

    @responds_to_state
    @emits_state(pre=fs_pre_push, post=fs_post_push)
    def sync_push(self, state, response, fs_path=None, pootle_path=None):
        """
        Push translations from Pootle to working directory.

        :param fs_path: FS path glob to filter translations
        :param pootle_path: Pootle path glob to filter translations
        :returns response: Where ``response`` is an instance of self.respose_class
        """
        pushable = state['pootle_staged'] + state['pootle_ahead']
        for fs_state in pushable:
            fs_state.store_fs.file.push()
            response.add('pushed_to_fs', fs_state=fs_state)
        return response

    @responds_to_state
    def sync_rm(self, state, response, fs_path=None, pootle_path=None):
        """
        Remove Store and files from working directory that are staged for
        removal.

        :param fs_path: FS path glob to filter translations
        :param pootle_path: Pootle path glob to filter translations
        :returns response: Where ``response`` is an instance of self.respose_class
        """
        for fs_state in state['remove']:
            fs_state.store_fs.file.delete()
            response.add("removed", fs_state=fs_state)
        return response

    @responds_to_state
    def sync(self, state, response, fs_path=None, pootle_path=None):
        """
        Synchronize all staged and non-conflicting files and Stores, and push
        changes upstream if required.

        :param fs_path: FS path glob to filter translations
        :param pootle_path: Pootle path glob to filter translations
        :returns response: Where ``response`` is an instance of self.respose_class
        """
        self.sync_rm(
            state, response, fs_path=fs_path, pootle_path=pootle_path)
        self.sync_merge(
            state, response, fs_path=fs_path, pootle_path=pootle_path)
        self.sync_pull(
            state, response, fs_path=fs_path, pootle_path=pootle_path)
        self.sync_push(
            state, response, fs_path=fs_path, pootle_path=pootle_path)
        self.push(response)
        sync_types = [
            "pushed_to_fs", "pulled_to_pootle",
            "merged_from_pootle", "merged_from_fs"]
        for sync_type in sync_types:
            if sync_type in response:
                for response_item in response.completed(sync_type):
                    response_item.store_fs.file.on_sync()
        return response
