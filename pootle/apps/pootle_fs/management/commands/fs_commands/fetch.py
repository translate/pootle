# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle_fs.management.commands import ProjectSubCommand


class FetchCommand(ProjectSubCommand):
    help = "Fetch remote filesystems."

    def handle(self, **options):
        self.get_fs(options["project"]).fetch()
