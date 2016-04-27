# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

"""Sphinx extension with custom stuff for Pootle docs."""

from sphinx import addnodes
from sphinx.domains.std import Cmdoption


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
        parse_node=parse_django_admin_node,
    )

    app.add_directive('django-admin-option', Cmdoption)

    return {"parallel_read_safe": True}


def parse_django_admin_node(env, sig, signode):
    command = sig.split(' ')[0]
    env.ref_context['std:program'] = command
    signode += addnodes.desc_name(sig, sig)
    return command
