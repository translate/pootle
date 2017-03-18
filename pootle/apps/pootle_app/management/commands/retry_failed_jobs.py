# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os

# This must be run before importing Django.
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from django.core.management.base import BaseCommand

from django_rq.queues import get_failed_queue


class Command(BaseCommand):
    help = "Retry failed RQ jobs."

    def handle(self, **options):
        failed_queue = get_failed_queue()
        for job_id in failed_queue.get_job_ids():
            failed_queue.requeue(job_id=job_id)
