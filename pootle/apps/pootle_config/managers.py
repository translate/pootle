# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.base import ModelBase
from django.utils.encoding import force_text

from pootle.core.signals import config_updated

from .delegate import config_should_not_be_appended, config_should_not_be_set
from .exceptions import ConfigurationError


class ConfigQuerySet(models.QuerySet):

    def __init__(self, *args, **kwargs):
        super(ConfigQuerySet, self).__init__(*args, **kwargs)
        self.query_model = None

    def _clone(self, **kwargs):
        clone = super(ConfigQuerySet, self)._clone(**kwargs)
        clone.query_model = self.query_model
        return clone

    @property
    def base_qs(self):
        qs = self.__class__(self.model)
        qs.query_model = self.query_model
        return qs.select_related("content_type")

    def append_config(self, key, value="", model=None):
        model = self.get_query_model(model)
        self.should_append_config(key, value, model)
        self.create(
            key=key, value=value,
            **self.get_model_kwargs(model))

    def clear_config(self, key, model=None):
        self.get_config_queryset(model).filter(key=key).delete()

    def config_for(self, model):
        """
        QuerySet for all config for a particular model (either an instance or
        a class).
        """
        self.query_model = model
        return self.base_qs.filter(**self.get_model_kwargs(model))

    def get_config(self, key, model=None):
        conf = self.get_config_queryset(model)
        try:
            key = conf.get(key=key)
        except self.model.DoesNotExist:
            return None
        return key.value

    def get_config_queryset(self, model):
        model = self.get_query_model(model)
        if model:
            if isinstance(model, models.Model):
                return self.config_for(model)
            return self.config_for(model).filter(object_pk__isnull=True)
        return self.site_config()

    def get_model_kwargs(self, model):
        model = self.get_query_model(model)
        if model is None:
            return {}
        ct = ContentType.objects.get_for_model(model)
        kwargs = dict(content_type=ct)
        if isinstance(model, models.Model):
            kwargs["object_pk"] = force_text(model._get_pk_val())
        return kwargs

    def get_query_model(self, model=None):
        if model:
            self.query_model = model
        elif self.query_model:
            model = self.query_model
        return model

    def list_config(self, key=None, model=None):
        conf = self.get_config_queryset(model)
        conf_list = []

        if isinstance(key, (list, tuple)):
            if key:
                conf = conf.filter(key__in=key)
        elif key is not None:
            conf = conf.filter(key=key)
        for item in conf.order_by("key", "pk"):
            # dont use values_list to trigger to_python
            conf_list.append((item.key, item.value))
        return conf_list

    def set_config(self, key, value="", model=None):
        model = self.get_query_model(model)
        model_conf = self.get_config_queryset(model)
        self.should_set_config(key, value, model)
        old_value = None
        updated = False
        try:
            conf = model_conf.get(key=key)
        except model_conf.model.DoesNotExist:
            conf = self.create(
                key=key,
                value=value,
                **self.get_model_kwargs(model))
            updated = True
        if conf.value != value:
            old_value = conf.value
            updated = True
            conf.value = value
            conf.save()
        if updated:
            if isinstance(model, ModelBase):
                sender = model
                instance = None
            else:
                sender = model.__class__
                instance = model
            config_updated.send(
                sender,
                instance=instance,
                key=key,
                value=value,
                old_value=old_value)

    def should_append_config(self, key, value, model=None):
        sender = model
        instance = None
        if isinstance(model, models.Model):
            sender = model.__class__
            instance = model
        no_append = config_should_not_be_appended.get(
            sender,
            instance=instance,
            key=key,
            value=value)
        if no_append:
            raise ConfigurationError(no_append)

    def should_set_config(self, key, value, model=None):
        sender = model
        instance = None
        if isinstance(model, models.Model):
            sender = model.__class__
            instance = model
        no_set = config_should_not_be_set.get(
            sender,
            instance=instance,
            key=key,
            value=value)
        if no_set:
            raise ConfigurationError(no_set)

    def site_config(self):
        self.query_model = None
        return self.base_qs.filter(
            content_type__isnull=True, object_pk__isnull=True)


class ConfigManager(models.Manager):
    pass
