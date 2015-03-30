#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.apps import AppConfig


class PootleCoreConfig(AppConfig):
    name = 'pootle'

    def ready(self):
        import pootle.core.auth.signals
