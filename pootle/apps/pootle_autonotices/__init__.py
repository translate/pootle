#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.db.models.signals import post_save

from pootle_language.models import Language
from pootle_project.models import Project

from . import signals

post_save.connect(signals.new_language, sender=Language)
post_save.connect(signals.new_project, sender=Project)
