# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django import forms
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from .models import ANN_VPATH, Agreement, StaticPage


class AnnouncementForm(forms.ModelForm):

    class Meta:
        model = StaticPage
        fields = ('title', 'virtual_path', 'active', 'body', )
        help_texts = {
            'virtual_path': '',
            'active': '',
        }
        labels = {
            'virtual_path': '',
            'active': '',
            'title': '',
            'body': '',
        }
        widgets = {
            'virtual_path': forms.HiddenInput(),
            'active': forms.HiddenInput(),
        }

    def save(self, *args, **kwargs):
        if not self.cleaned_data['virtual_path'].startswith(ANN_VPATH):
            orig_vpath = self.cleaned_data['virtual_path']
            self.instance.virtual_path = ANN_VPATH + orig_vpath

        return super(AnnouncementForm, self).save(*args, **kwargs)


def agreement_form_factory(pages, user):
    """Factory that builds an agreement form.

    :param pages: Legal pages that need to be accepted by users.
    :param user: User bound to the agreement form.
    :return: An `AgreementForm` class with `pages` as required checkboxes.
    """
    class AgreementForm(forms.Form):

        def __init__(self, *args, **kwargs):
            kwargs.setdefault('label_suffix', '')
            super(AgreementForm, self).__init__(*args, **kwargs)

            self._pages = pages
            self._user = user

            for page in self._pages:
                self.add_page_field(page)

        def save(self, **kwargs):
            """Saves user agreements."""
            for page in self._pages:
                agreement, created = Agreement.objects.get_or_create(
                    user=self._user, document=page,
                )
                agreement.save()

        def legal_fields(self):
            """Returns any fields added by legal pages."""
            return [field for field in self
                    if field.name.startswith('legal_')]

        def add_page_field(self, page):
            """Adds `page` as a required field to this form."""
            url = page.url and page.url or \
                reverse('pootle-staticpages-display', args=[page.virtual_path])
            label_params = {
                'url': url,
                'classes': 'js-agreement-popup',
                'title': page.title,
            }
            label = mark_safe(_('I have read and accept: <a href="%(url)s" '
                                'class="%(classes)s">%(title)s</a>',
                                label_params))

            field_name = 'legal_%d' % page.pk
            self.fields[field_name] = forms.BooleanField(label=label,
                                                         required=True)
            self.fields[field_name].widget.attrs['class'] = 'js-legalfield'

    return AgreementForm
