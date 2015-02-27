#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL2
# license. See the LICENSE file for a copy of the license and the AUTHORS file
# for copyright and authorship information.

from django.dispatch import Signal

translation_file_updated = Signal(providing_args=["path"])
post_unit_update = Signal(providing_args=["oldstats", "newstats"])
translation_submitted = Signal(providing_args=["unit", "profile"])
