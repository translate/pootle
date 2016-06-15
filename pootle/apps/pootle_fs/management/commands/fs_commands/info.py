# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle_fs.management.commands import ProjectSubCommand


class ProjectInfoCommand(ProjectSubCommand):
    help = "Show pootle_fs configuration information for specified project."

    def handle(self, *args, **kwargs):
        fs = self.get_fs(kwargs['project'])
        self.stdout.write("Project: %s" % fs.project.code)
        self.stdout.write("type: %s" % fs.fs_type)
        self.stdout.write("URL: %s" % fs.fs_url)
