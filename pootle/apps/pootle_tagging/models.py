#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013, 2014 Zuza Software Foundation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# Pootle is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# Pootle; if not, see <http://www.gnu.org/licenses/>.

import re


def slugify_tag_name(tag_name):
    """Convert the given tag name to a slug."""
    # Replace invalid characters for slug with hyphens.
    slug = re.sub(r'[^a-z0-9-]', "-", tag_name.lower())

    # Replace groups of hyphens with a single hyphen.
    slug = re.sub(r'-{2,}', "-", slug)

    # Remove leading and trailing hyphens.
    return slug.strip("-")
