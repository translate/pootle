# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django import forms
from django.contrib.auth import get_user_model
from django.urls import reverse

from pootle.core.delegate import language_team, review
from pootle.core.forms import FormtableForm
from pootle.core.views.widgets import TableSelectMultiple
from pootle.i18n.gettext import ugettext_lazy as _
from pootle_store.constants import OBSOLETE, STATES_MAP
from pootle_store.models import Suggestion
from pootle_translationproject.models import TranslationProject

from .models import Language


User = get_user_model()

LANGUAGE_TEAM_ROLES = (
    ("member", _("Member")),
    ("submitter", _("Submitter")),
    ("reviewer", _("Reviewer")),
    ("admin", _("Administrator")))


class LanguageSpecialCharsForm(forms.ModelForm):

    class Meta(object):
        model = Language
        fields = ('specialchars',)


class LanguageTeamBaseAdminForm(forms.Form):

    @property
    def language_team(self):
        return language_team.get(self.language.__class__)(self.language)


class LanguageTeamFormtableForm(FormtableForm, LanguageTeamBaseAdminForm):
    pass


class LanguageTeamNewMemberSearchForm(LanguageTeamBaseAdminForm):
    q = forms.CharField(max_length=255)

    def __init__(self, *args, **kwargs):
        self.language = kwargs.pop("language")
        super(LanguageTeamNewMemberSearchForm, self).__init__(*args, **kwargs)

    def search(self):
        non_members = self.language_team.non_members
        return dict(
            results=[
                dict(id=int(m["id"]), text=m["username"])
                for m
                in (non_members.filter(username__contains=self.cleaned_data["q"])
                               .values("id", "username"))])


class RemoteSelectWidget(forms.Select):

    def render_options(self, selected_choices):
        return ""


class LanguageTeamAdminForm(LanguageTeamBaseAdminForm):
    rm_admins = forms.ModelMultipleChoiceField(
        label=_("Administrators"),
        widget=TableSelectMultiple(item_attrs=["username"]),
        required=False,
        queryset=User.objects.none())
    rm_reviewers = forms.ModelMultipleChoiceField(
        required=False,
        label=_("Reviewers"),
        widget=TableSelectMultiple(item_attrs=["username"]),
        queryset=User.objects.none())
    rm_submitters = forms.ModelMultipleChoiceField(
        required=False,
        label=_("Submitters"),
        widget=TableSelectMultiple(item_attrs=["username"]),
        queryset=User.objects.none())
    rm_members = forms.ModelMultipleChoiceField(
        required=False,
        label=_("Members"),
        widget=TableSelectMultiple(item_attrs=["username"]),
        queryset=User.objects.none())
    new_member = forms.ModelChoiceField(
        label=_("New member"),
        help_text=_("Add a user to this team"),
        required=False,
        queryset=User.objects.none(),
        initial=[],
        widget=RemoteSelectWidget(
            attrs={
                "data-s2-placeholder": _("Search for users to add"),
                'class': 'js-select2-remote js-s2-new-members'}))
    role = forms.ChoiceField(
        label=_("Role"),
        required=False,
        widget=forms.Select(
            attrs={'class': 'js-select2'}),
        choices=LANGUAGE_TEAM_ROLES)

    def __init__(self, *args, **kwargs):
        self.language = kwargs.pop("language")
        super(LanguageTeamAdminForm, self).__init__(*args, **kwargs)
        for role in self.language_team.roles:
            self.fields["rm_%ss" % role].queryset = getattr(
                self.language_team, "%ss" % role)
            self.fields["rm_%ss" % role].choices = [
                (item.id, item)
                for item in
                getattr(self.language_team, "%ss" % role)]
        self.fields["new_member"].widget.attrs["data-select2-url"] = reverse(
            "pootle-language-admin-team-new-members",
            kwargs=dict(language_code=self.language.code))
        self.fields["new_member"].queryset = self.language_team.non_members

    def clean(self):
        if any(self.errors):
            return
        no_role = (
            self.cleaned_data.get("new_member")
            and not self.cleaned_data.get("role"))
        if no_role:
            self.add_error(
                "role",
                forms.ValidationError(
                    _("Role is required when adding a new member")))

    def should_save(self):
        return (
            self.cleaned_data["new_member"] and self.cleaned_data["role"]
            or any(
                self.cleaned_data["rm_%ss" % role]
                for role in self.language_team.roles))

    def save(self):
        if self.cleaned_data["new_member"] and self.cleaned_data["role"]:
            self.language_team.add_member(
                self.cleaned_data["new_member"],
                self.cleaned_data["role"])
        else:
            for role in self.language_team.roles:
                if self.cleaned_data["rm_%ss" % role]:
                    for user in self.cleaned_data["rm_%ss" % role]:
                        self.language_team.remove_member(user)


class LanguageSuggestionAdminForm(LanguageTeamFormtableForm):
    action_field = "actions"
    search_field = "suggestions"
    action_choices = (
        ("", "----"),
        ("reject", _("Reject")),
        ("accept", _("Accept")))
    filter_suggester = forms.ChoiceField(
        label=_("Filter by suggester"),
        choices=(),
        required=False,
        widget=forms.Select(
            attrs={'class': 'js-select2 select2-language'}))
    filter_state = forms.ChoiceField(
        label=_("Filter by state"),
        required=False,
        choices=(
            [("", "-----")]
            + [(k, v)
               for k, v
               in STATES_MAP.items() if k != OBSOLETE]),
        widget=forms.Select(
            attrs={'class': 'js-select2 select2-language'}))
    filter_tp = forms.ModelChoiceField(
        label=_("Project"),
        required=False,
        queryset=TranslationProject.objects.none(),
        widget=forms.Select(
            attrs={'class': 'js-select2'}))
    suggestions = forms.ModelMultipleChoiceField(
        widget=TableSelectMultiple(
            item_attrs=[
                "unit_link",
                "unit_state",
                "unit",
                "target_f",
                "user",
                "creation_time",
                "project"]),
        required=False,
        queryset=Suggestion.objects.select_related(
            "unit",
            "unit__store",
            "unit__store__translation_project",
            "unit__store__translation_project__project").none())

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        self.language = kwargs.pop("language")
        super(LanguageSuggestionAdminForm, self).__init__(*args, **kwargs)
        self.fields["filter_suggester"].choices = self.filter_suggester_choices
        self.fields["filter_tp"].queryset = self.filter_tp_qs
        self.fields["suggestions"].queryset = self.suggestions_qs

    @property
    def filter_suggester_choices(self):
        suggesters = list(
            (username,
             ("%s (%s)" % (fullname, username)
              if fullname.strip()
              else username))
            for username, fullname
            in sorted(self.language_team.users_with_suggestions))
        return [("", "-----")] + suggesters

    @property
    def suggestions_qs(self):
        return self.language_team.suggestions.select_related("unit", "user").filter(
            unit__store__translation_project__project__disabled=False,
            unit__store__obsolete=False)

    @property
    def filter_tp_qs(self):
        tps = self.language.translationproject_set.exclude(
            project__disabled=True)
        tps = tps.filter(
            stores__unit__suggestion__state__name="pending")
        return tps.order_by("project__code").distinct()

    @property
    def suggestions_to_save(self):
        if not self.is_valid():
            return []
        return (
            self.fields["suggestions"].queryset
            if self.cleaned_data["select_all"]
            else self.cleaned_data["suggestions"])

    @property
    def suggestions_review(self):
        if not self.is_valid():
            return
        return review.get(Suggestion)(self.suggestions_to_save, self.user)

    def save(self):
        return (
            self.suggestions_review.accept(
                comment=self.cleaned_data["comment"])
            if self.cleaned_data["actions"] == "accept"
            else self.suggestions_review.reject(
                comment=self.cleaned_data["comment"]))

    def search(self):
        searched = super(LanguageSuggestionAdminForm, self).search()
        if self.cleaned_data.get("filter_suggester"):
            searched = searched.filter(
                user__username=self.cleaned_data["filter_suggester"])
        if self.cleaned_data.get("filter_tp"):
            searched = searched.filter(
                unit__store__translation_project=self.cleaned_data["filter_tp"])
        if self.cleaned_data.get("filter_state"):
            searched = searched.filter(
                unit__state=self.cleaned_data["filter_state"])
        return searched
