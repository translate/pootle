#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2012 Zuza Software Foundation
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

from django import forms
from django.contrib import auth
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from registration.forms import RegistrationForm as OriginalRegistrationForm

from staticpages.models import LegalPage

from .models import PootleProfile


class RegistrationForm(OriginalRegistrationForm):
    """Custom registration form that adds required checkboxes for any
    legal documents defined in the server.
    """

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)

        # FIXME: We should handle caching in the manager
        for lp in LegalPage.live.iterator():
            url = lp.url and lp.url or reverse('staticpages.display',
                                               args=[lp.virtual_path])
            anchor = u'href="%s" class="fancybox"' % url
            # Translators: The second '%s' is the title of a document
            label = mark_safe(_("I have read and accept: <a %s>%s</a>",
                                (anchor, lp.title,)))

            field_name = 'legal_%d' % lp.pk
            self.fields[field_name] = forms.BooleanField(label=label,
                                                         required=True)
            self.fields[field_name].widget.attrs['class'] = 'js-legalfield'

    def legal_fields(self):
        """Returns any fields added by legal pages."""
        return [field for field in self if field.name.startswith('legal_')]


def language_list(request):
    """Returns the list of localised language names, with 'default'."""
    tr_default = _("Default")

    if tr_default != "Default":
        tr_default = u"%s | \u202dDefault" % tr_default

    from pootle.i18n.override import lang_choices

    choices = lang_choices()
    choices.insert(0, ('', tr_default))

    return choices


def lang_auth_form_factory(request, **kwargs):

    class LangAuthenticationForm(AuthenticationForm):

        language = forms.ChoiceField(label=_('Interface Language'),
                                     choices=language_list(request),
                                     initial="", required=False,
                                     widget=forms.Select(attrs={
                                         'class': 'js-select2 select2-language',
                                     }),
        )


        def clean(self):
            username = self.cleaned_data.get('username')
            password = self.cleaned_data.get('password')

            if username and password:
                self.user_cache = auth.authenticate(username=username,
                                                    password=password)

                if self.user_cache is None:
                    raise forms.ValidationError(
                        _("Please enter a correct username and password. "
                          "Note that both fields are case-sensitive.")
                    )
                elif not self.user_cache.is_active:
                    raise forms.ValidationError(_("This account is inactive."))

            return self.cleaned_data

    return LangAuthenticationForm(**kwargs)


class UserForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')


def pootle_profile_form_factory(exclude_fields):

    class PootleProfileForm(forms.ModelForm):

        class Meta:
            model = PootleProfile

        def __init__(self, *args, **kwargs):
            self.exclude_fields = exclude_fields
            super(PootleProfileForm, self).__init__(*args, **kwargs)

            # Delete the fields the user can't edit
            for field in self.exclude_fields:
                del self.fields[field]
            self.fields['ui_lang'].widget.attrs['class'] = \
                "js-select2 select2-language"
            self.fields['alt_src_langs'].widget.attrs['class'] = \
                "js-select2 select2-multiple"
            self.fields['alt_src_langs'].widget.attrs['data-placeholder'] = \
                _('Select one or more languages')

    return PootleProfileForm
