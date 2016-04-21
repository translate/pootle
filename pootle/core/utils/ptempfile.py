# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
import tempfile

from django.conf import settings


def mkstemp(*args, **kwargs):
    """Wrap tempfile.mkstemp, setting the permissions of the created temporary
    file as specified in settings (see bug 1983).
    """
    fd, name = tempfile.mkstemp(*args, **kwargs)
    if hasattr(os, 'fchmod'):
        os.fchmod(fd, settings.POOTLE_SYNC_FILE_MODE)
    else:
        os.chmod(name, settings.POOTLE_SYNC_FILE_MODE)
    return fd, name
