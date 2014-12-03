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

"""Form fields required for handling translation files."""
import re

from django import forms
from django.utils import timezone
from django.utils.translation import get_language, ugettext as _

from translate.misc.multistring import multistring

from pootle.core.log import (TRANSLATION_ADDED, TRANSLATION_CHANGED,
                             TRANSLATION_DELETED)
from pootle.core.mixins import CachedMethods
from pootle_app.models.permissions import check_permission
from pootle_statistics.models import (Submission, SubmissionFields,
                                      SubmissionTypes)

from .fields import to_db
from .models import Unit
from .util import FUZZY, TRANSLATED, UNTRANSLATED


############## text cleanup and highlighting #########################

FORM_RE = re.compile('\r\n|\r|\n|\t|\\\\')

def highlight_whitespace(text):
    """Make whitespace chars visible."""

    def replace(match):
        submap = {
            '\r\n': '\\r\\n\n',
            '\r': '\\r\n',
            '\n': '\\n\n',
            '\t': '\\t',
            '\\': '\\\\',
            }
        return submap[match.group()]

    return FORM_RE.sub(replace, text)


FORM_UNRE = re.compile('\r|\n|\t|\\\\r|\\\\n|\\\\t|\\\\\\\\')

def unhighlight_whitespace(text):
    """Replace visible whitespace with proper whitespace."""

    def replace(match):
        submap = {
            '\t': '',
            '\n': '',
            '\r': '',
            '\\t': '\t',
            '\\n': '\n',
            '\\r': '\r',
            '\\\\': '\\',
            }
        return submap[match.group()]

    return FORM_UNRE.sub(replace, text)


class MultiStringWidget(forms.MultiWidget):
    """Custom Widget for editing multistrings, expands number of text
    area based on number of plural forms."""

    def __init__(self, attrs=None, nplurals=1, textarea=True):
        if textarea:
            widget = forms.Textarea
        else:
            widget = forms.TextInput

        widgets = [widget(attrs=attrs) for i in xrange(nplurals)]
        super(MultiStringWidget, self).__init__(widgets, attrs)

    def format_output(self, rendered_widgets):
        from django.utils.safestring import mark_safe
        if len(rendered_widgets) == 1:
            return mark_safe(rendered_widgets[0])

        output = ''
        for i, widget in enumerate(rendered_widgets):
            output += '<div lang="%s" title="%s">' % \
                (get_language(), _('Plural Form %d', i))
            output += widget
            output += '</div>'

        return mark_safe(output)

    def decompress(self, value):
        if value is None:
            return [None] * len(self.widgets)
        elif isinstance(value, multistring):
            return [highlight_whitespace(string) for string in value.strings]
        elif isinstance(value, list):
            return [highlight_whitespace(string) for string in value]
        elif isinstance(value, basestring):
            return [highlight_whitespace(value)]
        else:
            raise ValueError


class HiddenMultiStringWidget(MultiStringWidget):
    """Uses hidden input instead of textareas."""

    def __init__(self, attrs=None, nplurals=1):
        widgets = [forms.HiddenInput(attrs=attrs) for i in xrange(nplurals)]
        super(MultiStringWidget, self).__init__(widgets, attrs)

    def format_output(self, rendered_widgets):
        return super(MultiStringWidget, self).format_output(rendered_widgets)

    def __call__(self):
        #HACKISH: Django is inconsistent in how it handles
        # Field.widget and Field.hidden_widget, it expects widget to
        # be an instantiated object and hidden_widget to be a class,
        # since we need to specify nplurals at run time we can let
        # django instantiate hidden_widget.
        #
        # making the object callable let's us get away with forcing an
        # object where django expects a class
        return self


class MultiStringFormField(forms.MultiValueField):

    def __init__(self, nplurals=1, attrs=None, textarea=True, *args, **kwargs):
        self.widget = MultiStringWidget(nplurals=nplurals, attrs=attrs,
                                        textarea=textarea)
        self.hidden_widget = HiddenMultiStringWidget(nplurals=nplurals)
        fields = [forms.CharField() for i in range(nplurals)]
        super(MultiStringFormField, self).__init__(fields=fields,
                                                   *args, **kwargs)

    def compress(self, data_list):
        return [unhighlight_whitespace(string) for string in data_list]


class UnitStateField(forms.BooleanField):

    def to_python(self, value):
        """Returns a Python boolean object.

        It is necessary to customize the behavior because the default
        ``BooleanField`` treats the string '0' as ``False``, but if the
        unit is in ``UNTRANSLATED`` state (which would report '0' as a
        value), we need the marked checkbox to be evaluated as ``True``.

        :return: ``False`` for any unknown :cls:`~pootle_store.models.Unit`
            states and for the 'False' string.
        """
        truthy_values = (str(s) for s in (UNTRANSLATED, FUZZY, TRANSLATED))
        if (isinstance(value, basestring) and
            (value.lower() == 'false' or value not in truthy_values)):
            value = False
        else:
            value = bool(value)

        return super(forms.BooleanField, self).to_python(value)


def unit_form_factory(language, snplurals=None, request=None):

    if snplurals is not None:
        tnplurals = language.nplurals
    else:
        tnplurals = 1

    action_disabled = False
    if request is not None:
        cantranslate = check_permission("translate", request)
        cansuggest = check_permission("suggest", request)

        if not (cansuggest or cantranslate):
            action_disabled = True

    target_attrs = {
        'lang': language.code,
        'dir': language.direction,
        'class': 'translation expanding focusthis js-translation-area',
        'rows': 5,
        'tabindex': 10,
    }

    fuzzy_attrs = {
        'accesskey': 'f',
        'class': 'fuzzycheck',
        'tabindex': 13,
    }

    if action_disabled:
        target_attrs['disabled'] = 'disabled'
        fuzzy_attrs['disabled'] = 'disabled'

    class UnitForm(forms.ModelForm):
        class Meta:
            model = Unit
            fields = ('id', 'index', 'target_f', 'state',)

        id = forms.IntegerField(required=False)
        target_f = MultiStringFormField(
            nplurals=tnplurals,
            required=False,
            attrs=target_attrs,
        )
        state = UnitStateField(
            required=False,
            label=_('Needs work'),
            widget=forms.CheckboxInput(
                attrs=fuzzy_attrs,
                check_test=lambda x: x == FUZZY,
            ),
        )

        def __init__(self, *args, **kwargs):
            self.request = kwargs.pop('request', None)
            super(UnitForm, self).__init__(*args, **kwargs)
            self.updated_fields = []

        def clean_target_f(self):
            value = self.cleaned_data['target_f']

            if self.instance.target.strings != multistring(value or [u'']):
                self.instance._target_updated = True
                self.updated_fields.append((SubmissionFields.TARGET,
                                            to_db(self.instance.target),
                                            to_db(value)))

            return value

        def clean_state(self):
            old_state = self.instance.state  # Integer
            is_fuzzy = self.cleaned_data['state']  # Boolean
            new_target = self.cleaned_data['target_f']

            if (self.request is not None and
                not check_permission('administrate', self.request) and
                is_fuzzy):
                raise forms.ValidationError(_('Fuzzy flag must be cleared'))

            if new_target:
                if old_state == UNTRANSLATED:
                    self.instance._save_action = TRANSLATION_ADDED
                    self.instance.store \
                                 .flag_for_deletion(CachedMethods.TRANSLATED)
                else:
                    self.instance._save_action = TRANSLATION_CHANGED

                if is_fuzzy:
                    new_state = FUZZY
                else:
                    new_state = TRANSLATED
            else:
                new_state = UNTRANSLATED
                if old_state > FUZZY:
                    self.instance._save_action = TRANSLATION_DELETED
                    self.instance.store \
                                 .flag_for_deletion(CachedMethods.TRANSLATED)

            if is_fuzzy != (old_state == FUZZY):
                # when Unit toggles its FUZZY state the number of translated words
                # also changes
                self.instance.store.flag_for_deletion(CachedMethods.FUZZY,
                                                      CachedMethods.TRANSLATED,
                                                      CachedMethods.LAST_ACTION)

            if old_state != new_state:
                self.instance._state_updated = True
                self.updated_fields.append((SubmissionFields.STATE,
                                            old_state, new_state))
            else:
                self.instance._state_updated = False

            return new_state

    return UnitForm


def unit_comment_form_factory(language):

    comment_attrs = {
        'lang': language.code,
        'dir': language.direction,
        'class': 'comments expanding focusthis',
        'rows': 2,
        'tabindex': 15,
    }

    class UnitCommentForm(forms.ModelForm):

        class Meta:
            fields = ('translator_comment',)
            model = Unit

        translator_comment = forms.CharField(
            required=True,
            label=_("Translator comment"),
            widget=forms.Textarea(attrs=comment_attrs),
        )

        def __init__(self, *args, **kwargs):
            self.request = kwargs.pop('request', None)
            super(UnitCommentForm, self).__init__(*args, **kwargs)

        def save(self):
            """Register the submission and save the comment."""
            if self.has_changed():
                creation_time = timezone.now()
                translation_project = self.request.translation_project

                sub = Submission(
                    creation_time=creation_time,
                    translation_project=translation_project,
                    submitter=self.request.user,
                    unit=self.instance,
                    field=SubmissionFields.COMMENT,
                    type=SubmissionTypes.NORMAL,
                    old_value=u"",
                    new_value=self.cleaned_data['translator_comment']
                )
                sub.save()

            super(UnitCommentForm, self).save()

    return UnitCommentForm
