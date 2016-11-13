# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle.core.delegate import panels, url_patterns
from pootle.core.plugin import provider
from pootle_translationproject.views import TPBrowseView

from .panels import VFolderPanel
from .urls import urlpatterns


@provider(url_patterns)
def vf_url_provider(**kwargs_):
    return dict(vfolders=urlpatterns)


@provider(panels, sender=TPBrowseView)
def vf_panel_provider(**kwargs_):
    return dict(vfolders=VFolderPanel)
