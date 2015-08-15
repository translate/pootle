#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from translate.storage.factory import getclass

from django.utils.translation import ugettext as _

from pootle_store.models import Store
from pootle_statistics.models import SubmissionTypes

from .exceptions import (ERR_UNSUPPORTED_FILETYPE, ERR_MISSING_POOTLE_PATH,
                         ERR_MISSING_POOTLE_REV, ERR_FILE_IMPORT,
                         UnsupportedFiletypeError, MissingPootlePathError,
                         MissingPootleRevError, FileImportError)


def import_file(file, user=None):
    f = getclass(file)(file.read())
    if not hasattr(f, "parseheader"):
        raise UnsupportedFiletypeError(_(ERR_UNSUPPORTED_FILETYPE) % file.name)
    header = f.parseheader()
    pootle_path = header.get("X-Pootle-Path")
    if not pootle_path:
        raise MissingPootlePathError(_(ERR_MISSING_POOTLE_PATH) % file.name)

    rev = header.get("X-Pootle-Revision")
    if not rev or not rev.isdigit():
        raise MissingPootleRevError(_(ERR_MISSING_POOTLE_REV) % file.name)
    rev = int(rev)

    try:
        store, created = Store.objects.get_or_create(pootle_path=pootle_path)
    except Exception as e:
        raise FileImportError(_(ERR_FILE_IMPORT) % (file.name, e))

    store.update(overwrite=True, store=f, user=user,
                 submission_type=SubmissionTypes.UPLOAD)
