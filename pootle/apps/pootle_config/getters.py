# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle.core.delegate import config
from pootle.core.plugin import getter

from .exceptions import ConfigurationError
from .models import Config


@getter(config)
def config_getter(**kwargs):
    sender = kwargs["sender"]
    instance = kwargs.get("instance")
    key = kwargs.get("key")

    if sender:
        if instance is not None and not isinstance(instance, sender):
            raise ConfigurationError(
                "'instance' must be an instance of 'sender', when specified")
        conf = Config.objects.get_config_queryset(instance or sender)
    elif instance:
        raise ConfigurationError(
            "'sender' must be defined when 'instance' is specified")
    else:
        conf = Config.objects.site_config()

    if key is None:
        return conf

    if isinstance(key, (list, tuple)):
        return conf.list_config(key)

    try:
        return conf.get_config(key)
    except Config.MultipleObjectsReturned as e:
        raise ConfigurationError(e)
