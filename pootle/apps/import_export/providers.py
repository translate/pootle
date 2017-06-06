# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle.core.delegate import context_data
from pootle.core.plugin import provider
from pootle_translationproject.views import TPBrowseView

from .utils import TPTMXExporter


@provider(context_data, sender=TPBrowseView)
def register_context_data(**kwargs):
    tp = kwargs['view'].tp
    return dict(has_offline_tm=TPTMXExporter(tp).exported_file_exists())
