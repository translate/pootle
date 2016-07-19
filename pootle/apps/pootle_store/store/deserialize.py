# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import io

from translate.storage.factory import getclass

from django.utils.functional import cached_property

from pootle.core.delegate import config, deserializers


class StoreDeserialization(object):
    """Calls configured deserializers for Store"""

    def __init__(self, store):
        self.store = store

    @property
    def project_deserializers(self):
        project = self.store.translation_project.project
        return (
            config.get(
                project.__class__,
                instance=project,
                key="pootle.core.deserializers")
            or [])

    @cached_property
    def deserializers(self):
        available_deserializers = deserializers.gather(
            self.store.translation_project.project.__class__)
        found_deserializers = []
        for deserializer in self.project_deserializers:
            found_deserializers.append(available_deserializers[deserializer])
        return found_deserializers

    def pipeline(self, data):
        if not self.deserializers:
            return data
        for deserializer in self.deserializers:
            data = deserializer(self.store, data).output
        return data

    def dataio(self, data):
        data = io.BytesIO(data)
        data.name = self.store.name
        return data

    def fromstring(self, data):
        data = self.dataio(data)
        return getclass(data)(data)

    def deserialize(self, data):
        return self.fromstring(self.pipeline(data))
