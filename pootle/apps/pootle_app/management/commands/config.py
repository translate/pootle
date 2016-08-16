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
        group = parser.add_mutually_exclusive_group()
        group.add_argument(
            '-g', '--get',
            action='store',
            dest='get',
            metavar="KEY",
            help="Get config with this key, key must be unique")
        group.add_argument(
            '-l', '--list',
            action='append',
            dest='list',
            metavar="KEY",
            help=(
                "List config with this key, "
                "can be specified multiple times"))
        group.add_argument(
            '-s', '--set',
            action='store',
            dest="set",
            metavar=("KEY", "VALUE"),
            nargs=2,
            help=(
                "Set config with this VALUE, KEY should not exist "
                "or must be unique"))
        group.add_argument(
            '-a', '--append',
            action='store',
            dest="append",
            metavar=("KEY", "VALUE"),
            nargs=2,
            help="Append config with this value")
        group.add_argument(
            '-c', '--clear',
            action='append',
            dest='clear',
            metavar="KEY",
            help="Clear config with this key")
        parser.add_argument(
            '-j', '--json',
            action='store_true',
            dest='json',
            help=(
                "When getting/setting/appending a config dump/load "
                "VALUE as json"))

    def print_config_item(self, name, key, value, name_col=25, key_col=25):
        format_string = "{: <%d} {: <%d} {: <30}" % (name_col, key_col)
        self.stdout.write(
            format_string.format(
                name, key, self.repr_value(value)))

    def get_conf(self, **kwargs):
        if kwargs["object"] and not kwargs["content_type"]:
            raise CommandError(
                "You must set --content-type (-t) when using "
                "--object-pk (-o)")
        if kwargs["content_type"]:
            if "." not in kwargs["content_type"]:
                raise CommandError(
                    "content_type should be set with $app_label.$model_name")
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
                catch_exc = (
                    ct_model.DoesNotExist,
                    ct_model.MultipleObjectsReturned,
                    ValueError,
                    FieldError)
                try:
                    instance = ct_model.objects.get(**model_query)
                except catch_exc as e:
                    raise CommandError(e)
                return config.get(ct_model, instance=instance)
            return config.get(ct_model)
        return config.get()

    def print_no_config(self):
        self.stdout.write("No configuration found")

    def handle(self, **kwargs):
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
        self.stdout.write("Config '%s' set" % k)

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
        self.stdout.write("Config '%s' appended" % k)

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
        except conf.model.MultipleObjectsReturned as e:
            raise CommandError(e)
        if kwargs["json"]:
            v = json.dumps(v)
        else:
            v = self.repr_value(v)
        self.stdout.write(v, ending="")

    def get_item_name(self, item, object_field=None):
        if item.content_type:
            ct = ".".join(item.content_type.natural_key())
            if item.object_pk:
                if object_field:
                    pk = getattr(
                        item.content_object,
                        object_field)
                else:
                    pk = item.object_pk
                return "%s[%s]" % (ct, pk)
            else:
                return ct
        return "Pootle"

    def handle_list_config(self, conf, **kwargs):
        if kwargs["list"]:
            conf = conf.filter(key__in=set(kwargs["list"]))
        items = []
        name_col = 25
        key_col = 25
        # first pass, populate the list and find longest name/key
        for item in conf.order_by("key", "pk").iterator():
            name = self.get_item_name(
                item, object_field=kwargs["object_field"])
            if len(name) > name_col:
                name_col = len(name)
            if len(item.key) > key_col:
                key_col = len(item.key)
            items.append((name, item.key, item.value))
        for name, key, value in items:
            self.print_config_item(
                name, key, value,
                name_col=name_col,
                key_col=key_col)
        if not items:
            self.print_no_config()

    def handle_clear_config(self, conf, **kwargs):
        for key in kwargs["clear"]:
            conf.clear_config(key)
