#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

ERR_MISSING_POOTLE_PATH = "File '%s' missing X-Pootle-Path header\n"
ERR_UNSUPPORTED_FILETYPE = ("Unsupported filetype '%s', only PO files are "
                            "supported at this time\n")
ERR_MISSING_POOTLE_REV = ("File '%s' missing or invalid X-Pootle-Revision "
                          "header\n")
ERR_FILE_IMPORT = "Could not create '%s'. Missing Project/Language? (%s)"


class UnsupportedFiletypeError(ValueError):
    pass


class MissingPootlePathError(ValueError):
    pass


class MissingPootleRevError(ValueError):
    pass


class FileImportError(ValueError):
    pass
