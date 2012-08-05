#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2012 Zuza Software Foundation
#
# This file is part of Pootle.
#
# translate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from django.forms import ModelForm, ValidationError
from django.utils.translation import ugettext_lazy as _

from legalpages.models import LegalPage


class LegalPageForm(ModelForm):

    class Meta:
        model = LegalPage


    def clean(self):
        cleaned_data = super(LegalPageForm, self).clean()

        url = cleaned_data.get('url')
        body = cleaned_data.get('body')

        if url == '' and body == '':
            # Translators: 'URL' and 'content' refer to form fields.
            msg = _('URL or content must be provided.')
            raise ValidationError(msg)

        return cleaned_data
