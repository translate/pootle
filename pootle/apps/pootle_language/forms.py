# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django import forms
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse

from pootle.core.delegate import language_team
from pootle.core.views.widgets import TableSelectMultiple
from pootle.i18n.gettext import ugettext_lazy as _

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

    @property
    def should_save(self):
        rm_members = [
            self.cleaned_data["rm_%ss" % role]
            for role in self.language_team.roles]
        return (
            (self.cleaned_data["new_member"]
             and self.cleaned_data["role"])
            or any(rm_members))


class LanguageTeamNewMemberSearchForm(LanguageTeamBaseAdminForm):
    q = forms.CharField(max_length=255)

    def __init__(self, *args, **kwargs):
        self.language = kwargs.pop("language")
        super(LanguageTeamNewMemberSearchForm, self).__init__(*args, **kwargs)

    def search(self):
        non_members = self.language_team.non_members
        return [
            dict(id=int(m["id"]), username=m["username"])
            for m
            in (non_members.filter(username__contains=self.cleaned_data["q"])
                           .values("id", "username"))]


class LanguageTeamAdminForm(LanguageTeamBaseAdminForm):
    rm_admins = forms.ModelMultipleChoiceField(
        label=_("Admins"),
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
        required=False,
        queryset=User.objects.none(),
        widget=forms.Select(
            attrs={
                'class': 'js-select2-remote'}))
    role = forms.ChoiceField(
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
                    "Role is required when adding a new member"))

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
