#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013-2014 Evernote Corporation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify
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

from django.core.urlresolvers import reverse

from contact_form.views import ContactFormView

from pootle.core.views import AjaxResponseMixin

from .forms import EvernoteContactForm


SUBJECT_TEMPLATE = 'Unit #%d (%s)'
BODY_TEMPLATE = '''
Unit: %s

Source: %s

Current translation: %s

Your question or comment:
'''


class EvernoteContactFormView(AjaxResponseMixin, ContactFormView):
    form_class = EvernoteContactForm

    def get_initial(self):
        initial = super(EvernoteContactFormView, self).get_initial()

        user = self.request.user
        if user.is_authenticated():
            initial.update({
                'name': user.full_name,
                'email': user.email,
            })

        report = self.request.GET.get('report', False)
        if report:
            try:
                from pootle_store.models import Unit
                uid = int(report)
                try:
                    unit = Unit.objects.select_related(
                        'store__translation_project__project',
                    ).get(id=uid)
                    if unit.is_accessible_by(user):
                        unit_absolute_url = self.request.build_absolute_uri(
                                unit.get_translate_url()
                            )
                        initial.update({
                            'subject': SUBJECT_TEMPLATE % (
                                unit.id,
                                unit.store.translation_project.language.code
                            ),
                            'body': BODY_TEMPLATE % (
                                unit_absolute_url,
                                unit.source,
                                unit.target
                            ),
                        })
                except Unit.DoesNotExist:
                    pass
            except ValueError:
                pass

        return initial

    def get_success_url(self):
        # XXX: This is unused. We don't need a `/contact/sent/` URL, but
        # the parent :cls:`ContactView` enforces us to set some value here
        return reverse('pootle-contact')
