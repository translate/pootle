# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
from datetime import date

os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from pootle.core.delegate import log
from pootle_store.models import Store, Unit


class Command(BaseCommand):
    help = "Pootle log"

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            '-t', '--type',
            action='store',
            dest='type',
            help=(
                "Use given field as identifier to get object, "
                "should be unique"))
        parser.add_argument(
            'object',
            action='store',
            nargs="?",
            help="Unique identifier for object, by default pk")

    def handle_path(self, **kwargs):
        # ideally this would be any path but for now store...
        event_log = log.get(Store)(Store.objects.get(
            pootle_path=kwargs["object"]))
        for event in event_log.get_activity(start=date.today()):
            self.stdout.write(unicode(event).encode("utf-8"))

    def handle_unit(self, **kwargs):
        event_log = log.get(Unit)(Unit.objects.get(pk=kwargs["object"]))
        for event in event_log.get_activity():
            self.stdout.write(unicode(event).encode("utf-8"))

    def handle_user(self, **kwargs):
        User = get_user_model()
        event_log = log.get(User)(User.objects.get(username=kwargs["object"]))
        for event in event_log.get_activity():
            self.stdout.write(unicode(event).encode("utf-8"))

    def handle(self, **kwargs):
        if kwargs.get("type") and kwargs["type"] == "unit":
            return self.handle_unit(**kwargs)

        if kwargs.get("type") and kwargs["type"] == "user":
            return self.handle_user(**kwargs)

        if kwargs.get("type") and kwargs["type"] == "path":
            return self.handle_path(**kwargs)
