# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle.core.plugin.delegate import Getter, Provider


fs_file = Getter()
fs_finder = Getter()
fs_matcher = Getter()
fs_resources = Getter()
fs_translation_mapping_validator = Getter()
fs_url_validator = Getter()

# File system plugins such as git/mercurial/localfs
fs_plugins = Provider()

fs_pre_pull_handlers = Provider()
fs_post_pull_handlers = Provider()
fs_pre_push_handlers = Provider()
fs_post_push_handlers = Provider()

fs_upstream = Provider()
