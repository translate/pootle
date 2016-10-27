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

from django.conf import settings
from django.core.management.base import BaseCommand
from django.urls import set_script_prefix
from django.utils.encoding import force_unicode

from django_rq.queues import get_failed_queue


class Command(BaseCommand):
    help = "Retry failed RQ jobs."

    def handle(self, **options):
        # The script prefix needs to be set here because the generated URLs
        # need to be aware of that and they are cached. Ideally Django should
        # take care of setting this up, but it doesn't yet (fixed in Django
        # 1.10): https://code.djangoproject.com/ticket/16734
        script_name = (u'/'
                       if settings.FORCE_SCRIPT_NAME is None
                       else force_unicode(settings.FORCE_SCRIPT_NAME))
        set_script_prefix(script_name)

        failed_queue = get_failed_queue()
        for job_id in failed_queue.get_job_ids():
            failed_queue.requeue(job_id=job_id)
