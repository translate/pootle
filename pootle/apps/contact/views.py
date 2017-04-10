# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.template.loader import render_to_string
from django.urls import reverse
from django.views.generic import TemplateView

from contact_form.views import ContactFormView as OriginalContactFormView

from pootle.core.views.mixins import AjaxResponseMixin
from pootle.i18n.gettext import ugettext_lazy as _
from pootle_store.models import Unit

from .forms import ContactForm, ReportForm


class ContactFormTemplateView(TemplateView):
    template_name = 'contact_form/contact_form.html'


class ContactFormView(AjaxResponseMixin, OriginalContactFormView):
    form_class = ContactForm
    template_name = 'contact_form/xhr_contact_form.html'

    def get_context_data(self, **kwargs):
        ctx = super(ContactFormView, self).get_context_data(**kwargs)
        # Provide the form action URL to use in the template that renders the
        # contact dialog.
        ctx.update({
            'contact_form_title': _('Contact Us'),
            'contact_form_url': reverse('pootle-contact-xhr'),
        })
        return ctx

    def get_initial(self):
        initial = super(ContactFormView, self).get_initial()

        user = self.request.user
        if user.is_authenticated:
            initial.update({
                'name': user.full_name,
                'email': user.email,
            })

        return initial

    def get_success_url(self):
        # XXX: This is unused. We don't need a `/contact/sent/` URL, but the
        # parent :cls:`ContactView` enforces us to set some value here
        return reverse('pootle-contact')


class ReportFormView(ContactFormView):
    form_class = ReportForm

    def _get_reported_unit(self):
        """Get the unit the error is being reported for."""
        unit_pk = self.request.GET.get('report', False)
        if not unit_pk:
            return None

        try:
            unit_pk = int(unit_pk)
        except ValueError:
            return None

        try:
            unit = Unit.objects.select_related(
                'store__translation_project__project',
                'store__translation_project__language',
            ).get(pk=unit_pk)
        except Unit.DoesNotExist:
            return None

        if unit.is_accessible_by(self.request.user):
            return unit

        return None

    def get_context_data(self, **kwargs):
        ctx = super(ReportFormView, self).get_context_data(**kwargs)
        # Provide the form action URL to use in the template that renders the
        # contact dialog.
        unit_pk = self.unit.pk if self.unit else ''
        url = "%s?report=%s" % (reverse('pootle-contact-report-error'), unit_pk)
        ctx.update({
            'contact_form_title': _('Report problem with string'),
            'contact_form_url': url,
        })
        return ctx

    def get_form_kwargs(self):
        kwargs = super(ReportFormView, self).get_form_kwargs()
        self.unit = self._get_reported_unit()
        if self.unit:
            kwargs.update({'unit': self.unit})
        return kwargs

    def get_initial(self):
        initial = super(ReportFormView, self).get_initial()

        self.unit = self._get_reported_unit()
        if not self.unit:
            return initial

        abs_url = self.request.build_absolute_uri(self.unit.get_translate_url())
        initial.update({
            'context': render_to_string(
                'contact_form/report_form_context.txt',
                context={
                    'unit': self.unit,
                    'unit_absolute_url': abs_url,
                }),
        })
        return initial
