# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.contrib.auth import get_user_model

from pootle.core.delegate import event_formatters
from pootle.core.plugin import provider
from pootle_log.formatters import base_formatters


@provider(event_formatters, sender=get_user_model())
def gather_user_event_formatters(**kwargs_):
    return base_formatters
