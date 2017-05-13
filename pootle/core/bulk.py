# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging

from bulk_update.helper import bulk_update


logger = logging.getLogger(__name__)


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

    def pre_update(self, instance=None, objects=None, values=None):
        pass

    def post_update(self, instance=None, objects=None, pre=None, result=None,
                    values=None):
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
            logger.debug(
                "[crud] Created (%s): %s",
                len(result),
                self.model.__name__)
            self.post_create(objects=kwargs["objects"], pre=pre, result=result)

    def delete(self, **kwargs):
        if "instance" in kwargs:
            pre = self.pre_delete(instance=kwargs["instance"])
            result = kwargs["instance"].delete()
            self.post_delete(instance=kwargs["instance"], pre=pre, result=result)
        if "objects" in kwargs:
            pre = self.pre_delete(objects=kwargs["objects"])
            result = kwargs["objects"].select_for_update().delete()
            logger.debug(
                "[crud] Deleted (%s): %s",
                str(result),
                self.model.__name__)
            self.post_delete(objects=kwargs["objects"], pre=pre, result=result)

    def update_object(self, obj, update):
        for k, v in update.items():
            if not getattr(obj, k) == v:
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
            return self.select_for_update(
                self.qs.filter(id__in=ids_to_fetch))

    def select_for_update(self, qs):
        return qs

    def update_object_list(self, **kwargs):
        fields = (
            set(kwargs["update_fields"])
            if kwargs.get("update_fields")
            else set())
        objects = []
        if "objects" in kwargs and kwargs["objects"] is not None:
            fields |= set(
                self.update_objects(
                    kwargs["objects"],
                    kwargs.get("updates"),
                    objects))
        return objects, (fields or None)

    def update_common_objects(self, ids, values):
        objects = self.select_for_update(self.model.objects).filter(id__in=ids)
        pre = self.pre_update(objects=objects, values=values)
        result = objects.select_for_update().update(**values)
        self.post_update(
            objects=objects, pre=pre, result=result, values=values)
        return result

    def all_updates_common(self, updates):
        values = {}
        first = True
        for item, _update in updates.items():
            if not first and len(values) != len(_update):
                return False
            for k, v in _update.items():
                if first:
                    values[k] = v
                    continue
                if k not in values or values[k] != v:
                    return False
            first = False
        return values

    def update_object_dict(self, objects, updates, fields):
        extra_fields = None
        to_fetch = self.objects_to_fetch(objects, updates)
        if to_fetch is None and not objects:
            return set()
        if not objects:
            common_updates = self.all_updates_common(updates)
            if common_updates:
                return self.update_common_objects(
                    updates.keys(),
                    common_updates)
        if to_fetch is not None:
            extra_fields = set(
                self.update_objects(
                    to_fetch.iterator(),
                    updates,
                    objects))
        if objects:
            pre = self.pre_update(objects=objects)
            if fields is not None:
                fields = list(
                    fields | extra_fields
                    if extra_fields is not None
                    else fields)
            result = self.bulk_update(
                objects,
                fields=fields)
            self.post_update(objects=objects, pre=pre, result=result)
        return result

    def update_object_instance(self, instance):
        pre = self.pre_update(instance=instance)
        result = instance.save()
        self.post_update(instance=instance, pre=pre, result=result)
        return result

    def update(self, **kwargs):
        if kwargs.get("instance") is not None:
            return self.update_object_instance(kwargs["instance"])
        objects, fields = self.update_object_list(**kwargs)
        updated = self.update_object_dict(objects, kwargs.get("updates"), fields)
        total = (updated or 0) + len(objects)
        logger.debug(
            "[crud] Updated (%s): %s %s",
            total,
            self.model.__name__,
            "%s" % (", ".join(fields or [])))
        return total
