# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible


@deconstructible
class PootleFileSystemStorage(FileSystemStorage):
    """Custom storage class, otherwise Django assumes all files are
    uploads headed to `MEDIA_ROOT`.

    Subclassing necessary to avoid messing up with migrations (#3557).
    """

    def __init__(self, **kwargs):
        kwargs.update({
            'location': settings.POOTLE_TRANSLATION_DIRECTORY,
        })
        super(PootleFileSystemStorage, self).__init__(**kwargs)
