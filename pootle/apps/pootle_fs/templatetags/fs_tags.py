# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django import template

from pootle.core.delegate import upstream


register = template.Library()


@register.inclusion_tag('includes/upstream_link.html')
def upstream_link(project):
    upstream_provider = None
    if project.config.get("pootle.fs.upstream"):
        upstream_providers = upstream.gather(project.__class__)
        upstream_provider = upstream_providers.get(
            project.config["pootle.fs.upstream"])
    if not upstream_provider:
        return dict()
    return upstream_provider(project).context_data


@register.inclusion_tag('includes/upstream_link_short.html')
def upstream_link_short(project, location=None):
    upstream_provider = None
    if project.config.get("pootle.fs.upstream"):
        upstream_providers = upstream.gather(project.__class__)
        upstream_provider = upstream_providers.get(
            project.config["pootle.fs.upstream"])
    if not upstream_provider:
        return dict()
    return upstream_provider(project, location).context_data


@register.inclusion_tag('includes/fs/state_header.html')
def fs_state_header(project, fs, state, page_name, fetch_form):
    context = {}
    context["latest_hash"] = fs.latest_hash
    context["fs_type"] = fs.plugin.name
    context["fs_url"] = fs.plugin.fs_url
    context["project_code"] = project.code
    context["pootle_revision"] = project.directory.revisions.get(key="stats").value
    context["sync_revision"] = project.directory.revisions.get(key="fs").value
    context["state"] = state.changed
    context["tracked"] = len(state.resources.tracked)
    if project.config.get("pootle.fs.upstream"):
        upstream_providers = upstream.gather(fs.__class__)
        if project.config["pootle.fs.upstream"] in upstream_providers:
            upstream_provider = upstream_providers[
                project.config["pootle.fs.upstream"]](fs)
            context["upstream_url"] = upstream_provider.url
    context["untracked"] = (
        state.changed.get("fs_untracked", 0)
        + state.changed.get("pootle_untracked", 0)
        + state.changed.get("conflict_untracked", 0))
    context["unsynced"] = (
        state.changed.get("fs_staged", 0)
        + state.changed.get("fs_ahead", 0)
        + state.changed.get("pootle_staged", 0)
        + state.changed.get("pootle_ahead", 0)
        + state.changed.get("merge_fs_wins", 0)
        + state.changed.get("merge_pootle_wins", 0)
        + state.changed.get("remove", 0))
    context["conflicting"] = (
        state.changed.get("conflict_untracked", 0)
        + state.changed.get("conflict", 0))
    context["page_name"] = page_name
    context["project_url"] = project.pootle_path
    context["fetch_form"] = fetch_form
    return context
