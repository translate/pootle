# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging
import time


logger = logging.getLogger(__name__)


class Batch(object):

    def __init__(self, target, batch_size=10000):
        self.target = target
        self.batch_size = batch_size

    def batched_create(self, qs, create_method, reduces=True):
        complete = 0
        offset = 0
        total = qs.count()
        start = time.time()
        step = (
            self.batch_size
            if not reduces
            else 0)
        while True:
            complete += self.batch_size
            result = self.target.bulk_create(
                self.target.model(**create_method(*args))
                for args
                in self.iterate_qs(qs, offset))
            if not result:
                break
            logger.debug(
                "added %s/%s in %s seconds",
                min(complete, total),
                total,
                (time.time() - start))
            yield result
            if complete > total:
                break
            offset = offset + step

    def create(self, qs, create_method, reduces=True):
        created = 0
        for result in self.batched_create(qs, create_method, reduces):
            created += len(result)
        return created

    def iterate_qs(self, qs, offset):
        return qs[offset:offset + self.batch_size].iterator()
