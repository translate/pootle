#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Zuza Software Foundation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify
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


from django import forms
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _


def add_page_field(form, page):
    """Adds `page` as a required field to `form`."""
    url = page.url and page.url or reverse('staticpages.display',
                                           args=[page.virtual_path])
    anchor = u'href="%s" class="fancybox"' % url
    # Translators: The second '%s' is the title of a document
    label = mark_safe(_("I have read and accept: <a %s>%s</a>",
                        (anchor, page.title,)))

    field_name = 'legal_%d' % page.pk
    form.fields[field_name] = forms.BooleanField(label=label,
                                                 required=True)
    form.fields[field_name].widget.attrs['class'] = 'js-legalfield'
