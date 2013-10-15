#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Zuza Software Foundation
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
from itertools import chain

from translate.filters.decorators import Category

from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.encoding import iri_to_uri
from django.utils.translation import ugettext_lazy as _

from taggit.models import TagBase, GenericTaggedItemBase

from pootle.core.markup import get_markup_filter_name, MarkupField
from pootle.core.url_helpers import get_editor_filter, split_pootle_path
from pootle_misc.checks import category_names, check_names
from pootle_misc.stats import add_percentages, get_processed_stats
from pootle_store.util import (OBSOLETE, completestatssum, statssum,
                               suggestions_sum)

from .decorators import get_from_cache_for_path


def slugify_tag_name(tag_name):
    """Convert the given tag name to a slug."""
    # Replace invalid characters for slug with hyphens.
    slug = re.sub(r'[^a-z0-9-]', "-", tag_name.lower())

    # Replace groups of hyphens with a single hyphen.
    slug = re.sub(r'-{2,}', "-", slug)

    # Remove leading and trailing hyphens.
    return slug.strip("-")


class Goal(TagBase):
    """Goal is a tag with a priority.

    Also it might be used to set shared goals across a translation project, for
    example a goal with all the files that must focus first their effor on all
    the translators (independently of the language they are translating to).

    It inherits from TagBase instead of Tag because that way it is possible to
    reduce the number of DB queries.
    """
    description_help_text = _('A description of this goal. This is useful to '
                              'give more information or instructions. Allowed '
                              'markup: %s', get_markup_filter_name())
    description = MarkupField(blank=True, help_text=description_help_text)

    # Priority goes from 1 to 10, being 1 the greater and 10 the lower.
    priority = models.IntegerField(verbose_name=_("Priority"), default=10,
                                   help_text=_("The priority for this goal."))

    # Tells if the goal is going to be shared across a project. This might be
    # seen as a 'virtual goal' because it doesn't apply to any real TP, but to
    # the templates one.
    project_goal_help_text = _("Designates that this is a project goal "
                               "(shared across all languages in the project).")
    project_goal = models.BooleanField(verbose_name=_("Project goal?"),
                                       default=False,
                                       help_text=project_goal_help_text)

    # Necessary for assigning and checking permissions.
    directory = models.OneToOneField('pootle_app.Directory', db_index=True,
                                     editable=False)

    class Meta:
        ordering = ["priority"]

    ############################ Properties ###################################

    @property
    def pootle_path(self):
        return "/goals/" + self.slug + "/"

    @property
    def goal_name(self):
        """Return the goal name, i.e. the name without the 'goal:' prefix.

        If this is a project goal, then is appended a text indicating that.
        """
        if self.project_goal:
            return "%s %s" % (self.name[5:], _("(Project goal)"))
        else:
            return self.name[5:]

    ############################ Methods ######################################

    @classmethod
    def get_goals_for_path(cls, pootle_path):
        """Return the goals applied to the stores in this path.

        If this is not the 'templates' translation project for the project then
        also return the 'project goals' applied to the stores in the
        'templates' translation project.

        :param pootle_path: A string with a valid pootle path.
        """
        # Putting the next imports at the top of the file causes circular
        # import issues.
        from pootle_app.models.directory import Directory
        from pootle_store.models import Store

        directory = Directory.objects.get(pootle_path=pootle_path)
        stores_pks = directory.stores.values_list("pk", flat=True)
        criteria = {
            'items_with_goal__content_type': ContentType.objects \
                                                        .get_for_model(Store),
            'items_with_goal__object_id__in': stores_pks,
        }
        tp = directory.translation_project

        if tp.is_template_project:
            # Return the 'project goals' applied to stores in this path.
            return cls.objects.filter(**criteria) \
                              .order_by('project_goal', 'priority').distinct()
        else:
            # Get the 'non-project goals' (aka regular goals) applied to stores
            # in this path.
            criteria['project_goal'] = False
            regular_goals = cls.objects.filter(**criteria).distinct()

            # Now get the 'project goals' applied to stores in the 'templates'
            # TP for this TP's project.
            template_tp = tp.project.get_template_translationproject()
            tpl_dir_path = "/%s/%s" % (template_tp.language.code,
                                       pootle_path.split("/", 2)[-1])

            try:
                tpl_dir = Directory.objects.get(pootle_path=tpl_dir_path)
            except Directory.DoesNotExist:
                project_goals = cls.objects.none()
            else:
                tpl_stores_pks =  tpl_dir.stores.values_list('pk', flat=True)
                criteria.update({
                    'project_goal': True,
                    'items_with_goal__object_id__in': tpl_stores_pks,
                })
                project_goals = cls.objects.filter(**criteria).distinct()

            return list(chain(regular_goals, project_goals))

    @classmethod
    def get_most_important_incomplete_for_path(cls, pootle_path):
        """Return the most important incomplete goal for this path or None.

        If this is not the 'templates' translation project for the project then
        also considers the 'project goals' applied to the stores in the
        'templates' translation project.

        The most important goal is the one with the lowest priority, or if more
        than a goal have the lower priority then the alphabetical order is
        taken in account.

        :param pootle_path: A string with a valid pootle path.
        """
        most_important = None
        for goal in cls.get_goals_for_path(pootle_path):
            if (most_important is None or
                goal.priority < most_important.priority or
                (goal.priority == most_important.priority and
                 goal.name < most_important.name)):
                if goal.get_incomplete_words_in_path(pootle_path):
                    most_important = goal

        return most_important

    def save(self, *args, **kwargs):
        # Putting the next import at the top of the file causes circular import
        # issues.
        from pootle_app.models.directory import Directory

        self.directory = Directory.objects.goals.get_or_make_subdir(self.slug)
        super(Goal, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        directory = self.directory
        super(Goal, self).delete(*args, **kwargs)
        directory.delete()

    def get_translate_url_for_path(self, pootle_path, **kwargs):
        """Return this goal's translate URL for the given path.

        :param pootle_path: A string with a valid pootle path.
        """
        lang, proj, dir_path, fn = split_pootle_path(pootle_path)
        return u''.join([
            reverse('pootle-tp-translate', args=[lang, proj, dir_path, fn]),
            get_editor_filter(goal=self.slug, **kwargs),
        ])

    def get_drill_down_url_for_path(self, pootle_path):
        """Return this goal's drill down URL for the given path.

        :param pootle_path: A string with a valid pootle path.
        """
        lang, proj, dir_path, filename = split_pootle_path(pootle_path)
        reverse_args = [lang, proj, self.slug, dir_path, filename]
        return reverse('pootle-tp-goal-drill-down', args=reverse_args)

    def get_stores_for_path(self, pootle_path):
        """Return the stores for this goal in the given pootle path.

        If this is a project goal then the corresponding stores in the path to
        that ones in the 'templates' TP for this goal are returned instead.

        :param pootle_path: A string with a valid pootle path.
        """
        # Putting the next imports at the top of the file causes circular
        # import issues.
        from pootle_store.models import Store
        from pootle_translationproject.models import TranslationProject

        lang, proj, dir_path, filename = split_pootle_path(pootle_path)

        # Get the translation project for this pootle_path.
        try:
            tp = TranslationProject.objects.get(language__code=lang,
                                                project__code=proj)
        except TranslationProject.DoesNotExist:
            return Store.objects.none()

        if self.project_goal and not tp.is_template_project:
            # Get the stores for this goal that are in the 'templates' TP.
            path_in_templates = tp.project.get_template_translationproject() \
                                          .pootle_path + dir_path + filename
            lookups = {
                'pootle_path__startswith': path_in_templates,
                'goals__in': [self],
            }
            template_stores_in_goal = Store.objects.filter(**lookups)

            # Putting the next imports at the top of the file causes circular
            # import issues.
            if tp.file_style == 'gnu':
                from pootle_app.project_tree import (get_translated_name_gnu as
                                                     get_translated_name)
            else:
                from pootle_app.project_tree import get_translated_name

            # Get the pootle path for the corresponding stores in the given TP
            # for those stores in the 'templates' TP.
            criteria = {
                'pootle_path__in': [get_translated_name(tp, store)[0]
                                    for store in template_stores_in_goal],
            }
        else:
            # This is a regular goal or the given TP is the 'templates' TP, so
            # just retrieve the goal stores on this TP.
            criteria = {
                'pootle_path__startswith': pootle_path,
                'goals__in': [self],
            }

        # Return the stores.
        return Store.objects.filter(**criteria)

    def get_children_for_path(self, pootle_path):
        """Return this goal stores and subdirectories in the given directory.

        The subdirectories returned are the ones that have any store for this
        goal just below them, or in any of its subdirectories.

        If this is a project goal then are returned instead:

        * The stores in the given directory that correspond to the goal stores
          in the corresponding directory in the 'templates' TP,
        * The subdirectories in the given directory that have stores that
          correspond to goal stores in the 'templates' TP.

        :param pootle_path: The pootle path for a :class:`Directory` instance.
        :return: Tuple with a stores list and a directories queryset.
        """
        # Putting the next import at the top of the file causes circular import
        # issues.
        from pootle_app.models.directory import Directory

        stores_in_dir = []
        subdir_paths = set()

        stores_for_path = self.get_stores_for_path(pootle_path)

        # Put apart the stores that are just below the directory from those
        # that are in subdirectories inside directory.
        for store in stores_for_path:
            trailing_path = store.pootle_path[len(pootle_path):]

            if "/" in trailing_path:
                # Store is in a subdirectory.
                subdir_name = trailing_path.split("/")[0] + "/"
                subdir_paths.add(pootle_path + subdir_name)
            else:
                # Store is in the directory.
                stores_in_dir.append(store)

        # Get the subdirectories that have stores for this goal.
        subdirs_in_dir = Directory.objects.filter(pootle_path__in=subdir_paths)

        # Return a tuple with stores and subdirectories in the given directory.
        return (stores_in_dir, subdirs_in_dir)

    def slugify(self, tag, i=None):
        return slugify_tag_name(tag)

    def delete_cache_for_path(self, translation_project, store):
        """Delete this goal cache for a given path and upper directories.

        The cache is deleted for the given path, for the directories between
        the given path and the translation project, and for the translation
        project itself.

        If the goal is a 'project goal' then delete the cache for all the
        translation projects in the same project for the specified translation
        project.

        :param translation_project: An instance of :class:`TranslationProject`.
        :param store: An instance of :class:`Store`.
        """
        CACHED_FUNCTIONS = ["get_raw_stats_for_path"]

        if self.project_goal:
            # Putting the next imports at the top of the file causes circular
            # import issues.
            from pootle_store.models import Store
            if translation_project.file_style == 'gnu':
                from pootle_app.project_tree import (get_translated_name_gnu as
                                                     get_translated_name)
            else:
                from pootle_app.project_tree import get_translated_name

            # Delete the cached stats for all the translation projects in the
            # same project.
            tps = translation_project.project.translationproject_set.all()
        else:
            # Just delete the cached stats for the given translation project.
            tps = [translation_project]

        # For each TP get the pootle_path for all the directories in between
        # the store and TP.
        keys = []
        for tp in tps:
            if tp != translation_project:
                store_path = get_translated_name(tp, store)[0]
                try:
                    tp_store = Store.objects.get(pootle_path=store_path)
                except Store.DoesNotExist:
                    # If there is no matching store in this TP then just jump
                    # to the next TP.
                    continue
            else:
                tp_store = store

            # Note: Not including tp_store in path_objs since we still don't
            # support including units in a goal.
            path_objs = chain([tp], tp_store.parent.trail())

            for path_obj in path_objs:
                for function_name in CACHED_FUNCTIONS:
                    keys.append(iri_to_uri(self.pootle_path + ":" +
                                           path_obj.pootle_path + ":" +
                                           function_name))
        cache.delete_many(keys)

    @get_from_cache_for_path
    def get_raw_stats_for_path(self, pootle_path):
        """Return a raw stats dictionary for this goal inside the given path.

        If this is a project goal the stats returned are the ones for the
        stores in the given path that correspond to the stores inside this goal
        that are present in the matching path in the 'templates' TP.

        :param pootle_path: A string with a valid pootle path.
        """
        # Retrieve the stores for this goal in the path.
        tp_stores_for_this_goal = self.get_stores_for_path(pootle_path)

        # Get and sum the stats for the stores.
        quickstats = statssum(tp_stores_for_this_goal)
        stats = get_processed_stats(add_percentages(quickstats))

        # Get and sum the suggestion counts for the stores.
        stats['suggestions'] = suggestions_sum(tp_stores_for_this_goal)

        return stats

    def get_failing_checks_for_path(self, pootle_path):
        """Return a failed quality checks list sorted by importance.

        :param pootle_path: A string with a valid pootle path.
        """
        checks = []
        path_stats = self.get_raw_stats_for_path(pootle_path)
        goal_stores_for_path = self.get_stores_for_path(pootle_path)
        property_stats = completestatssum(goal_stores_for_path)
        total = path_stats['total']['units']

        keys = property_stats.keys()
        keys.sort(reverse=True)

        for i, category in enumerate(keys):
            checks.append({
                'checks': []
            })

            if category != Category.NO_CATEGORY:
                checks[i].update({
                    'name': category,
                    'display_name': unicode(category_names[category]),
                })

            cat_keys = property_stats[category].keys()
            cat_keys.sort()

            for checkname in cat_keys:
                checkcount = property_stats[category][checkname]

                if total and checkcount:
                    check_display = unicode(check_names.get(checkname,
                                                            checkname))
                    check = {
                        'name': checkname,
                        'display_name': check_display,
                        'count': checkcount,
                    }
                    checks[i]['checks'].append(check)

        return checks

    def get_incomplete_words_in_path(self, pootle_path):
        """Return the number of incomplete words for this goal in the path.

        :param pootle_path: A string with a valid pootle path.
        """
        stats = self.get_raw_stats_for_path(pootle_path)
        return stats['untranslated']['words'] + stats['fuzzy']['words']


class ItemWithGoal(GenericTaggedItemBase):
    """Item that relates a Goal and an item with that goal."""
    # Set the custom 'Tag' model, which is 'Goal', to use as tag.
    tag = models.ForeignKey(Goal, related_name="items_with_goal")

    class Meta:
        verbose_name = _("Item with goal")
        verbose_name_plural = _("Items with goal")
