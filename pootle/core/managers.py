#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008, 2013 Zuza Software Foundation
# Copyright 2014 Evernote Corporation
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

from django.db import models


class RelatedManager(models.Manager):
    """Model manager that always does full joins on relations.

    This saves us lots of database queries later.
    """
    def get_queryset(self):
        return super(RelatedManager, self).get_queryset() \
                                          .select_related(depth=1)
