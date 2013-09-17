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

from django.db import models
from django.utils.translation import ugettext_lazy as _

from taggit.models import TagBase, GenericTaggedItemBase

from pootle.core.markup import get_markup_filter_name, MarkupField


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

    def slugify(self, tag, i=None):
        return slugify_tag_name(tag)


class ItemWithGoal(GenericTaggedItemBase):
    """Item that relates a Goal and an item with that goal."""
    # Set the custom 'Tag' model, which is 'Goal', to use as tag.
    tag = models.ForeignKey(Goal, related_name="items_with_goal")

    class Meta:
        verbose_name = _("Item with goal")
        verbose_name_plural = _("Items with goal")
