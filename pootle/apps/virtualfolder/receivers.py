# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.db.models.signals import post_save
from django.dispatch import receiver

from pootle_store.models import Store

from .models import VirtualFolder, VirtualFolderTreeItem


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


def add_store_to_vfolders(store):
    """For a given Unit check for membership of any VirtualFolders
    """
    pootle_path = store.pootle_path

    for vf in VirtualFolder.objects.iterator():
        store_added = False
        for location in vf.all_locations:
            if not pootle_path.startswith(location):
                continue

            for filename in vf.filter_rules.split(","):
                if pootle_path == "".join([location, filename]):
                    vf.stores.add(store)
                    store_added = True
                    break

            if store_added:
                break

        if store_added:
            update_vfolder_tree(vf, store)


@receiver(post_save, sender=VirtualFolder)
def vfolder_save_handler(sender, instance, created, **kwargs):
    """Remove Units from VirtualFolder when vfolder changes

    - Check the original VirtualFolder object's locations
    - Check the new VirtualFolders object's locations
    - Remove any units from the VirtualFolder that are only in original's
      locations and reset Unit priority
    - Update VirtualFolderTree for any Stores that may have been affected
    """
    locations = set()
    for location in instance.all_locations:
        for filename in instance.filter_rules.split(","):
            locations.add("".join([location, filename]))

    stores_we_want = Store.objects.none()
    for location in locations:
        stores_we_want = stores_we_want | Store.objects.filter(
            pootle_path__startswith=location)
    to_remove = list(
        instance.stores.exclude(
            pk__in=stores_we_want.values_list("pk", flat=True)))
    to_add = list(
        stores_we_want.exclude(
            pk__in=instance.stores.values_list("pk", flat=True)))
    instance.stores.remove(*to_remove)
    instance.stores.add(*to_add)
    for store in to_add:
        update_vfolder_tree(instance, store)
    for store in to_remove:
        store.set_priority()
    for store in stores_we_want:
        store.set_priority()


@receiver(post_save, sender=Store)
def vfolder_store_postsave_handler(**kwargs):
    """Match VirtualFolders to Unit and update Unit.priority

    - If unit was newly created, then check vfolders for membership
    - Update Unit priority from vfolder membership on Unit.save or create

    """
    instance = kwargs["instance"]
    created = kwargs.get("created", False)
    if created:
        add_store_to_vfolders(instance)
    instance.set_priority()
