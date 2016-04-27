# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from redis.connection import ConnectionError

from django_rq.queues import get_queue
from django_rq.workers import Worker


def redis_is_running():
    """Checks is redis is running

    :returns: `True` if redis is running, `False` otherwise.
    """
    try:
        queue = get_queue()
        Worker.all(queue.connection)
    except ConnectionError:
        return False
    return True


def rq_workers_are_running():
    """Checks if there are any rq workers running

    :returns: `True` if there are rq workers running, `False` otherwise.
    """
    if redis_is_running():
        queue = get_queue()
        if len(queue.connection.smembers(Worker.redis_workers_keys)):
            return True
    return False
