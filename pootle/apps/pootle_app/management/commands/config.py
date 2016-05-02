# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import collections
import json
import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldError
from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext_lazy as _

from pootle.core.delegate import config


class Command(BaseCommand):
    help = "Manage configuration for Pootle objects."

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            'content_type',
            action='store',
            nargs="?",
            help="Get/set config for given content type")
        parser.add_argument(
            'object',
            action='store',
            nargs="?",
            help="Unique identifier for object, by default pk")
        parser.add_argument(
            '-o', '--object-field',
            action='store',
            dest='object_field',
            help=(
                "Use given field as identifier to get object, "
                "should be unique"))
        parser.add_argument(
            '-g', '--get',
            action='store',
            dest='get',
            metavar="KEY",
            help="Get config with this key, key must be unique")
        parser.add_argument(
            '-l', '--list',
            action='append',
            dest='list',
            metavar="KEY",
            help=(
                "List config with this key, "
                "can be specified multiple times"))
        parser.add_argument(
            '-s', '--set',
            action='store',
            dest="set",
            metavar=("KEY", "VALUE"),
            nargs=2,
            help=(
                "Set config with this VALUE, KEY should not exist "
                "or must be unique"))
        parser.add_argument(
            '-j', '--json',
            action='store_true',
            dest='json',
            help=(
                "When getting/setting/appending a config dump/load "
                "VALUE as json"))
        parser.add_argument(
            '-a', '--append',
            action='store',
            dest="append",
            metavar=("KEY", "VALUE"),
            nargs=2,
            help="Append config with this value")
        parser.add_argument(
            '-c', '--clear',
            action='append',
            dest='clear',
            metavar="KEY",
            help="Clear config with this key")

    def print_config_item(self, item, object_field=None):
        if item.content_type:
            ct = ".".join(item.content_type.natural_key())
            if item.object_pk:
                if object_field:
                    pk = getattr(
                        item.content_object,
                        object_field)
                else:
                    pk = item.object_pk
                item_name = "%s[%s]" % (ct, pk)
            else:
                item_name = ct
        else:
            item_name = "Pootle"
        self.stdout.write(
            "{: <25} {: <25} {: <30}".format(
                item_name, item.key, self.repr_value(item.value)))

    def get_conf(self, **kwargs):
        if kwargs["object"] and not kwargs["content_type"]:
            raise CommandError(
                _("You must set --content-type (-t) when using "
                  "--object-pk (-o)"))

        if kwargs["content_type"]:
            if "." not in kwargs["content_type"]:
                raise CommandError(
                    _("content_type should be set with $app_label.$model_name"))
            parts = kwargs["content_type"].split(".")
            model_name = parts[-1]
            app_label = ".".join(parts[:-1])
            try:
                ct = ContentType.objects.get(
                    app_label=app_label,
                    model=model_name)
            except ContentType.DoesNotExist as e:
                raise CommandError(e)
            ct_model = ct.model_class()
            if kwargs["object"]:
                if kwargs["object_field"]:
                    model_query = {kwargs["object_field"]: kwargs["object"]}
                else:
                    model_query = dict(pk=kwargs["object"])
                try:
                    instance = ct_model.objects.get(**model_query)
                except ct_model.DoesNotExist as e:
                    raise CommandError(e)
                except ct_model.MultipleObjectsReturned as e:
                    raise CommandError(e)
                except FieldError as e:
                    raise CommandError(e)
                return config.get(ct_model, instance=instance)
            return config.get(ct_model)
        return config.get()

    def print_no_config(self, **kwargs):
        self.stdout.write("No configuration found")

    def check_incompatible_flags(self, **kwargs):
        mutually_incompatible = ["get", "set", "append", "list", "clear"]
        found_flags = [
            k for k, v
            in kwargs.items()
            if k in mutually_incompatible
            and (v and v != (None, None))]
        if len(found_flags) > 1:
            raise CommandError(
                _("You cannot use get, set, list, append and clear "
                  "together"))

    def handle(self, **kwargs):
        self.check_incompatible_flags(**kwargs)
        conf = self.get_conf(**kwargs)
        if kwargs["get"]:
            return self.handle_get_config(
                conf, **kwargs)
        elif kwargs["set"]:
            return self.handle_set_config(
                conf, **kwargs)
        elif kwargs["append"]:
            return self.handle_append_config(
                conf, **kwargs)
        elif kwargs["clear"]:
            return self.handle_clear_config(
                conf, **kwargs)
        return self.handle_list_config(
            conf, **kwargs)

    def handle_set_config(self, conf, **kwargs):
        k, v = kwargs["set"]
        if kwargs["json"]:
            v = self.json_value(v)
        try:
            conf.set_config(k, v)
        except conf.model.MultipleObjectsReturned as e:
            raise CommandError(e)
        self.stdout.write("Config updated")

    def json_value(self, value):
        try:
            return json.JSONDecoder(
                object_pairs_hook=collections.OrderedDict).decode(value)
        except ValueError as e:
            raise CommandError(e)

    def handle_append_config(self, conf, **kwargs):
        k, v = kwargs["append"]
        if kwargs["json"]:
            v = self.json_value(v)
        conf.append_config(k, v)
        self.stdout.write("Config updated")

    def repr_value(self, value):
        if not isinstance(value, (str, unicode)):
            value_class = type(value).__name__
            return (
                "%s(%s)"
                % (value_class,
                   json.dumps(value)))
        return value

    def handle_get_config(self, conf, **kwargs):
        try:
            v = conf.get_config(kwargs["get"])
        except conf.model.DoesNotExist as e:
            return None
        except conf.model.MultipleObjectsReturned as e:
            raise CommandError(e)
        if kwargs["json"]:
            v = json.dumps(v)
        else:
            v = self.repr_value(v)
        self.stdout.write(v)

    def handle_list_config(self, conf, **kwargs):
        found = False
        if kwargs["list"]:
            conf = conf.filter(key__in=set(kwargs["list"]))
        for item in conf.order_by("key", "pk"):
            found = True
            self.print_config_item(item, kwargs["object_field"])
        if found is False:
            self.print_no_config(**kwargs)

    def handle_clear_config(self, conf, **kwargs):
        for key in kwargs["clear"]:
            conf.clear_config(key)
