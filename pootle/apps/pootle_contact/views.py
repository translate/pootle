#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Zuza Software Foundation
# Copyright 2013 Evernote Corporation
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

from django.core.urlresolvers import reverse

from contact_form.views import ContactFormView

from pootle.core.views import AjaxResponseMixin

from .forms import PootleContactForm


class PootleContactFormView(AjaxResponseMixin, ContactFormView):
    form_class = PootleContactForm

    def get_initial(self):
        initial = super(PootleContactFormView, self).get_initial()

        user = self.request.user
        if user.is_authenticated():
            initial.update({
                'name': user.get_profile().fullname,
                'email': user.email,
            })

        return initial

    def get_success_url(self):
        # XXX: This is unused. We don't need a `/contact/sent/` URL, but
        # the parent :cls:`ContactView` enforces us to set some value here
        return reverse('pootle-contact')
