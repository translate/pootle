#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2013 Zuza Software Foundation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# Pootle is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# Pootle; if not, see <http://www.gnu.org/licenses/>.

import re

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _


ITEM_CODE_RE = re.compile("[\.@]")  # This must match the regexp in JS code.


HEADING_CHOICES = [
    {
        'id': 'name',
        'class': 'stats',
        'display_name': _("Name"),
    },
    {
        'id': 'project',
        'class': 'stats',
        'display_name': _("Project"),
    },
    {
        'id': 'language',
        'class': 'stats',
        'display_name': _("Language"),
    },
    {
        'id': 'progress',
        'class': 'stats',
        # Translators: noun. The graphical representation of translation status
        'display_name': _("Progress"),
    },
    {
        'id': 'total',
        'class': 'stats-number sorttable_numeric when-loaded',
        # Translators: Heading representing the total number of words of a file
        # or directory
        'display_name': _("Total"),
    },
    {
        'id': 'need-translation',
        'class': 'stats-number sorttable_numeric when-loaded',
        'display_name': _("Need Translation"),
    },
    {
        'id': 'suggestions',
        'class': 'stats-number sorttable_numeric when-loaded',
        # Translators: The number of suggestions pending review
        'display_name': _("Suggestions"),
    },
    {
        'id': 'critical',
        'class': 'stats-number sorttable_numeric when-loaded',
        'display_name': _("Critical"),
    },
    {
        'id': 'last-updated',
        'class': 'stats sorttable_numeric when-loaded',
        'display_name': _("Last updated"),
    },
    {
        'id': 'activity',
        'class': 'stats sorttable_numeric when-loaded',
        'display_name': _("Last Activity"),
    },
    # NOTE: 'tags' heading is not included here on purpose to avoid the
    # creation of such column in the table. Tags are instead shown in a new row
    # that keeps the same color scheme.
]


def get_table_headings(choices):
    """Filter the list of available table headings to the given `choices`."""
    return filter(lambda x: x['id'] in choices, HEADING_CHOICES)


def make_generic_item(path_obj):
    """Template variables for each row in the table."""
    return {
        'href': path_obj.get_absolute_url(),
        'href_all': path_obj.get_translate_url(),
        'href_todo': path_obj.get_translate_url(state='incomplete'),
        'href_sugg': path_obj.get_translate_url(state='suggestions'),
        'href_critical': path_obj.get_critical_url(),
        'title': path_obj.name,
        'code': ITEM_CODE_RE.sub("-", path_obj.code),
    }


def make_directory_item(directory):
    item = make_generic_item(directory)
    item.update({
        'icon': 'folder',
    })
    return item


def make_store_item(store):
    item = make_generic_item(store)
    item.update({
        'icon': 'file',
    })
    return item


def get_parent(directory):
    parent_dir = directory.parent

    if not (parent_dir.is_language() or parent_dir.is_project()):
        return {
            'icon': 'folder-parent',
            'title': _("Back to parent folder"),
            'href': parent_dir.get_absolute_url()
        }
    else:
        return None


def make_project_item(translation_project):
    item = make_generic_item(translation_project)
    item.update({
        'icon': 'project',
        'title': translation_project.project.name,
    })
    return item


def make_language_item(translation_project):
    item = make_generic_item(translation_project)
    item.update({
        'icon': 'language',
        'title': translation_project.language.name,
    })
    return item


def make_xlanguage_item(resource_obj):
    translation_project = resource_obj.translation_project
    item = make_generic_item(resource_obj)
    item.update({
        'icon': 'language',
        'code': translation_project.language.code,
        'title': translation_project.language.name,
    })
    return item


def make_project_list_item(project):
    item = make_generic_item(project)
    item.update({
        'icon': 'project',
        'title': project.fullname,
    })
    return item


def get_children(directory):
    """Return a list of children directories and stores for this ``directory``.

    The elements of the list are dictionaries which keys are populated after in
    the templates.
    """
    directories = [make_directory_item(child_dir)
                   for child_dir in directory.child_dirs.iterator()]

    stores = [make_store_item(child_store)
              for child_store in directory.child_stores.iterator()]

    return directories + stores
