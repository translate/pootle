# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

"""Form fields required for handling translation files."""

from translate.misc.multistring import multistring

from django import forms
from django.contrib.auth import get_user_model
from django.urls import Resolver404, resolve
from django.utils.translation import get_language

from pootle.core.delegate import review
from pootle.core.url_helpers import split_pootle_path
from pootle.i18n.gettext import ugettext as _
from pootle_app.models import Directory
from pootle_app.models.permissions import (
    check_permission, check_user_permission)
from pootle_checks.constants import CATEGORY_CODES, CHECK_NAMES
from pootle_comment.forms import UnsecuredCommentForm
from pootle_misc.util import get_date_interval
from pootle_project.models import Project
from pootle_statistics.models import SubmissionFields, SubmissionTypes

from .constants import ALLOWED_SORTS, FUZZY, OBSOLETE, TRANSLATED, UNTRANSLATED
from .contextmanagers import update_store_after
from .fields import to_db
from .form_fields import (
    CategoryChoiceField, CommaSeparatedCheckboxSelectMultiple,
    ISODateTimeField, MultipleArgsField)
from .models import Suggestion, Unit


UNIT_SEARCH_FILTER_CHOICES = (
    ("all", "all"),
    ("translated", "translated"),
    ("untranslated", "untranslated"),
    ("fuzzy", "fuzzy"),
    ("incomplete", "incomplete"),
    ("suggestions", "suggestions"),
    ("my-suggestions", "my-suggestions"),
    ("user-suggestions", "user-suggestions"),
    ("user-suggestions-accepted", "user-suggestions-accepted"),
    ("user-suggestions-rejected", "user-suggestions-rejected"),
    ("my-submissions", "my-submissions"),
    ("user-submissions", "user-submissions"),
    ("my-submissions-overwritten", "my-submissions-overwritten"),
    ("user-submissions-overwritten", "user-submissions-overwritten"),
    ("checks", "checks"))

UNIT_SEARCH_SORT_CHOICES = (
    ('priority', 'priority'),
    ('oldest', 'oldest'),
    ('newest', 'newest'))

# # # # # # #  text cleanup and highlighting # # # # # # # # # # # # #


class MultiStringWidgetMixin(object):

    def decompress(self, value):
        if value is None:
            return [None] * len(self.widgets)
        elif isinstance(value, multistring):
            return [string for string in value.strings]
        elif isinstance(value, list):
            return value
        elif isinstance(value, basestring):
            return [value]

        raise ValueError


class MultiStringWidget(MultiStringWidgetMixin, forms.MultiWidget):
    """Custom Widget for editing multistrings, expands number of text
    area based on number of plural forms.
    """

    def __init__(self, attrs=None, nplurals=1, textarea=True):
        if textarea:
            widget = forms.Textarea
        else:
            widget = forms.TextInput

        widgets = [widget(attrs=attrs) for i_ in xrange(nplurals)]
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


class HiddenMultiStringWidget(MultiStringWidgetMixin, forms.MultiWidget):
    """Uses hidden input instead of textareas."""

    def __init__(self, attrs=None, nplurals=1):
        widgets = [forms.HiddenInput(attrs=attrs) for i_ in xrange(nplurals)]
        super(HiddenMultiStringWidget, self).__init__(widgets, attrs)

    def format_output(self, rendered_widgets):
        return super(
            HiddenMultiStringWidget, self).format_output(rendered_widgets)

    def __call__(self):
        # HACKISH: Django is inconsistent in how it handles Field.widget and
        # Field.hidden_widget, it expects widget to be an instantiated object
        # and hidden_widget to be a class, since we need to specify nplurals at
        # run time we can let django instantiate hidden_widget.
        #
        # making the object callable let's us get away with forcing an object
        # where django expects a class
        return self


class MultiStringFormField(forms.MultiValueField):

    def __init__(self, nplurals=1, attrs=None, textarea=True, *args, **kwargs):
        self.widget = MultiStringWidget(nplurals=nplurals, attrs=attrs,
                                        textarea=textarea)
        self.hidden_widget = HiddenMultiStringWidget(nplurals=nplurals)
        fields = [forms.CharField(strip=False) for i_ in range(nplurals)]
        super(MultiStringFormField, self).__init__(fields=fields,
                                                   *args, **kwargs)

    def compress(self, data_list):
        return data_list


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
        'rows': 2,
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
        class Meta(object):
            model = Unit
            fields = ('target_f', )

        target_f = MultiStringFormField(
            nplurals=tnplurals,
            required=False,
            attrs=target_attrs,
        )
        is_fuzzy = forms.BooleanField(
            required=False,
            label=_("Needs work"),
            widget=forms.CheckboxInput(attrs=fuzzy_attrs))
        suggestion = forms.ModelChoiceField(
            queryset=Suggestion.objects.all(),
            required=False)
        comment = forms.CharField(required=False)

        def __init__(self, *args, **kwargs):
            self.request = kwargs.pop('request', None)
            self.user = self.request.user
            super(UnitForm, self).__init__(*args, **kwargs)
            self._updated_fields = []
            self.fields['target_f'].widget.attrs['data-translation-aid'] = \
                self['target_f'].value()
            self.initial.update(dict(is_fuzzy=(self.instance.state == FUZZY)))

        @property
        def updated_fields(self):
            order_dict = {
                SubmissionFields.STATE: 0,
                SubmissionFields.TARGET: 1,
            }
            return sorted(self._updated_fields, key=lambda x: order_dict[x[0]])

        def clean_target_f(self):
            value = self.cleaned_data['target_f']

            if self.instance.target != multistring(value or [u'']):
                self._updated_fields.append((SubmissionFields.TARGET,
                                            to_db(self.instance.target),
                                            to_db(value)))

            return value

        def clean_is_fuzzy(self):
            return self.data.get("is_fuzzy", None) and True or False

        def clean(self):
            old_state = self.instance.state  # Integer
            is_fuzzy = self.cleaned_data['is_fuzzy']  # Boolean
            new_target = self.cleaned_data['target_f']

            # If suggestion is provided set `old_state` should be `TRANSLATED`.
            if self.cleaned_data['suggestion']:
                old_state = TRANSLATED

                # Skip `TARGET` field submission if suggestion value is equal
                # to submitted translation
                if new_target == self.cleaned_data['suggestion'].target_f:
                    self._updated_fields = []
            not_cleared = (
                self.request is not None
                and not check_permission('administrate', self.request)
                and is_fuzzy)
            if not_cleared:
                self.add_error(
                    'is_fuzzy',
                    forms.ValidationError(
                        _('Needs work flag must be cleared')))

            if new_target:
                if is_fuzzy:
                    new_state = FUZZY
                else:
                    new_state = TRANSLATED
            else:
                new_state = UNTRANSLATED
            if old_state not in [new_state, OBSOLETE]:
                self._updated_fields.append((SubmissionFields.STATE,
                                             old_state, new_state))

                self.cleaned_data['state'] = new_state
            else:
                self.cleaned_data['state'] = old_state

            return super(UnitForm, self).clean()

        def save(self, *args, **kwargs):
            if not self.updated_fields:
                return
            changed_with = kwargs.pop("changed_with", None)
            suggestion = self.cleaned_data["suggestion"]
            with update_store_after(self.instance.store):
                user = (
                    suggestion.user
                    if suggestion
                    else self.user)
                self.instance.save(
                    user=user,
                    changed_with=changed_with)
            return self.instance

    return UnitForm


def unit_comment_form_factory(language):

    comment_attrs = {
        'lang': language.code,
        'dir': language.direction,
        'class': 'comments expanding focusthis',
        'rows': 1,
        'tabindex': 15,
    }

    class UnitCommentForm(forms.ModelForm):

        class Meta(object):
            fields = ('translator_comment',)
            model = Unit

        translator_comment = forms.CharField(
            required=True,
            label=_("Translator comment"),
            widget=forms.Textarea(attrs=comment_attrs),
        )

        def __init__(self, *args, **kwargs):
            self.request = kwargs.pop('request', None)
            self.previous_value = ''

            super(UnitCommentForm, self).__init__(*args, **kwargs)

            if self.request.method == 'DELETE':
                self.fields['translator_comment'].required = False

        def clean_translator_comment(self):
            # HACKISH: Setting empty string when `DELETE` is being used
            if self.request.method == 'DELETE':
                self.previous_value = self.instance.translator_comment
                return ''

            return self.cleaned_data['translator_comment']

        def save(self, *args, **kwargs):
            self.instance.save(user=self.request.user)

    return UnitCommentForm


class UnitSearchForm(forms.Form):

    offset = forms.IntegerField(required=False)
    path = forms.CharField(
        max_length=2048,
        required=True)
    previous_uids = MultipleArgsField(
        field=forms.IntegerField(),
        required=False)
    uids = MultipleArgsField(
        field=forms.IntegerField(),
        required=False)
    filter = forms.ChoiceField(
        required=False,
        choices=UNIT_SEARCH_FILTER_CHOICES)
    checks = forms.MultipleChoiceField(
        required=False,
        widget=CommaSeparatedCheckboxSelectMultiple,
        choices=CHECK_NAMES.items())
    category = CategoryChoiceField(
        required=False,
        choices=CATEGORY_CODES.items())
    month = forms.DateField(
        required=False,
        input_formats=['%Y-%m'])
    sort = forms.ChoiceField(
        required=False,
        choices=UNIT_SEARCH_SORT_CHOICES)

    user = forms.ModelChoiceField(
        queryset=get_user_model().objects.all(),
        required=False,
        to_field_name="username")

    search = forms.CharField(required=False)

    soptions = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple,
        choices=(
            ('exact', _('Phrase match')),
            ('case', _('Case-sensitive match'))))

    sfields = forms.MultipleChoiceField(
        required=False,
        widget=CommaSeparatedCheckboxSelectMultiple,
        choices=(
            ('source', _('Source Text')),
            ('target', _('Target Text')),
            ('notes', _('Comments')),
            ('locations', _('Locations'))),
        initial=['source', 'target'])

    def __init__(self, *args, **kwargs):
        self.request_user = kwargs.pop("user")
        super(UnitSearchForm, self).__init__(*args, **kwargs)
        self.fields["modified-since"] = ISODateTimeField(required=False)

    def clean(self):
        if "checks" in self.errors:
            del self.errors["checks"]
            self.cleaned_data["checks"] = None
        if "user" in self.errors:
            del self.errors["user"]
            self.cleaned_data["user"] = self.request_user
        if self.errors:
            return
        self.cleaned_data['count'] = self.request_user.get_unit_rows()
        self.cleaned_data["vfolder"] = None
        pootle_path = self.cleaned_data.get("path")
        path_keys = [
            "project_code", "language_code", "dir_path", "filename"]
        try:
            path_kwargs = {
                k: v
                for k, v in resolve(pootle_path).kwargs.items()
                if k in path_keys}
        except Resolver404:
            raise forms.ValidationError('Unrecognised path')
        self.cleaned_data.update(path_kwargs)
        sort_on = "units"
        if "filter" in self.cleaned_data:
            unit_filter = self.cleaned_data["filter"]
            if unit_filter in ('suggestions', 'user-suggestions'):
                sort_on = 'suggestions'
            elif unit_filter in ('user-submissions', ):
                sort_on = 'submissions'
        sort_by_param = self.cleaned_data["sort"]
        self.cleaned_data["sort_by"] = ALLOWED_SORTS[sort_on].get(sort_by_param)
        self.cleaned_data["sort_on"] = sort_on

    def clean_month(self):
        if self.cleaned_data["month"]:
            return get_date_interval(self.cleaned_data["month"].strftime("%Y-%m"))

    def clean_user(self):
        return self.cleaned_data["user"] or self.request_user

    def clean_path(self):
        lang_code, proj_code = split_pootle_path(
            self.cleaned_data["path"])[:2]
        if not (lang_code or proj_code):
            permission_context = Directory.objects.projects
        elif proj_code and not lang_code:
            try:
                permission_context = Project.objects.select_related(
                    "directory").get(code=proj_code).directory
            except Project.DoesNotExist:
                raise forms.ValidationError("Unrecognized path")
        else:
            # no permission checking on lang translate views
            return self.cleaned_data["path"]
        if self.request_user.is_superuser:
            return self.cleaned_data["path"]
        can_view_path = check_user_permission(
            self.request_user, "administrate", permission_context)
        if can_view_path:
            return self.cleaned_data["path"]
        raise forms.ValidationError("Unrecognized path")


class BaseSuggestionForm(UnsecuredCommentForm):
    should_save = lambda self: True

    def __init__(self, *args, **kwargs):
        kwargs["request_user"] = kwargs.get("request_user") or self.request_user
        super(BaseSuggestionForm, self).__init__(**kwargs)
        self.fields["comment"].required = False

    @property
    def review_type(self):
        return SubmissionTypes.WEB

    @property
    def suggestion_review(self):
        return review.get(self.target_object.__class__)(
            [self.target_object],
            self.request_user,
            review_type=self.review_type)


class SuggestionReviewForm(BaseSuggestionForm):

    action = forms.ChoiceField(
        required=True,
        choices=(
            ("accept", "Accept"),
            ("reject", "Reject")))

    def clean_action(self):
        if not self.target_object.is_pending:
            self.add_error(
                "action",
                forms.ValidationError(
                    _("Suggestion '%s' has already been accepted or rejected.",
                      self.target_object)))
        return self.data["action"]

    def clean(self):
        self_review = (
            self.request_user == self.target_object.user
            and self.cleaned_data.get("action") == "reject")
        permission = (
            "view"
            if self_review
            else "review")
        has_permission = check_user_permission(
            self.request_user,
            permission,
            self.target_object.unit.store.parent)
        if not has_permission:
            raise forms.ValidationError(
                _("Insufficient rights to access this page."))
        if not self.errors:
            super(SuggestionReviewForm, self).clean()

    def save(self):
        if self.cleaned_data["action"] == "accept":
            self.suggestion_review.accept(
                target=self.cleaned_data.get("target_f"))
        else:
            self.suggestion_review.reject()
        if self.cleaned_data["comment"]:
            super(SuggestionReviewForm, self).save()


class SubmitFormMixin(object):

    def __init__(self, *args, **kwargs):
        self.unit = kwargs.pop("unit")
        self.request_user = kwargs.pop("request_user")
        super(SubmitFormMixin, self).__init__(*args, **kwargs)
        snplurals = (
            len(self.unit.source.strings)
            if self.unit.hasplural()
            else None)
        nplurals = (
            self.unit.store.translation_project.language.nplurals
            if snplurals
            else 1)
        self.fields["target_f"].widget = MultiStringWidget(
            nplurals=nplurals,
            attrs={
                'lang': self.unit.store.translation_project.language.code,
                'dir': self.unit.store.translation_project.language.direction,
                'class': 'translation expanding focusthis js-translation-area',
                'rows': 2,
                'tabindex': 10})
        self.fields['target_f'].widget.attrs[
            'data-translation-aid'] = self['target_f'].value()
        self.fields[
            "target_f"].hidden_widget = HiddenMultiStringWidget(nplurals=nplurals)
        self.fields["target_f"].fields = [
            forms.CharField(strip=False, required=False) for i in range(nplurals)]
        for k in ["user", "name", "email"]:
            if k in self.fields:
                self.fields[k].required = False


class SuggestionSubmitForm(SubmitFormMixin, BaseSuggestionForm):

    target_f = MultiStringFormField(required=False, require_all_fields=False)

    def save_unit(self):
        self.suggestion_review.accept(target=self.cleaned_data["target_f"])

    def save(self):
        with update_store_after(self.unit.store):
            self.save_unit()
        if self.cleaned_data['comment']:
            super(SuggestionSubmitForm, self).save()


class AddSuggestionForm(SubmitFormMixin, forms.Form):
    target_f = MultiStringFormField(required=False, require_all_fields=False)

    def clean_target_f(self):
        target = multistring(self.cleaned_data["target_f"] or [u''])
        if self.unit.get_suggestions().filter(target_f=target).exists():
            self.add_error(
                "target_f",
                forms.ValidationError(
                    _("Suggestion '%s' already exists.",
                      target)))
        elif target == self.unit.target:
            self.add_error(
                "target_f",
                forms.ValidationError(
                    _("Suggestion '%s' equals to current unit target value.",
                      target)))
        else:
            return self.cleaned_data["target_f"]

    def save_unit(self):
        user = self.request_user
        review.get(Suggestion)().add(
            self.unit,
            self.cleaned_data["target_f"],
            user=user)

    def save(self):
        with update_store_after(self.unit.store):
            self.save_unit()


class SubmitForm(SubmitFormMixin, forms.Form):
    is_fuzzy = forms.BooleanField(
        initial=False,
        label=_("Needs work"))
    target_f = MultiStringFormField(required=False, require_all_fields=False)

    def clean_is_fuzzy(self):
        return self.data["is_fuzzy"] != "0"

    def save_unit(self):
        user = self.request_user
        target = multistring(self.cleaned_data["target_f"] or [u''])
        if target != self.unit.target:
            self.unit.target = self.cleaned_data["target_f"]
        if self.unit.target:
            if self.cleaned_data["is_fuzzy"]:
                self.unit.state = FUZZY
            else:
                self.unit.state = TRANSLATED
        else:
            self.unit.state = UNTRANSLATED
        self.unit.save(
            user=user,
            changed_with=SubmissionTypes.WEB)

    def save(self):
        with update_store_after(self.unit.store):
            self.save_unit()
