# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.template import Context, Template

from pootle.core.delegate import upstream
from pootle.core.plugin import provider
from pootle_project.models import Project


def _render_template(string, context=None):
    context = context or {}
    context = Context(context)
    return Template(string).render(context=context)


def _render_upstream(ctx):
    return _render_template(
        "{% load fs_tags %}{% upstream_link project %}",
        context=ctx)


def _render_upstream_short(ctx):
    return _render_template(
        "{% load fs_tags %}{% upstream_link_short project location %}",
        context=ctx)


@pytest.mark.django_db
def test_fs_tags_upstream(project0):

    # no upstreams and project not configured
    assert not _render_upstream(dict(project=project0)).strip()

    # still no upstreams
    project0.config["pootle.fs.upstream"] = "foostream"
    assert not _render_upstream(dict(project=project0)).strip()

    foocontext = dict(
        upstream_url="UPSTREAM URL",
        revision_url="REVISION URL",
        fs_path="FS PATH",
        latest_hash="LATEST HASH")

    class Foostream(object):

        def __init__(self, project):
            self.project = project

        @property
        def context_data(self):
            return foocontext

    @provider(upstream, sender=Project)
    def foostream_provider(**kwargs_):
        return dict(foostream=Foostream)

    rendered = _render_upstream(dict(project=project0))
    assert all([(v in rendered) for v in foocontext.values()])
    upstream.receivers = []


@pytest.mark.django_db
def test_fs_tags_upstream_short(project0):

    # no upstreams and project not configured
    assert not _render_upstream_short(dict(project=project0)).strip()

    # still no upstreams
    project0.config["pootle.fs.upstream"] = "foostream"
    assert not _render_upstream_short(dict(project=project0)).strip()

    foocontext = dict(
        upstream_url="UPSTREAM URL",
        revision_url="REVISION URL",
        latest_hash="LATEST HASH")

    class Foostream(object):

        def __init__(self, project, location=None):
            self.project = project

        @property
        def context_data(self):
            return foocontext

    @provider(upstream, sender=Project)
    def foostream_provider(**kwargs_):
        return dict(foostream=Foostream)

    rendered = _render_upstream_short(dict(project=project0))
    assert all([(v in rendered) for v in foocontext.values()])
    rendered = _render_upstream_short(
        dict(project=project0, location="FOO"))
    assert all([(v in rendered) for v in foocontext.values()])
    upstream.receivers = []
