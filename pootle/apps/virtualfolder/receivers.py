# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from pootle_store.models import Unit
from pootle_store.util import OBSOLETE

from .models import VirtualFolder, VirtualFolderTreeItem
from .signals import vfolder_post_save


def update_vfolder_tree(vf, store):
    """For a given VirtualFolder and Store update the VirtualFolderTreeItem
    """
    # Create missing VirtualFolderTreeItem tree structure for affected Stores
    # after adding or unobsoleting Units.
    vfolder_treeitem, created = (
        VirtualFolderTreeItem.objects.get_or_create(
            directory=store.parent, vfolder=vf))

    if not created:
        # The VirtualFolderTreeItem already existed, so
        # calculate again the stats up to the root.
        vfolder_treeitem.update_all_cache()


def add_unit_to_vfolders(unit):
    """For a given Unit check for membership of any VirtualFolders
    """
    pootle_path = unit.store.pootle_path

    for vf in VirtualFolder.objects.iterator():
        unit_added = False
        for location in vf.all_locations:
            if not pootle_path.startswith(location):
                continue

            for filename in vf.filter_rules.split(","):
                if pootle_path == "".join([location, filename]):
                    vf.units.add(unit)
                    unit_added = True
                    break

            if unit_added:
                break

        if unit_added:
            update_vfolder_tree(vf, unit.store)


@receiver(pre_save, sender=VirtualFolder)
def vfolder_unit_priority_presave_handler(sender, instance, **kwargs):
    """Remove Units from VirtualFolder when vfolder changes

    - Check the original VirtualFolder object's locations
    - Check the new VirtualFolders object's locations
    - Remove any units from the VirtualFolder that are only in original's
      locations and reset Unit priority
    - Update VirtualFolderTree for any Stores that may have been affected
    """

    if instance.id is None:
        return

    original = VirtualFolder.objects.get(pk=instance.pk)

    original_locations = set()
    new_locations = set()

    for location in original.all_locations:
        for filename in original.filter_rules.split(","):
            original_locations.add("".join([location, filename]))

    for location in instance.all_locations:
        for filename in instance.filter_rules.split(","):
            new_locations.add("".join([location, filename]))

    removed_locations = original_locations - new_locations

    stores_affected = set()
    for location in removed_locations:
        # reindex these units without this vfolder
        removed_units = (
            Unit.objects.filter(store__pootle_path__startswith=location,
                                vfolders=original))
        for unit in removed_units.iterator():
            unit.vfolders.remove(original)
            unit.set_priority()
            stores_affected.add(unit.store)

    for store in stores_affected:
        update_vfolder_tree(original, store)


@receiver(vfolder_post_save, sender=VirtualFolder)
def vfolder_unit_priority_handler(sender, instance, **kwargs):
    """Set Unit priorities for VirtualFolder members on change
    """
    for unit in instance.units.all():
        unit.set_priority()


@receiver(pre_save, sender=Unit)
def vfolder_unit_resurrected(sender, instance, created=False, **kwargs):
    """Update Unit VirtualFolder membership when Unit is *un*obsoleted
    """
    if instance.state == OBSOLETE:
        return
    try:
        Unit.objects.get(pk=instance.pk, state=OBSOLETE)
    except Unit.DoesNotExist:
        return
    add_unit_to_vfolders(instance)
    instance.set_priority()


@receiver(pre_save, sender=Unit)
def vfolder_unit_obsoleted(sender, instance, created=False, **kwargs):
    """Update Unit VirtualFolder membership when Unit is obsoleted
    """
    if instance.state != OBSOLETE:
        return
    try:
        Unit.objects.get(pk=instance.pk, state__gt=OBSOLETE)
    except Unit.DoesNotExist:
        return

    # grab the pk of any vfolder_treeitems
    vfolder_treeitems = instance.store.parent_vf_treeitems.values_list("pk")

    # clear Unit vfolder membership and update priority
    instance.vfolders.clear()
    instance.set_priority()

    # update the vfolder treeitems
    vf_qs = VirtualFolderTreeItem.objects.filter(pk__in=vfolder_treeitems)
    for vfolder_treeitem in vf_qs.iterator():
        vfolder_treeitem.update_all_cache()


@receiver(post_save, sender=Unit)
def vfolder_unit_postsave_handler(sender, instance, created=False, **kwargs):
    """Match VirtualFolders to Unit and update Unit.priority

    - If unit was newly created, then check vfolders for membership
    - Update Unit priority from vfolder membership on Unit.save or create

    """

    if created:
        add_unit_to_vfolders(instance)
    instance.set_priority()
