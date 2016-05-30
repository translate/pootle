# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.


import datetime
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from pootle_statistics.models import ScoreLog


class Command(BaseCommand):
    help = "Refresh score"

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            dest='reset',
            default=False,
            help='Reset all scores to zero',
        )
        parser.add_argument(
            '--user',
            action='append',
            dest='users',
            help='User to refresh',
        )

    def handle(self, **options):
        self.stdout.write('Start running of refresh_scores command...')

        User = get_user_model()
        users = User.objects.all()
        if options['users']:
            users = users.filter(username__in=options['users'])

        if options['reset']:
            users.update(score=0)
            scorelogs = ScoreLog.objects.all()
            if options['users']:
                scorelogs = scorelogs.filter(user__in=users)

            scorelogs.delete()

            if options['users']:
                self.stdout.write('Scores for specified users were reset to 0.')
            else:
                self.stdout.write('Scores for all users were reset to 0.')
            return

        start = datetime.datetime.now()
        for user_pk, username in users.values_list("pk", "username"):
            self.stdout.write("Processing user %s..." % username)
            scorelog_qs = ScoreLog.objects.filter(user=user_pk) \
                .select_related(
                    'submission',
                    'submission__suggestion',
                    'submission__unit')
            user_score = 0
            for scorelog in scorelog_qs.iterator():
                score_delta = scorelog.get_score_delta()
                translated, reviewed = scorelog.get_paid_wordcounts()
                user_score += score_delta
                ScoreLog.objects.filter(id=scorelog.id).update(
                    score_delta=score_delta,
                    translated_wordcount=translated
                )
            self.stdout.write("Score for user %s set to %.3f" %
                              (username, user_score))
            User.objects.filter(id=user_pk).update(score=user_score)
        end = datetime.datetime.now()
        self.stdout.write('All done in %s.' % (end - start))
