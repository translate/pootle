# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from redis.exceptions import ConnectionError

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.shortcuts import render

from django_rq.queues import get_failed_queue, get_queue
from django_rq.workers import Worker

from pootle.core.decorators import admin_required
from pootle.i18n import formatter
from pootle.i18n.gettext import ugettext as _, ungettext
from pootle_statistics.models import Submission
from pootle_store.models import Suggestion


def _format_numbers(numbers):
    for k in numbers.keys():
        numbers[k] = formatter.number(numbers[k])


def server_stats():
    User = get_user_model()
    result = cache.get("server_stats")
    if result is None:
        result = {}
        result['user_count'] = max(User.objects.filter(
            is_active=True).count()-2, 0)
        # 'default' and 'nobody' might be counted
        # FIXME: the special users should not be retuned with is_active
        result['submission_count'] = Submission.objects.count()
        result['pending_count'] = Suggestion.objects.pending().count()
        cache.set("server_stats", result, 86400)
    _format_numbers(result)
    return result


def rq_stats():
    queue = get_queue()
    failed_queue = get_failed_queue()
    try:
        workers = Worker.all(queue.connection)
    except ConnectionError:
        return None

    num_workers = len(workers)
    is_running = len(queue.connection.smembers(Worker.redis_workers_keys)) > 0
    if is_running:
        # Translators: this refers to the status of the background job worker
        status_msg = ungettext('Running (%d worker)', 'Running (%d workers)',
                               num_workers) % num_workers
    else:
        # Translators: this refers to the status of the background job worker
        status_msg = _('Stopped')

    result = {
        'job_count': queue.count,
        'failed_job_count': failed_queue.count,
        'is_running': is_running,
        'status_msg': status_msg,
    }

    return result


def checks():
    from django.core.checks.registry import registry

    return [e for e in registry.run_checks() if not e.is_silenced()]


@admin_required
def view(request):
    ctx = {
        'page': 'admin-dashboard',
        'server_stats': server_stats(),
        'rq_stats': rq_stats(),
        'checks': checks(),
    }
    return render(request, "admin/dashboard.html", ctx)
