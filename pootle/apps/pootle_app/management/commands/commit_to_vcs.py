# -*- coding: utf-8 -*-
#
# Copyright 2012-2013 Zuza Software Foundation
#
# This file is part of Pootle.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

import logging
import os
from optparse import make_option

# This must be run before importing Django.
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from pootle_app.management.commands import PootleCommand


class Command(PootleCommand):
    help = "Allow VCS-managed data to be committed manually."
    option_list = PootleCommand.option_list + (
        make_option('--user', default='admin',
                    help="Username to list in the commit message"),
        )

    def handle_noargs(self, **options):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            self.user = User.objects.get(username=options['user'])
        except User.DoesNotExist:
            logging.error("Unknown user (%s)", options['user'])
            return

        super(Command, self).handle_noargs(**options)

    def handle_translation_project(self, tp, **options):
        """Commit to VCS all stores referred to by the translation project

        The translation project may be limited by language, filename, etc.
        """
        tp.commit_dir(self.user, tp.directory)
