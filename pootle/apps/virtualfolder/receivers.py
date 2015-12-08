# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.db.models.signals import post_save
from django.dispatch import receiver

from pootle_store.models import Unit


@receiver(post_save, sender=Unit)
def relate_unit(sender, instance, created=False, **kwargs):
    """Add newly created units to the virtual folders they belong, if any.

    When a new store or translation project, or even a full project is added,
    some of their units might be matched by the filters of any of the
    previously existing virtual folders, so this signal handler relates those
    new units to the virtual folders they belong to, if any.
    """
    if not created:
        return

    pootle_path = instance.store.pootle_path

    for vf in VirtualFolder.objects.iterator():
        for location in vf.all_locations:
            if not pootle_path.startswith(location):
                continue

            for filename in vf.filter_rules.split(","):
                if pootle_path == "".join([location, filename]):
                    vf.units.add(instance)

                    # Create missing VirtualFolderTreeItem tree structure after
                    # adding this new unit.
                    vfolder_treeitem, created = \
                        VirtualFolderTreeItem.objects.get_or_create(
                            directory=instance.store.parent, vfolder=vf)

                    if not created:
                        # The VirtualFolderTreeItem already existed, so
                        # calculate again the stats up to the root.
                        vfolder_treeitem.update_all_cache()

                    break
