# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.


from bulk_update.helper import bulk_update


class BulkCRUD(object):

    model = None

    def __repr__(self):
        return (
            "<%s:%s>"
            % (self.__class__.__name__,
               str(self.model._meta)))

    @property
    def qs(self):
        return self.model.objects

    def bulk_update(self, objects, fields=None):
        bulk_update(
            objects,
            update_fields=fields)

    def create(self, **kwargs):
        if "instance" in kwargs:
            kwargs["instance"].save()
        if "objects" in kwargs:
            self.model.objects.bulk_create(
                kwargs["objects"])

    def delete(self, **kwargs):
        if "instance" in kwargs:
            kwargs["instance"].delete()
        if "objects" in kwargs:
            kwargs["objects"].delete()

    def update_object(self, obj, update):
        for k, v in update.items():
            setattr(obj, k, v)
            yield k

    def update_objects(self, to_update, updates, objects):
        if not updates:
            objects += list(to_update)
            to_update = []
        for obj in to_update:
            if updates.get(obj.pk):
                for field in self.update_object(obj, updates[obj.pk]):
                    yield field
            objects.append(obj)

    def objects_to_fetch(self, objects, updates):
        ids_to_fetch = (
            set((updates or {}).keys())
            - set(obj.id for obj in objects))
        if ids_to_fetch:
            return self.qs.filter(id__in=ids_to_fetch)

    def update_object_list(self, **kwargs):
        fields = (
            set(kwargs["update_fields"])
            if "update_fields" in kwargs
            else set())
        objects = []
        if "objects" in kwargs:
            fields |= set(
                self.update_objects(
                    kwargs["objects"],
                    kwargs.get("updates"),
                    objects))
        return objects, fields

    def update_object_dict(self, objects, updates):
        to_fetch = self.objects_to_fetch(
            objects, updates)
        return (
            set()
            if to_fetch is None
            else (
                set(self.update_objects(
                    to_fetch.iterator(),
                    updates,
                    objects))))

    def update(self, **kwargs):
        if kwargs.get("instance") is not None:
            kwargs["instance"].save()
        objects, fields = self.update_object_list(**kwargs)
        fields = (
            (fields or set())
            | self.update_object_dict(
                objects, kwargs.get("updates")))
        if objects:
            self.bulk_update(
                objects,
                fields=list(fields))
        return objects
