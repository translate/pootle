# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle_fs.display import StateDisplay
from pootle_fs.management.commands import FSAPISubCommand


STATE_COLORMAP = {
    "conflict": ("CONFLICT", "CONFLICT"),
    "conflict_untracked": ("CONFLICT", "CONFLICT"),
    "remove": ("MISSING", "MISSING"),
    "merge_fs_wins": ("UPDATED", "UPDATED"),
    "merge_pootle_wins": ("UPDATED", "UPDATED"),
    "fs_ahead": (None, "UPDATED"),
    "fs_staged": ("MISSING", "STAGED"),
    "fs_untracked": ("MISSING", "UNTRACKED"),
    "fs_removed": (None, "REMOVED"),
    "pootle_untracked": ("UNTRACKED", "REMOVED"),
    "pootle_staged": ("STAGED", "REMOVED"),
    "pootle_removed": ("REMOVED", None),
    "pootle_ahead": ("UPDATED", None)}


class StateCommand(FSAPISubCommand):
    help = ("Show state of tracked and untracked files and Stores for the "
            "specified project")
    api_method = "state"

    def add_arguments(self, parser):
        super(StateCommand, self).add_arguments(parser)
        parser.add_argument(
            '-t', '--type',
            action='append',
            dest='state_type',
            help='State type')

    @property
    def colormap(self):
        return STATE_COLORMAP

    def display(self, **options):
        return StateDisplay(self.handle_api(**options))

    def is_empty(self, display):
        return not display.context.has_changed
