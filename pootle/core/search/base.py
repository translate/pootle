#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.conf import settings


SERVER_SETTINGS_NAME = 'POOTLE_TM_SERVER'


class SearchBackend(object):
    def __init__(self, config_name=None, **kwargs):
        self._setup_settings(config_name)

    def _setup_settings(self, config_name):
        self._settings = getattr(settings, SERVER_SETTINGS_NAME, None)
        if config_name is not None:
            self._settings = self._settings[config_name]

    def search(self, unit):
        """Search for TM results.

        :param unit: :cls:`~pootle_store.models.Unit`
        :return: list of results or [] for no results or offline
        """
        raise NotImplementedError

    def update(self, language, obj):
        """Add a unit to the backend"""
        pass
