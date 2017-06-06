# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging

from django.utils.functional import cached_property

from pootle.core.decorators import persistent_property
from pootle.core.delegate import panels, scores
from pootle.core.helpers import (
    SIDEBAR_COOKIE_NAME, get_sidebar_announcements_context)
from pootle.core.utils.stats import (
    TOP_CONTRIBUTORS_CHUNK_SIZE, get_translation_states)
from pootle.i18n import formatter

from .base import PootleDetailView
from .display import ChecksDisplay, StatsDisplay


logger = logging.getLogger(__name__)


class PootleBrowseView(PootleDetailView):
    template_name = 'browser/index.html'
    table_fields = None
    is_store = False
    object_children = ()
    page_name = "browse"
    view_name = ""
    panel_names = ('children', )

    @property
    def checks(self):
        return ChecksDisplay(self.object).checks_by_category

    @property
    def path(self):
        return self.request.path

    @property
    def states(self):
        states = get_translation_states(self.object)
        stats = self.stats
        for state in states:
            if state["state"] == "untranslated":
                if stats["total"]:
                    stats[state["state"]] = state["count"] = (
                        stats["total"] - stats["fuzzy"] - stats["translated"])
            else:
                stats[state["state"]] = state["count"] = stats[state["state"]]
            if state.get("count"):
                state["count_display"] = formatter.number(state["count"])
                state["percent"] = round(
                    float(state["count"]) / stats["total"], 3)
                state["percent_display"] = formatter.percent(
                    state["percent"], "#,##0.0%")
        return states

    @cached_property
    def cache_key(self):
        return (
            "%s.%s.%s.%s.%s"
            % (self.page_name,
               self.view_name,
               self.object.data_tool.cache_key,
               self.show_all,
               self.request_lang))

    @property
    def show_all(self):
        return (
            self.request.user.is_superuser
            or "administrate" in self.request.permissions)

    @persistent_property
    def stats(self):
        stats = self.object.data_tool.get_stats(user=self.request.user)
        return StatsDisplay(self.object, stats=stats).stats

    @property
    def can_translate(self):
        return bool(
            not self.is_templates_context
            and (self.request.user.is_superuser
                 or self.language
                 or self.project))

    @property
    def can_translate_stats(self):
        return bool(
            not self.is_templates_context
            and (self.request.user.is_superuser
                 or self.language))

    @property
    def has_vfolders(self):
        return False

    @property
    def sidebar_announcements(self):
        return get_sidebar_announcements_context(
            self.request,
            (self.object, ))

    @persistent_property
    def has_disabled(self):
        return any(
            item.get('is_disabled')
            for item
            in self.object_children or [])

    def add_child_stats(self, items):
        stats = self.stats
        for item in items:
            if item["code"] in stats["children"]:
                item["stats"] = stats["children"][item["code"]]
            elif item["title"] in stats["children"]:
                item["stats"] = stats["children"][item["title"]]
        return items

    def get(self, *args, **kwargs):
        response = super(PootleBrowseView, self).get(*args, **kwargs)
        response.delete_cookie(SIDEBAR_COOKIE_NAME)
        return response

    @cached_property
    def scores(self):
        return scores.get(
            self.score_context.__class__)(
                self.score_context)

    @property
    def score_context(self):
        return self.object

    @persistent_property
    def top_scorer_data(self):
        chunk_size = TOP_CONTRIBUTORS_CHUNK_SIZE

        def scores_to_json(score):
            score["user"] = score["user"].to_dict()
            return score
        top_scorers = self.scores.display(
            limit=chunk_size,
            formatter=scores_to_json)
        return dict(
            items=list(top_scorers),
            has_more_items=len(self.scores.top_scorers) > chunk_size)

    @property
    def panels(self):
        _panels = panels.gather(self.__class__)
        for panel in self.panel_names:
            if panel in _panels:
                yield _panels[panel](self).content
            else:
                logger.warning("Unrecognized panel '%s'", panel)

    @property
    def is_templates_context(self):
        return self.object.pootle_path.startswith("/templates/")

    def get_context_data(self, *args, **kwargs):
        filters = {}
        if self.has_vfolders:
            filters['sort'] = 'priority'

        show_translation_links = (
            (self.request.user.is_superuser
             or self.language)
            and not self.object.pootle_path.startswith("/templates"))

        if show_translation_links:
            url_action_continue = self.object.get_translate_url(
                state='incomplete',
                **filters)
            url_action_fixcritical = self.object.get_critical_url(
                **filters)
            url_action_review = self.object.get_translate_url(
                state='suggestions',
                **filters)
            url_action_view_all = self.object.get_translate_url(state='all')
        else:
            url_action_continue = None
            url_action_fixcritical = None
            url_action_review = None
            url_action_view_all = None

        ctx = self.sidebar_announcements
        ctx.update(super(PootleBrowseView, self).get_context_data(*args, **kwargs))
        stats = self.stats.copy()
        del stats["children"]
        ctx.update(
            {'page': self.page_name,
             'checks': self.checks,
             'translation_states': self.states,
             'stats': stats,
             'can_translate': self.can_translate,
             'can_translate_stats': self.can_translate_stats,
             'cache_key': self.cache_key,
             'url_action_continue': url_action_continue,
             'url_action_fixcritical': url_action_fixcritical,
             'url_action_review': url_action_review,
             'url_action_view_all': url_action_view_all,
             'top_scorers': self.top_scorer_data,
             'has_disabled': self.has_disabled,
             'templates_context': self.is_templates_context,
             'panels': self.panels,
             'is_store': self.is_store,
             'browser_extends': self.template_extends})
        return ctx
