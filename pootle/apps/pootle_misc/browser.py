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

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _, ungettext

from pootle_misc.stats import get_raw_stats, stats_descriptions


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
        'id': 'priority',
        'class': 'stats-number sorttable_numeric',
        # Translators: Heading representing the priority for a goal
        'display_name': _("Priority"),
    },
    {
        'id': 'progress',
        'class': 'stats',
        # Translators: noun. The graphical representation of translation status
        'display_name': _("Progress"),
    },
    {
        'id': 'total',
        'class': 'stats-number sorttable_numeric',
        # Translators: Heading representing the total number of words of a file
        # or directory
        'display_name': _("Total"),
    },
    {
        'id': 'need-translation',
        'class': 'stats-number sorttable_numeric',
        'display_name': _("Need Translation"),
    },
    {
        'id': 'suggestions',
        'class': 'stats-number sorttable_numeric',
        # Translators: The number of suggestions pending review
        'display_name': _("Suggestions"),
    },
    {
        'id': 'activity',
        'class': 'stats',
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
    """Template variables for each row in the table.

    :func:`make_directory_item` and :func:`make_store_item` will add onto these
    variables.
    """
    action = path_obj.pootle_path
    try:
        stats = get_raw_stats(path_obj, include_suggestions=True)
        info = {
            'href': action,
            'href_all': path_obj.get_translate_url(),
            'href_todo': path_obj.get_translate_url(state='incomplete'),
            'href_sugg': path_obj.get_translate_url(state='suggestions'),
            'stats': stats,
            'tooltip': _('%(percentage)d%% complete',
                         {'percentage': stats['translated']['percentage']}),
            'title': path_obj.name,
        }

        errors = stats.get('errors', 0)
        if errors:
            info['errortooltip'] = ungettext('Error reading %d file',
                                             'Error reading %d files',
                                             errors, errors)

        info.update(stats_descriptions(stats))
    except IOError as e:
        info = {
            'href': action,
            'errortooltip': e.strerror,
            'data': {
                'errors': 1,
            },
            'title': path_obj.name,
        }

    return info


def make_directory_item(directory):
    item = make_generic_item(directory)
    item.update({
        'icon': 'folder',
        'isdir': True,
    })
    return item


def make_store_item(store):
    item = make_generic_item(store)
    item.update({
        'icon': 'file',
        'isfile': True,
    })
    return item


def get_parent_item_list(directory):
    """Return a list with the parent directory item.

    If the parent directory is the directory for a language or a project then
    return an empty list.
    """
    parent_dir = directory.parent

    if not (parent_dir.is_language() or parent_dir.is_project()):
        return [{'title': u'..', 'href': parent_dir}]
    else:
        return []


def get_children(directory):
    """Return a list of children directories and stores for this ``directory``,
    and also the parent directory.

    The elements of the list are dictionaries which keys are populated after in
    the templates.
    """
    parent = get_parent_item_list(directory)

    directories = [make_directory_item(child_dir)
                   for child_dir in directory.child_dirs.iterator()]

    stores = [make_store_item(child_store)
              for child_store in directory.child_stores.iterator()]

    return parent + directories + stores


################################ Goal specific ################################

def make_goal_item(goal, pootle_path):
    """Create the item row for a goal."""
    try:
        stats = goal.get_raw_stats_for_path(pootle_path)
        info = {
            'href_all': goal.get_translate_url_for_path(pootle_path),
            'href_todo': goal.get_translate_url_for_path(pootle_path,
                                                         state='incomplete'),
            'href_sugg': goal.get_translate_url_for_path(pootle_path,
                                                         state='suggestions'),
            'stats': stats,
            'tooltip': _('%(percentage)d%% complete',
                         {'percentage': stats['translated']['percentage']}),
        }

        errors = stats.get('errors', 0)
        if errors:
            msg = ungettext('Error reading %d file', 'Error reading %d files',
                            errors, errors)
            info['errortooltip'] = msg

        info.update(stats_descriptions(stats))
    except IOError as e:
        info = {
            'errortooltip': e.strerror,
            'data': {
                'errors': 1,
            },
        }

    info.update({
        'href': goal.get_drill_down_url_for_path(pootle_path),
        'isdir': True,
        'priority': goal.priority,
        'title': goal.goal_name,
    })
    return info


def make_goal_dir_item(directory, goal):
    """Template variables for each row in the table."""
    try:
        stats = goal.get_raw_stats_for_path(directory.pootle_path)
        item = {
            'href_all': goal.get_translate_url_for_path(directory.pootle_path),
            'href_todo': goal.get_translate_url_for_path(directory.pootle_path,
                                                         state='incomplete'),
            'href_sugg': goal.get_translate_url_for_path(directory.pootle_path,
                                                         state='suggestions'),
            'stats': stats,
            'tooltip': _('%(percentage)d%% complete',
                         {'percentage': stats['translated']['percentage']}),
        }

        errors = stats.get('errors', 0)
        if errors:
            msg = ungettext('Error reading %d file', 'Error reading %d files',
                            errors, errors)
            item['errortooltip'] = msg

        item.update(stats_descriptions(stats))
    except IOError as e:
        item = {
            'errortooltip': e.strerror,
            'data': {
                'errors': 1,
            },
        }

    item.update({
        'href': goal.get_drill_down_url_for_path(directory.pootle_path),
        'title': directory.name,
        'icon': 'folder',
        'isdir': True,
    })
    return item


def make_goal_store_item(store, goal):
    item = make_store_item(store)
    item.update({
        'href': goal.get_drill_down_url_for_path(store.pootle_path),
        'href_all': goal.get_translate_url_for_path(store.pootle_path),
        'href_todo': goal.get_translate_url_for_path(store.pootle_path,
                                                     state='incomplete'),
        'href_sugg': goal.get_translate_url_for_path(store.pootle_path,
                                                     state='suggestions'),
    })
    return item


def get_goal_parent_item_list(directory, goal):
    """Return a list with the parent directory item in a drill down view.

    If the parent directory is the directory for a language or a project then
    return an item pointing at the goals tab.
    """
    if directory.parent.is_language() or directory.parent.is_project():
        url_kwargs = {
            'language_code': directory.translation_project.language.code,
            'project_code': directory.translation_project.project.code,
            'dir_path': directory.path,
        }
        return [{
            'title': u'..',
            'href': reverse('pootle-tp-goals', kwargs=url_kwargs),
        }]
    else:
        parent_path = directory.parent.pootle_path
        return [{
            'title': u'..',
            'href': goal.get_drill_down_url_for_path(parent_path),
        }]


def get_goal_children(directory, goal):
    """Return a list of children directories and stores for this ``directory``
    that in the provided stores,
    and also the parent directory.

    The elements of the list are dictionaries which keys are populated after
    in the templates.
    """
    # Get the stores and subdirectories for this goal in the current directory.
    dir_stores, dir_subdirs = goal.get_children_for_path(directory.pootle_path)

    # Now get and return the items for those stores and subdirectories.
    parent = get_goal_parent_item_list(directory, goal)

    directories = [make_goal_dir_item(child_dir, goal)
                   for child_dir in dir_subdirs]

    stores = [make_goal_store_item(child_store, goal)
              for child_store in dir_stores]

    return parent + directories + stores
