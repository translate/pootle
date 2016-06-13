# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from fnmatch import fnmatch


def filtered_fs_stores(plugin, fs_path, pootle_path):
    from pootle_store.models import Store

    state = plugin.state(pootle_path=pootle_path, fs_path=fs_path)
    stores = state.resources.store_filter.filtered(
        Store.objects.filter(translation_project__project=plugin.project))
    if fs_path:
        return state, [
            store for store
            in stores
            if fnmatch(plugin.get_fs_path(store.pootle_path), fs_path)]
    else:
        return state, list(stores)


def parse_fs_action_args(action):
    command_args = []
    plugin_kwargs = {}
    if action.endswith("_force"):
        action = action[:-6]
        command_args.append("--force")
        plugin_kwargs["force"] = True
    elif action.startswith("merge_"):
        if action.endswith("pootle"):
            command_args.append("--pootle-wins")
            plugin_kwargs["pootle_wins"] = True
        else:
            plugin_kwargs["pootle_wins"] = False
        action = "merge"
    return action, command_args, plugin_kwargs
