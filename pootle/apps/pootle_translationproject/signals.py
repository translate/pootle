# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.dispatch import Signal


tp_inited_async = Signal(
    providing_args=["instance", "response_url", ],
    use_caching=True)
tp_init_failed_async = Signal(
    providing_args=["instance", ],
    use_caching=True)
