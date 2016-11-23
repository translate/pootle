# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand, CommandError

from pootle.core.delegate import serializers, deserializers


class Command(BaseCommand):
    help = "Manage serialization for Projects."

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            '-m --model',
            dest="model",
            action="store",
            help='List de/serializers for given model.')
        parser.add_argument(
            '-d --deserializers',
            action="store_true",
            dest="deserializers",
            help='List deserializers')

    def model_from_content_type(self, ct_name):
        if not ct_name:
            return
        if "." not in ct_name:
            raise CommandError(
                "Model name should be contenttype "
                "$app_name.$label")
        try:
            return ContentType.objects.get_by_natural_key(
                *ct_name.split(".")).model_class()
        except ContentType.DoesNotExist as e:
            raise CommandError(e)

    def handle(self, **kwargs):
        model = self.model_from_content_type(kwargs["model"])
        if kwargs["deserializers"]:
            return self.print_serializers_list(
                deserializers.gather(model),
                serializer_type="deserializers")
        return self.print_serializers_list(
            serializers.gather(model))

    def print_serializers_list(self, serials, serializer_type="serializers"):
        if not serials.keys():
            self.stdout.write(
                "There are no %s set up on your system" % serializer_type)
        if not serials.keys():
            return
        heading = serializer_type.capitalize()
        self.stdout.write("\n%s" % heading)
        self.stdout.write("-" * len(heading))
        for name, serializer in serials.items():
            self.stdout.write(
                "{!s: <30} {!s: <50} ".format(name, serializer))
