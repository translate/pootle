# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from ..url_helpers import urljoin
from .version import get_rtd_version


DOCS_BASE = u'https://docs.translatehouse.org/projects/pootle/en/'


def get_docs_url(path_name, version=None):
    """Returns the absolute URL to `path_name` in the RTD docs."""
    return urljoin(DOCS_BASE, get_rtd_version(version=version), path_name)
