# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle.core.plugin import provider

from .delegate import fs_plugins
from .localfs import LocalFSPlugin


@provider(fs_plugins)
def localfs_plugin_provider(**kwargs_):
    return dict(localfs=LocalFSPlugin)
