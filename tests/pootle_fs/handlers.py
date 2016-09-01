# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle.core.plugin import provider
from pootle_fs.delegate import fs_pre_push_handlers
from pootle_fs.localfs import LocalFSPlugin


@pytest.mark.django_db
def test_custom_fs_push_scripts(project_fs):

    assert fs_pre_push_handlers.gather().keys() == []

    def push_handler(plugin):
        pass

    @provider(fs_pre_push_handlers, sender=LocalFSPlugin)
    def script_provider(**kwargs):
        return dict(test_script=push_handler)

    # this provider only provides for localfs
    assert fs_pre_push_handlers.gather().keys() == []

    scripts = fs_pre_push_handlers.gather(LocalFSPlugin)
    assert scripts["test_script"] is push_handler
