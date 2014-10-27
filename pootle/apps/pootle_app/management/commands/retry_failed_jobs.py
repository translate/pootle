#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2014 Zuza Software Foundation
# Copyright 2013 Evernote Corporation
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

from django.conf import settings
from django.core.management.base import NoArgsCommand
from django.core.urlresolvers import set_script_prefix
from django.utils.encoding import force_unicode

from django_rq.queues import get_failed_queue

class Command(NoArgsCommand):
    help = "Retry failed RQ jobs."

    def handle_noargs(self, **options):
        # The script prefix needs to be set here because the generated
        # URLs need to be aware of that and they are cached. Ideally
        # Django should take care of setting this up, but it doesn't yet:
        # https://code.djangoproject.com/ticket/16734
        script_name = (u'/' if settings.FORCE_SCRIPT_NAME is None
                            else force_unicode(settings.FORCE_SCRIPT_NAME))
        set_script_prefix(script_name)

        failed_queue = get_failed_queue()
        for job_id in failed_queue.get_job_ids():
            failed_queue.requeue(job_id=job_id)
