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

    def pre_delete(self, instance=None, objects=None):
        pass

    def post_delete(self, instance=None, objects=None, pre=None, result=None):
        pass

    def pre_create(self, instance=None, objects=None):
        pass

    def post_create(self, instance=None, objects=None, pre=None, result=None):
        pass

    def pre_update(self, instance=None, objects=None):
        pass

    def post_update(self, instance=None, objects=None, pre=None, result=None):
        pass

    def bulk_update(self, objects, fields=None):
        bulk_update(
            objects,
            update_fields=fields)

    def create(self, **kwargs):
        if "instance" in kwargs:
            pre = self.pre_create(instance=kwargs["instance"])
            result = kwargs["instance"].save()
            self.post_create(instance=kwargs["instance"], pre=pre, result=result)
        if "objects" in kwargs:
            pre = self.pre_delete(objects=kwargs["objects"])
            result = self.model.objects.bulk_create(
                kwargs["objects"])
            self.post_create(objects=kwargs["objects"], pre=pre, result=result)

    def delete(self, **kwargs):
        if "instance" in kwargs:
            pre = self.pre_delete(instance=kwargs["instance"])
            result = kwargs["instance"].delete()
            self.post_delete(instance=kwargs["instance"], pre=pre, result=result)
        if "objects" in kwargs:
            pre = self.pre_delete(objects=kwargs["objects"])
            result = kwargs["objects"].delete()
            self.post_delete(objects=kwargs["objects"], pre=pre, result=result)

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
        if "objects" in kwargs and kwargs["objects"] is not None:
            fields |= set(
                self.update_objects(
                    kwargs["objects"],
                    kwargs.get("updates"),
                    objects))
        return objects, fields

    def update_object_dict(self, objects, updates):
        to_fetch = self.objects_to_fetch(objects, updates)
        if to_fetch is None:
            return set()
        return set(
            self.update_objects(
                to_fetch.iterator(),
                updates,
                objects))

    def update(self, **kwargs):
        if kwargs.get("instance") is not None:
            pre = self.pre_update(instance=kwargs["instance"])
            result = kwargs["instance"].save()
            self.post_update(instance=kwargs["instance"], pre=pre, result=result)
        objects, fields = self.update_object_list(**kwargs)
        fields = (
            (fields or set())
            | self.update_object_dict(
                objects, kwargs.get("updates")))
        if objects:
            pre = self.pre_update(objects=objects)
            result = self.bulk_update(
                objects,
                fields=list(fields))
            self.post_update(objects=objects, pre=pre, result=result)
        return objects
