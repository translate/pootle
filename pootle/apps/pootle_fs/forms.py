# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from collections import Counter, OrderedDict

from django import forms
from django.core.cache import cache
from django.utils.functional import cached_property
from django.utils.lru_cache import lru_cache
from django.utils.safestring import mark_safe

from pootle.core.decorators import persistent_property
from pootle.core.delegate import revision_updater
from pootle.core.forms import FormtableForm
from pootle.core.views.widgets import TableRowItem, TableSelectMultiple
from pootle.i18n.gettext import ugettext_lazy as _
from pootle_language.models import Language
from pootle_fs.utils import FSPlugin
from pootle_project.models import Project
from pootle_store.constants import POOTLE_WINS
from pootle_translationproject.models import TranslationProject

from .delegate import (
    fs_plugins, fs_translation_mapping_validator, fs_url_validator)


FS_CHOICES = (
    ("gnu", _("GNU-style"), "/po/<language_code>.<ext>"),
    ("non-gnu",
     _("non GNU-style"),
     "/<language_code>/<dir_path>/<filename>.<ext>"),
    ("django",
     _("Django-style"),
     "/locale/<lang_code>/LC_MESSAGES/<filename>.<ext>"),
    ("custom", _("Custom"), ""))


STATE_TITLES = dict(
    (("conflict_untracked",
      _("Untracked file with matching Pootle store (conflict_untracked)")),
     ("conflict",
      _("Pootle store and file have both changed (conflict)")),
     ("merge_fs_wins",
      _("Awaiting merge, file wins if there are conflicting units "
        "(merge_fs_wins)")),
     ("fs_ahead",
      _("Awaiting sync, File has changed (fs_ahead)")),
     ("pootle_ahead",
      _("Awaiting sync, Pootle store has changed (pootle_ahead)")),
     ("pootle_untracked",
      _("Untracked Pootle store (pootle_untracked)")),
     ("remove",
      _("Awaiting removal (remove)")),
     ("up_to_date",
      _("Up-to-date (up_to_date)")),
     ("fs_untracked",
      _("Untracked file (fs_untracked)"))))


class StateTableRowItem(TableRowItem):

    @property
    def title(self):
        return STATE_TITLES.get(self.value, self.value)


class ProjectStates(object):

    @lru_cache()
    def project_state(self, project_code, cache_key):
        cached = cache.get("fs.state.%s" % cache_key)
        if cached:
            return cached
        project = Project.objects.get(code=project_code)
        fs = FSPlugin(project)
        state = fs.state()
        from pootle.core.debug import timings
        with timings():
            cache.set("fs.state.%s" % cache_key, state)
        return state


project_states = ProjectStates()


class ProjectFSAdminForm(forms.Form):
    comment_field = None

    fs_type = forms.ChoiceField(
        label=_("Filesystem backend"),
        help_text=_("Select a filesystem backend"),
        choices=(),
        widget=forms.Select(
            attrs={'class': 'js-select2'}))
    fs_url = forms.CharField(
        label=_("Backend URL or path"),
        help_text=_(
            "The URL or path to your translation files"))
    translation_mapping_presets = forms.ChoiceField(
        required=False,
        choices=(
            [("", "-----"), ]
            + [(x[0], x[1]) for x in FS_CHOICES]),
        widget=forms.Select(
            attrs={'class': 'js-select2 js-select-fs-mapping'}))
    translation_mapping = forms.CharField(
        label=_("Translation path mapping"),
        help_text=_("Translation path mapping that maps the localisation "
                    "files on the filesystem to stores on Pootle."),
        widget=forms.TextInput(
            attrs={'class': 'js-select-fs-mapping-target'}))

    def should_save(self):
        return self.is_valid()

    @property
    def fs_type_choices(self):
        return (
            (plugin_type, plugin.name or plugin.fs_type)
            for plugin_type, plugin
            in fs_plugins.gather().items())

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop("project")
        super(ProjectFSAdminForm, self).__init__(*args, **kwargs)
        self.fields["fs_type"].choices = self.fs_type_choices
        self.fields["fs_url"].initial = self.project.config.get("pootle_fs.fs_url")
        self.fields["fs_type"].initial = (
            self.project.config.get("pootle_fs.fs_type"))
        translation_mapping = (
            self.project.config.get("pootle_fs.translation_mappings"))
        if translation_mapping:
            self.fields["translation_mapping"].initial = (
                translation_mapping.get("default"))

    @property
    def fs_path_validator(self):
        return fs_translation_mapping_validator.get()

    @cached_property
    def fs_plugin(self):
        if self.cleaned_data.get("fs_type"):
            return fs_plugins.gather()[self.cleaned_data["fs_type"]]

    @cached_property
    def fs_url_validator(self):
        validator = fs_url_validator.get(self.fs_plugin)
        return validator and validator()

    def clean(self):
        if not hasattr(self, "cleaned_data") or not self.cleaned_data:
            return
        if self.cleaned_data.get("translation_mapping"):
            try:
                self.fs_path_validator(
                    self.cleaned_data["translation_mapping"]).validate()
            except ValueError as e:
                self.add_error("translation_mapping", e)
        if not self.fs_url_validator or not self.cleaned_data.get("fs_url"):
            return
        try:
            self.fs_url_validator.validate(self.cleaned_data["fs_url"])
        except forms.ValidationError as e:
            self.add_error(
                "fs_url",
                forms.ValidationError(
                    "Incorrect URL or path ('%s') for plugin type '%s': %s"
                    % (self.cleaned_data.get("fs_url"),
                       self.cleaned_data.get("fs_type"),
                       e)))

    def save(self):
        self.project.config["pootle_fs.fs_type"] = self.cleaned_data["fs_type"]
        self.project.config["pootle_fs.fs_url"] = self.cleaned_data["fs_url"]
        self.project.config["pootle_fs.translation_mappings"] = dict(
            default=self.cleaned_data["translation_mapping"])


class LangMappingForm(forms.Form):
    remove = forms.BooleanField(required=False)
    pootle_code = forms.ModelChoiceField(
        Language.objects.all(),
        to_field_name="code",
        widget=forms.Select(attrs={'class': 'js-select2'}))
    fs_code = forms.CharField(
        max_length=32)

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop("project")
        existing_codes = kwargs.pop("existing_codes")
        super(LangMappingForm, self).__init__(*args, **kwargs)
        if existing_codes:
            excluded_codes = (
                [c for c in existing_codes if c != self.initial["pootle_code"]]
                if self.initial and self.initial.get("pootle_code")
                else existing_codes)
            self.fields["pootle_code"].queryset = (
                self.fields["pootle_code"].queryset.exclude(
                    code__in=excluded_codes))


class BaseLangMappingFormSet(forms.BaseFormSet):

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop("project")
        mappings = self.project.config.get("pootle.core.lang_mapping", {})
        if mappings:
            kwargs["initial"] = [
                dict(pootle_code=v, fs_code=k)
                for k, v in mappings.items()]
        super(BaseLangMappingFormSet, self).__init__(*args, **kwargs)

    @property
    def cleaned_mapping(self):
        mapping = OrderedDict()
        for mapped in self.cleaned_data:
            if not mapped or mapped["remove"]:
                continue
            mapping[mapped["fs_code"]] = mapped["pootle_code"].code
        return mapping

    def save(self):
        self.project.config["pootle.core.lang_mapping"] = self.cleaned_mapping

    def clean(self):
        if any(self.errors):
            return
        fs_counter = Counter([v["fs_code"] for v in self.cleaned_data if v])
        if set(fs_counter.values()) != set([1]):
            raise forms.ValidationError(
                _("Filesystem language codes must be unique"))
        pootle_counter = Counter([v["pootle_code"] for v in self.cleaned_data if v])
        if set(pootle_counter.values()) != set([1]):
            raise forms.ValidationError(
                _("Pootle language mappings must be unique"))

    def get_form_kwargs(self, index):
        kwargs = super(BaseLangMappingFormSet, self).get_form_kwargs(index)
        kwargs["project"] = self.project
        kwargs["existing_codes"] = (
            [i["pootle_code"] for i in self.initial]
            if self.initial
            else [])
        return kwargs


LangMappingFormSet = forms.formset_factory(
    LangMappingForm,
    formset=BaseLangMappingFormSet)


class ProjectFSStateBaseForm(FormtableForm):
    comment_field = None
    form_class = "pootle-fs-config-form"
    filter_state = forms.ChoiceField(
        choices=(),
        required=False,
        widget=forms.Select(
            attrs={'class': 'js-select2'}))
    filter_language = forms.ModelChoiceField(
        queryset=TranslationProject.objects.none(),
        required=False,
        widget=forms.Select(
            attrs={'class': 'js-select2'}))

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop("project")
        super(ProjectFSStateBaseForm, self).__init__(*args, **kwargs)
        self.fields["filter_state"].choices = getattr(self, "state_choices", ())
        self.fields["filter_language"].queryset = (
            self.project.translationproject_set.all())

    @cached_property
    def fs(self):
        return FSPlugin(self.project)

    @property
    def items_to_save(self):
        return (
            [x[0] for x in self.fields[self.search_field].queryset]
            if self.cleaned_data["select_all"]
            else self.cleaned_data[self.search_field])

    @property
    def state(self):
        return project_states.project_state(
            self.project.code, self.cache_key)

    def count_choices(self, choices):
        return len(choices)

    def search(self):
        if not self.is_valid():
            return self.fields[self.paginate_field].choices
        choices = []
        tp = (
            self.cleaned_data["filter_language"]
            if self.cleaned_data.get("filter_language")
            else None)
        state = (
            self.cleaned_data["filter_state"]
            if self.cleaned_data.get("filter_state")
            else None)
        for path, choice in self.fields[self.paginate_field].choices:
            if tp and not choice["pootle_path"].startswith(tp.pootle_path):
                continue
            if state and not choice["state_type"].value == state:
                continue
            choices.append((path, choice))
        return choices


class ProjectFSStateUntrackedForm(ProjectFSStateBaseForm):
    search_field = "untracked"
    paginate_field = "untracked"
    action_choices = (
        ("merge_fs", "Add tracking (merge on conflict, fs wins)"),
        ("merge_pootle", "Add tracking (merge on conflict, Pootle wins)"),
        ("add_fs", "Add tracking (overwrite Pootle from fs)"),
        ("add_pootle", "Add tracking (overwrite fs from Pootle)"),
        ("rm", "Remove both Pootle and filesystem store"))
    untracked = forms.MultipleChoiceField(
        required=False,
        widget=TableSelectMultiple(
            item_attrs=["pootle_path", "fs_path", "state_type"]),
        choices=[])

    def __init__(self, *args, **kwargs):
        super(ProjectFSStateUntrackedForm, self).__init__(*args, **kwargs)
        self.fields["untracked"].choices = self.untracked_choices

    @property
    def cache_key(self):
        return "pootle.fs.form.untracked.%s" % self.fs.cache_key

    @persistent_property
    def untracked_choices(self):
        ks = ["fs_path", "state_type"]
        result = []
        for assoc in self.state_untracked:
            kwargs = {k: getattr(assoc, k) for k in ks}
            if assoc.state_type in ["pootle_untracked", "conflict_untracked"]:
                kwargs["pootle_path"] = mark_safe(
                    '<a href="%s" target="_blank">%s</a>'
                    % (assoc.pootle_path, assoc.pootle_path))
            else:
                kwargs["pootle_path"] = assoc.pootle_path
            kwargs["class"] = kwargs["state_type"].replace("_", "-")
            kwargs["state_type"] = StateTableRowItem(kwargs["state_type"])
            result.append(("%s%s" % (assoc.state_type, assoc.pootle_path), kwargs))
        return result

    @property
    def state_choices(self):
        return (
            ("", ""),
            ("conflict_untracked", STATE_TITLES.get("conflict_untracked")),
            ("pootle_untracked", STATE_TITLES.get("pootle_untracked")),
            ("fs_untracked", STATE_TITLES.get("fs_untracked")))

    @property
    def state_untracked(self):
        state = self.state
        return (
            state["conflict_untracked"]
            + state["pootle_untracked"]
            + state["fs_untracked"])

    def save(self):
        paths = []
        states = []
        select_all = (
            self.cleaned_data[self.select_all_field]
            and not any(
                self.cleaned_data[k]
                for k
                in self.filter_fields))
        if not select_all:
            for item in self.items_to_save:
                # TODO: check still in same state?
                state_type = item.split("/")[0]
                states.append(state_type)
                pootle_path = "/".join(item.split("/")[1:])
                pootle_path = "/%s" % pootle_path
                paths.append(pootle_path)
            state = self.state.filter(pootle_paths=paths, states=states)
        else:
            state = self.state
        if self.cleaned_data["actions"] == "merge_fs":
            self.fs.resolve(state=state)
            self.fs.add(state=state)
        if self.cleaned_data["actions"] == "merge_pootle":
            self.fs.resolve(state=state, pootle_wins=True)
            self.fs.add(state=state)
        if self.cleaned_data["actions"] == "add_pootle":
            self.fs.resolve(state=state, merge=False, pootle_wins=True)
            self.fs.add(state=state)
        if self.cleaned_data["actions"] == "add_fs":
            self.fs.resolve(state=state, merge=False)
            self.fs.add(state=state)
        elif self.cleaned_data["actions"] == "rm":
            self.fs.rm(force=True, state=state)
        self.fs.expire_sync_cache()


class ProjectFSStateUnsyncedForm(ProjectFSStateBaseForm):
    search_field = "unsynced"
    paginate_field = "unsynced"
    action_choices = (
        ("unstage", "Unstage any actions"),
        ("sync", "Synchronize Pootle and the filesystem now"))
    unsynced = forms.MultipleChoiceField(
        required=False,
        widget=TableSelectMultiple(
            item_attrs=["pootle_path", "fs_path", "state_type"]),
        choices=[])

    def __init__(self, *args, **kwargs):
        super(ProjectFSStateUnsyncedForm, self).__init__(*args, **kwargs)
        self.fields["unsynced"].choices = self.unsynced_choices

    @property
    def cache_key(self):
        return "pootle.fs.form.unsynced.%s" % self.fs.cache_key

    @persistent_property
    def unsynced_choices(self):
        ks = ["pootle_path", "fs_path", "state_type"]
        result = []
        for assoc in self.state_unsynced:
            kwargs = {k: getattr(assoc, k) for k in ks}
            kwargs["class"] = kwargs["state_type"].replace("_", "-")
            kwargs["state_type"] = StateTableRowItem(kwargs["state_type"])
            if not assoc.kwargs.get("store_id"):
                kwargs["class"] = "%s %s" % (kwargs["class"], "no-store")
            if not assoc.kwargs.get("file_exists"):
                kwargs["class"] = "%s %s" % (kwargs["class"], "no-file")
            result.append(("%s%s" % (assoc.state_type, assoc.pootle_path), kwargs))
        return result

    @property
    def state_choices(self):
        return (
            ("", ""),
            ("remove", _("Files marked for removal")),
            ("pootle_ahead", _("Update from pootle")),
            ("fs_ahead", _("Update from filesystem")))

    @property
    def state_unsynced(self):
        return (
            self.state["remove"]
            + self.state["merge_fs_wins"]
            + self.state["merge_pootle_wins"]
            + self.state["pootle_staged"]
            + self.state["fs_staged"]
            + self.state["pootle_ahead"]
            + self.state["fs_ahead"])

    def save(self):
        paths = []
        states = []
        if not self.cleaned_data[self.select_all_field]:
            for item in self.items_to_save:
                state_type = item.split("/")[0]
                states.append(state_type)
                pootle_path = "/".join(item.split("/")[1:])
                pootle_path = "/%s" % pootle_path
                paths.append(pootle_path)
            state = self.state.filter(pootle_paths=paths, states=states)
        else:
            state = self.state
        if self.cleaned_data["actions"] == "unstage":
            self.fs.unstage(state=state)
        elif self.cleaned_data["actions"] == "sync":
            self.fs.sync(state=state)
        revision_updater.get(
            self.project.directory.__class__)(
                self.project.directory).update(keys=["fs"])


class ProjectFSStateConflictingForm(ProjectFSStateBaseForm):
    search_field = "conflicting"
    action_choices = (
        ("merge_fs", "Merge both, file wins if units conflict"),
        ("merge_pootle", "Merge both, Pootle store wins if units conflict"),
        ("add_fs", "Keep file and overwrite Pootle store"),
        ("add_pootle", "Keep Pootle store and overwrite file"),
        ("rm", "Remove both Pootle store and file"))
    paginate_field = "conflicting"
    conflicting = forms.MultipleChoiceField(
        required=False,
        widget=TableSelectMultiple(
            item_attrs=["pootle_path", "fs_path", "state_type"]),
        choices=[])

    def __init__(self, *args, **kwargs):
        super(ProjectFSStateConflictingForm, self).__init__(*args, **kwargs)
        self.fields["conflicting"].choices = self.conflicting_choices

    @property
    def conflicting_choices(self):
        ks = ["fs_path", "state_type"]
        result = []
        for assoc in self.state_conflicting:
            kwargs = {k: getattr(assoc, k) for k in ks}
            kwargs["pootle_path"] = mark_safe(
                '<a href="%s" target="_blank">%s</a>'
                % (assoc.pootle_path, assoc.pootle_path))
            kwargs["class"] = kwargs["state_type"].replace("_", "-")
            kwargs["state_type"] = StateTableRowItem(kwargs["state_type"])
            result.append(("%s%s" % (assoc.state_type, assoc.pootle_path), kwargs))
        return result

    @property
    def cache_key(self):
        return "pootle.fs.form.conflicting.%s" % self.fs.cache_key

    @property
    def state_choices(self):
        return (
            ("", ""),
            ("conflict_untracked", STATE_TITLES.get("conflict_untracked")),
            ("conflict", STATE_TITLES.get("conflict")))

    @property
    def state_conflicting(self):
        return self.state["conflict"] + self.state["conflict_untracked"]

    def save(self):
        paths = []
        states = []
        select_all = (
            self.cleaned_data[self.select_all_field]
            and not any(
                self.cleaned_data[k]
                for k
                in self.filter_fields))
        if not select_all:
            for item in self.items_to_save:
                # TODO: check still in same state?
                state_type = item.split("/")[0]
                states.append(state_type)
                pootle_path = "/".join(item.split("/")[1:])
                pootle_path = "/%s" % pootle_path
                paths.append(pootle_path)
            state = self.state.filter(pootle_paths=paths, states=states)
        else:
            state = self.state
        if self.cleaned_data["actions"] == "merge_fs":
            self.fs.resolve(state=state)
        if self.cleaned_data["actions"] == "merge_pootle":
            self.fs.resolve(state=state, pootle_wins=True)
        if self.cleaned_data["actions"] == "add_pootle":
            self.fs.resolve(state=state, merge=False, pootle_wins=True)
        if self.cleaned_data["actions"] == "add_fs":
            self.fs.resolve(state=state, merge=False)
        elif self.cleaned_data["actions"] == "rm":
            self.fs.rm(state=state)
        revision_updater.get(
            self.project.directory.__class__)(
                self.project.directory).update(keys=["fs"])


class ProjectFSStateTrackedForm(ProjectFSStateBaseForm):
    search_field = "tracked"
    paginate_field = "tracked"
    action_choices = (
        ("merge_fs", "Merge on conflict, fs wins"),
        ("merge_pootle", "Merge on conflict, Pootle wins"),
        ("overwrite_from_fs", "Overwrite Pootle on conflict, from fs"),
        ("overwrite_from_pootle", "Overwrite fs on conflict, from Pootle"),
        ("rm", "Remove both Pootle and filesystem store"))
    tracked = forms.MultipleChoiceField(
        required=False,
        widget=TableSelectMultiple(
            item_attrs=["pootle_path", "fs_path", "state_type"]),
        choices=[])

    def __init__(self, *args, **kwargs):
        super(ProjectFSStateTrackedForm, self).__init__(*args, **kwargs)
        self.fields["tracked"].choices = self.tracked_choices

    @property
    def cache_key(self):
        return "pootle.fs.form.untracked.%s" % self.fs.cache_key

    @persistent_property
    def tracked_choices(self):
        result = []
        for assoc in self.state.resources.tracked:
            state_type = "up_to_date"
            if not (assoc.last_sync_revision and assoc.last_sync_hash):
                if assoc.staged_for_removal:
                    state_type = "remove"
                elif assoc.file.file_exists:
                    if not assoc.file.store_exists:
                        state_type = "fs_staged"
                    elif assoc.staged_for_merge:
                        if assoc.resolve_conflict == POOTLE_WINS:
                            state_type = "merge_pootle_wins"
                        else:
                            state_type = "merge_fs_wins"
                    else:
                        if assoc.resolve_conflict == POOTLE_WINS:
                            state_type = "pootle_staged"
                        else:
                            state_type = "fs_staged"
                else:
                    if assoc.file.store_exists:
                        state_type = "pootle_staged"
            kwargs = {}
            kwargs["pootle_path"] = mark_safe(
                '<a href="%s" target="_blank">%s</a>'
                % (assoc.pootle_path, assoc.pootle_path))
            kwargs["fs_path"] = assoc.path
            kwargs["state_type"] = state_type
            kwargs["state_type"] = StateTableRowItem(kwargs["state_type"])
            result.append(
                ("%s%s"
                 % (kwargs["state_type"], assoc.pootle_path), kwargs))
        return result

    @property
    def state_choices(self):
        return (
            ("", ""),
            ("up_to_date", STATE_TITLES.get("up_to_date")),
            ("pootle_ahead", STATE_TITLES.get("pootle_ahead")),
            ("fs_ahead", STATE_TITLES.get("fs_ahead")))

    def save(self):
        paths = []
        states = []
        select_all = (
            self.cleaned_data[self.select_all_field]
            and not any(
                self.cleaned_data[k]
                for k
                in self.filter_fields))
        if not select_all:
            for item in self.items_to_save:
                # TODO: check still in same state?
                state_type = item.split("/")[0]
                states.append(state_type)
                pootle_path = "/".join(item.split("/")[1:])
                pootle_path = "/%s" % pootle_path
                paths.append(pootle_path)
            state = self.state.filter(pootle_paths=paths, states=states)
        else:
            state = self.state
        if self.cleaned_data["actions"] == "merge_fs":
            self.fs.resolve(state=state)
            self.fs.add(state=state)
        if self.cleaned_data["actions"] == "merge_pootle":
            self.fs.resolve(state=state, pootle_wins=True)
            self.fs.add(state=state)
        if self.cleaned_data["actions"] == "add_pootle":
            self.fs.resolve(state=state, merge=False, pootle_wins=True)
            self.fs.add(state=state, merge=False, pootle_wins=True)
        if self.cleaned_data["actions"] == "add_fs":
            self.fs.resolve(state=state, merge=False)
            self.fs.add(state=state, merge=False)
        elif self.cleaned_data["actions"] == "rm":
            self.fs.rm(force=True, state=state)
        revision_updater.get(
            self.project.directory.__class__)(
                self.project.directory).update(keys=["fs"])


class ProjectFSFetchForm(forms.Form):

    came_from = forms.ChoiceField(
        widget=forms.HiddenInput(),
        choices=(("tracked", "tracked"), ("untracked", "untracked")))

    fetch = forms.BooleanField(
        initial=True,
        widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop("project")
        page_name = kwargs.pop("page_name", None)
        super(ProjectFSFetchForm, self).__init__(*args, **kwargs)
        if page_name:
            self.fields["came_from"].initial = page_name

    def should_save(self):
        return self.is_valid()

    def save(self):
        fs = FSPlugin(self.project)
        fs.fetch()
