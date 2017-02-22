# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging
import os

# This must be run before importing the rest of the Django libs.
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from pootle.core.management.subcommands import CommandWithSubcommands

from .project_commands import (CloneCommand, MoveCommand, RemoveCommand,
                               UpdateCommand)


logger = logging.getLogger()


class Command(CommandWithSubcommands):
    help = "Pootle project (via TPTool) API."
    subcommands = {
        "clone": CloneCommand,
        "move": MoveCommand,
        "remove": RemoveCommand,
        "update": UpdateCommand,
    }
