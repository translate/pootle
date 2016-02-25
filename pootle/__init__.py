#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle.core.utils.version import get_version

VERSION = (2, 7, 3, 'beta', 1)

__version__ = get_version(VERSION)

default_app_config = 'pootle.apps.PootleConfig'
