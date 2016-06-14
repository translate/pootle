# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.


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
