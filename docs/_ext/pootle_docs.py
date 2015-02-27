#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL2
# license. See the LICENSE file for a copy of the license and the AUTHORS file
# for copyright and authorship information.

"""Sphinx extension with custom stuff for Pootle docs."""


def setup(app):
    # Django :xxx: roles for intersphinx cross-references
    app.add_crossref_type(
        directivename="setting",
        rolename="setting",
        indextemplate="pair: %s; setting",
    )
    app.add_description_unit(
        directivename="django-admin",
        rolename="djadmin",
        indextemplate="pair: %s; django-admin command",
        #parse_node=parse_django_admin_node,
    )

    return {"parallel_read_safe": True}
