#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2012 Zuza Software Foundation
# Copyright 2013-2014 Evernote Corporation
#
# This file is part of Pootle.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

import locale

from django.core.urlresolvers import reverse
from django.db import models
from django.utils.translation import ugettext_lazy as _


class Notice(models.Model):
    directory = models.ForeignKey('pootle_app.Directory', db_index=True)
    message = models.TextField(_('Message'))
    added = models.DateTimeField(
        # Translators: The date that the news item was written
        _('Added'),
        auto_now_add=True,
        null=True,
        db_index=True,
    )

    class Meta:
        ordering = ["-added"]

    def __unicode__(self):
        return self.message

    def get_absolute_url(self):
        return reverse('pootle-notifications-notice',
                       args=[self.directory.pootle_path, self.id])

    def get_date(self):
        return self.added.strftime(locale.nl_langinfo(locale.D_T_FMT))
