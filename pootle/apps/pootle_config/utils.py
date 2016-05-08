# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from collections import OrderedDict

from django.utils.functional import cached_property

from pootle.core.delegate import config


class ConfigDict(object):
    """Assumes keys for __config__ are unique, uses last instance of key
    if not
    """

    def __init__(self, context):
        self.context = context

    @property
    def __config__(self):
        raise NotImplementedError

    @cached_property
    def conf(self):
        return OrderedDict(self.__config__.list_config())

    def reload(self):
        if "conf" in self.__dict__:
            del self.__dict__["conf"]

    def __contains__(self, k):
        return self.conf.__contains__(k)

    def __getitem__(self, k):
        return self.conf.__getitem__(k)

    def __iter__(self):
        return self.conf.__iter__()

    def __setitem__(self, k, v):
        self.__config__.set_config(k, v)
        self.reload()

    def get(self, k, default=None):
        return self.conf.get(k, default)

    def keys(self):
        return self.conf.keys()

    def items(self):
        return self.conf.items()

    def values(self):
        return self.conf.values()


class SiteConfig(ConfigDict):

    def __init__(self):
        pass

    @property
    def __config__(self):
        return config.get()


class ModelConfig(ConfigDict):

    @property
    def __config__(self):
        return config.get(self.context)


class ObjectConfig(ConfigDict):

    @property
    def __config__(self):
        return config.get(
            self.context.__class__,
            instance=self.context)
