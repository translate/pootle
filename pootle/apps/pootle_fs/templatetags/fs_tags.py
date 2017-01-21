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
