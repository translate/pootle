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
    elif action.startswith("resolve"):
        if action.endswith("_overwrite"):
            command_args.append("--overwrite")
            plugin_kwargs["merge"] = False
        else:
            plugin_kwargs["merge"] = True
        if "pootle" in action:
            command_args.append("--pootle-wins")
            plugin_kwargs["pootle_wins"] = True
        else:
            plugin_kwargs["pootle_wins"] = False
        action = "resolve"
    return action, command_args, plugin_kwargs
