#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013-2014 Evernote Corporation
#
# This file is part of Pootle.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.


import time
from datetime import datetime, timedelta, time as datetime_time

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseBadRequest
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import timezone
from django.utils.html import escape
from django.utils.translation import ugettext_lazy as _

from pootle.core.decorators import admin_required
from pootle.models.user import CURRENCIES
from pootle_misc.util import ajax_required, jsonify
from pootle_statistics.models import ScoreLog

from .forms import UserRatesForm, PaidTaskForm
from .models import PaidTask, PaidTaskTypes


# Django field query aliases
LANG_CODE = 'translation_project__language__code'
LANG_NAME = 'translation_project__language__fullname'
PRJ_CODE = 'translation_project__project__code'
PRJ_NAME = 'translation_project__project__fullname'
INITIAL = 'old_value'
POOTLE_WORDCOUNT = 'unit__source_wordcount'

SCORE_TRANSLATION_PROJECT = 'submission__translation_project'

# field aliases
DATE = 'creation_time_date'

STAT_FIELDS = ['n1']
INITIAL_STATES = ['new', 'edit']


@admin_required
def evernote_reports(request):
    User = get_user_model()

    ctx = {
        'users': jsonify(map(
            lambda x: {'id': x.username, 'text': escape(x.formatted_name)},
            User.objects.hide_meta()
        )),
        'user_rates_form': UserRatesForm(),
        'paid_task_form': PaidTaskForm(),
    }

    return render_to_response('admin/reports.html', ctx,
                              context_instance=RequestContext(request))

@admin_required
def evernote_reports_detailed(request):
    username = request.GET.get('username', None)
    start_date = request.GET.get('start', None)
    end_date = request.GET.get('end', None)

    try:
        User = get_user_model()
        user = User.objects.get(username=username)
    except:
        user = ''

    [start, end] = get_date_interval(start_date, end_date)

    scores = []
    totals = {'translated': {}, 'reviewed': {}, 'total': 0}

    if user and start and end:
        scores = ScoreLog.objects \
            .select_related('submission__unit') \
            .filter(user=user,
                    creation_time__gte=start,
                    creation_time__lte=end) \
            .order_by('creation_time')

        scores = list(scores)

        for score in scores:
            translated, reviewed = score.get_paid_words()
            if translated:
                score.action = PaidTask.get_task_type_title(PaidTaskTypes.TRANSLATION)
                score.subtotal = score.rate * translated
                score.words = score.wordcount * (1 - score.get_similarity())
            elif reviewed:
                score.action = PaidTask.get_task_type_title(PaidTaskTypes.REVIEW)
                score.subtotal = score.review_rate * reviewed
                score.words = score.wordcount
            score.similarity = score.get_similarity() * 100

            if score.rate in totals['translated']:
                totals['translated'][score.rate]['words'] += translated
            else:
                totals['translated'][score.rate] = {'words': translated}

            if score.review_rate in totals['reviewed']:
                totals['reviewed'][score.review_rate]['words'] += reviewed
            else:
                totals['reviewed'][score.review_rate] = {'words': reviewed}

        totals['all'] = 0

        for rate, words in totals['translated'].items():
            totals['translated'][rate]['words'] = int(totals['translated'][rate]['words'] + 0.5)
            totals['translated'][rate]['subtotal'] = rate * totals['translated'][rate]['words']
            totals['all'] += totals['translated'][rate]['subtotal']

        for rate, words in totals['reviewed'].items():
            totals['reviewed'][rate]['words'] = int(totals['reviewed'][rate]['words'] + 0.5)
            totals['reviewed'][rate]['subtotal'] = rate * totals['reviewed'][rate]['words']
            totals['all'] += totals['reviewed'][rate]['subtotal']

        totals['all'] = totals['all']

    if user != '' and user.currency is None:
        user.currency = CURRENCIES[0][0]

    ctx = {
        'scores': scores,
        'user': user,
        'start': start,
        'end': end,
        'totals': totals,
        'utc_offset': start.strftime("%z"),
        'http_host': request.META['HTTP_HOST'],
    }

    return render_to_response('admin/detailed_reports.html', ctx,
                              context_instance=RequestContext(request))


def get_date_interval(start_date, end_date):
    if start_date:
        start = datetime.strptime(start_date, '%Y-%m-%d')
    else:
        start = timezone.now()

    if end_date:
        end = datetime.strptime(end_date, '%Y-%m-%d')
    else:
        end = timezone.now()

    if settings.USE_TZ:
        tz = timezone.get_default_timezone()
        start = timezone.make_aware(start, tz)
        end = timezone.make_aware(end, tz)

    start = start.replace(hour=0, minute=0, second=0)
    end = end.replace(hour=23, minute=59, second=59)

    return [start, end]


def get_max_month_datetime(dt):
    next_month = dt.replace(day=1) + timedelta(days=31)

    return next_month.replace(day=1, hour=23, minute=59, second=59) - \
        timedelta(days=1)


def get_min_month_datetime(dt):
    return dt.replace(day=1, hour=0, minute=0, second=0)


@ajax_required
@admin_required
def update_user_rates(request):
    form = UserRatesForm(request.POST)

    if form.is_valid():
        try:
            User = get_user_model()
            user = User.objects.get(username=form.cleaned_data['username'])
        except User.DoesNotExist:
            error_text = _("User %s not found" % form.cleaned_data['username'])

            return HttpResponseNotFound(jsonify({'msg': error_text}),
                                        content_type="application/json")

        user.currency = form.cleaned_data['currency']
        user.rate = form.cleaned_data['rate']
        user.review_rate = form.cleaned_data['review_rate']
        user.hourly_rate = form.cleaned_data['hourly_rate']

        scorelog_filter = {'user': user}
        paid_task_filter = scorelog_filter.copy()
        if form.cleaned_data['effective_from'] is not None:
            effective_from = form.cleaned_data['effective_from']
            scorelog_filter.update({
                'creation_time__gte': effective_from
            })
            paid_task_filter.update({
                'date__gte': effective_from
            })

        scorelog_query = ScoreLog.objects.filter(**scorelog_filter)
        scorelog_count = scorelog_query.count()

        paid_task_query = PaidTask.objects.filter(**paid_task_filter)
        paid_task_count = paid_task_query.count()

        scorelog_query.update(rate=user.rate, review_rate=user.review_rate)

        def get_task_rate_for(user, task_type):
            return {
                PaidTaskTypes.TRANSLATION: user.rate,
                PaidTaskTypes.REVIEW: user.review_rate,
                PaidTaskTypes.HOURLY_WORK: user.hourly_rate,
            }.get(task_type, 0)

        for task in paid_task_query:
            task.rate = get_task_rate_for(user, task.task_type)
            task.save()

        user.save()

        return HttpResponse(
            jsonify({
                'scorelog_count': scorelog_count,
                'paid_task_count': paid_task_count
            }), content_type="application/json")

    return HttpResponseBadRequest(jsonify({'html': form.errors}),
                                  content_type="application/json")


@ajax_required
@admin_required
def add_paid_task(request):
    form = PaidTaskForm(request.POST)
    if form.is_valid():
        form.save()

        return HttpResponse(jsonify({'result': form.instance.id}),
                            content_type="application/json")

    return HttpResponseBadRequest(jsonify({'html': form.errors}),
                                  content_type="application/json")


@ajax_required
@admin_required
def remove_paid_task(request, task_id=None):
    if request.method == 'DELETE':
        tasks = PaidTask.objects.filter(id=task_id)
        count = tasks.count()
        tasks.delete()

        return HttpResponse(jsonify({'removed': count}),
                            content_type="application/json")

    return HttpResponseBadRequest(
        jsonify({'error': _('Invalid request method')}),
        content_type="application/json"
    )


@ajax_required
@admin_required
def user_date_prj_activity(request):
    username = request.GET.get('username', None)
    start_date = request.GET.get('start', None)
    end_date = request.GET.get('end', None)

    try:
        User = get_user_model()
        user = User.objects.get(username=username)
    except:
        user = ''

    [start, end] = get_date_interval(start_date, end_date)

    json = {}
    user_dict = {
        'id': user.id,
        'username': user.username,
        'formatted_name': user.formatted_name,
        'currency': user.currency if user.currency else CURRENCIES[0][0],
        'rate': user.rate,
        'review_rate': user.review_rate,
        'hourly_rate': user.hourly_rate,
    } if user != '' else user

    json['meta'] = {'user': user_dict, 'start': start_date, 'end': end_date}
    if user != '':
        json['summary'] = get_summary(user, start, end)
        json['grouped'] = get_grouped_paid_words(user, start, end)
        json['paid_tasks'] = get_paid_tasks(user, start, end)
        json['daily'] = get_daily_activity(user, start, end)

    response = jsonify(json)

    return HttpResponse(response, content_type="application/json")


def get_daily_activity(user, start, end):
    result_translated = {
        'label': PaidTask.get_task_type_title(
            PaidTaskTypes.TRANSLATION),
        'data': {},
    }
    result_reviewed = {
        'label': PaidTask.get_task_type_title(
            PaidTaskTypes.REVIEW),
        'data': {},
    }

    result = {
        'data': [result_translated, result_reviewed],
        'max_day_score': 10,
        'min_ts': "%d" % (time.mktime(start.timetuple()) * 1000),
        'max_ts': "%d" % (time.mktime(end.timetuple()) * 1000),
        'nonempty': False,
    }

    scores = ScoreLog.objects \
                     .select_related('submission__unit') \
                     .filter(user=user,
                             creation_time__gte=start,
                             creation_time__lte=end) \
                     .order_by('creation_time')

    saved_ts = None
    current_day_score = 0
    for score in scores:
        score_time = score.creation_time
        if settings.USE_TZ:
            tz = timezone.get_default_timezone()
            score_time = timezone.make_naive(score_time, tz)
        date = score_time.date()
        ts = int((time.mktime(date.timetuple()) + 60*60*12) * 1000)

        translated, reviewed = score.get_paid_words()
        if translated or reviewed:
            if saved_ts != ts:
                saved_ts = ts
                result_reviewed['data'][ts] = 0
                result_translated['data'][ts] = 0
                if result['max_day_score'] < current_day_score:
                    result['max_day_score'] = current_day_score
                current_day_score = 0
            current_day_score += int(reviewed + translated)
            result['nonempty'] |= current_day_score > 0

            result_translated['data'][ts] += translated
            result_reviewed['data'][ts] += reviewed

    result_translated['data'] = sorted(result_translated['data'].items(),
                                       key=lambda x: x[0])
    result_reviewed['data'] = sorted(result_reviewed['data'].items(),
                                     key=lambda x: x[0])

    return result


def get_paid_tasks(user, start, end):
    result = []

    tasks = PaidTask.objects \
        .filter(user=user,
                date__gte=start,
                date__lte=end) \
        .order_by('pk')

    for task in tasks:
        result.append({
            'id': task.id,
            'description': task.description,
            'amount': task.amount,
            'type': task.task_type,
            'action': PaidTask.get_task_type_title(task.task_type),
            'rate': task.rate,
        })

    return result


def get_grouped_paid_words(user, start, end):
    result = []
    scores = ScoreLog.objects \
        .filter(user=user,
                creation_time__gte=start,
                creation_time__lte=end) \
        .order_by(SCORE_TRANSLATION_PROJECT)
    tp = None
    for score in scores:
        if tp != score.submission.translation_project:
            tp = score.submission.translation_project
            row = {
                'translation_project': u'%s / %s' %
                    (tp.project.fullname, tp.language.fullname),
                'score_delta': 0,
                'translated': 0,
                'translated_raw': 0,
                'reviewed': 0,
            }
            result.append(row)

        translated_words, reviewed_words = score.get_paid_words()
        row['translated'] += translated_words
        if translated_words:
            row['translated_raw'] += score.wordcount
        row['reviewed'] += reviewed_words
        row['score_delta'] += score.score_delta

    return sorted(result, key=lambda x: x['translation_project'])


def get_summary(user, start, end):
    rate = review_rate = None
    translation_month = review_month = None
    translated_row = reviewed_row = None

    translations = []
    reviews = []

    scores = ScoreLog.objects \
        .filter(user=user,
                creation_time__gte=start,
                creation_time__lte=end) \
        .order_by('creation_time')

    for score in scores:
        if (score.rate != rate or
            translation_month != score.creation_time.month):
            rate = score.rate
            translation_month = score.creation_time.month
            translated_row = {
                'type': PaidTaskTypes.TRANSLATION,
                'action': PaidTaskTypes.TRANSLATION,
                'amount': 0,
                'rate': score.rate,
                'start': score.creation_time,
                'end': score.creation_time,
            }
            translations.append(translated_row)
        if (score.review_rate != review_rate or
            review_month != score.creation_time.month):
            review_rate = score.review_rate
            review_month = score.creation_time.month
            reviewed_row = {
                'type': PaidTaskTypes.REVIEW,
                'action': PaidTaskTypes.REVIEW,
                'amount': 0,
                'rate': score.review_rate,
                'start': score.creation_time,
                'end': score.creation_time,
            }
            reviews.append(reviewed_row)

        translated_words, reviewed_words = score.get_paid_words()

        translated_row['amount'] += translated_words
        reviewed_row['amount'] += reviewed_words
        if translated_words > 0:
            translated_row['end'] = score.creation_time
        elif reviewed_row > 0:
            reviewed_row['end'] = score.creation_time

    for group in [translations, reviews]:
        for i, item in enumerate(group):
            if i == 0:
                item['start'] = start
            else:
                item['start'] = get_min_month_datetime(item['start'])

            if item['end'].month == end.month and item['end'].year == end.year:
                item['end'] = end
            else:
                item['end'] = get_max_month_datetime(item['end'])

    result = filter(lambda x: x['amount'] > 0, translations + reviews)
    result = sorted(result, key=lambda x: x['start'])

    tasks = PaidTask.objects \
        .filter(user=user,
                date__gte=start,
                date__lte=end) \
        .order_by('pk', 'task_type')

    for task in tasks:
        extended = None
        task_datetime = datetime.combine(
            task.date,
            datetime_time(hour=23, minute=59, second=59)
        )
        if settings.USE_TZ:
            tz = timezone.get_default_timezone()
            task_datetime = timezone.make_aware(task_datetime, tz)

        for item in result:
            if (item['start'] <= task_datetime <= item['end'] and
                task.task_type == item['action'] and
                item['rate'] == task.rate):
                extended = item
                break

        if extended is not None:
            extended['amount'] += task.amount
        else:
            insert_index = len(result)
            for index, item in enumerate(result):
                if item['start'] > task_datetime:
                    insert_index = index
                    break
            start = start.replace(hour=0, minute=0, second=0)
            end = end.replace(hour=23, minute=59, second=59)

            task_start = task_datetime.replace(day=1, hour=0, minute=0, second=0)
            task_end = get_max_month_datetime(task_datetime)
            if end <= task_end:
                task_end = end

            result.insert(insert_index, {
                'type': task.task_type,
                'action': task.task_type,
                'amount': task.amount,
                'rate': task.rate,
                'start': task_start,
                'end': task_end,
            })

    for item in result:
        item['type'] = item['action']
        item['action'] = PaidTask.get_task_type_title(item['action'])

    for item in result:
        item['start'] = item['start'].strftime('%Y-%m-%d')
        item['end'] = item['end'].strftime('%Y-%m-%d')

    return result


def users(request):
    User = get_user_model()
    json = list(
        User.objects.hide_meta()
                    .select_related('evernote_account')
                    .values('id', 'username', 'full_name')
    )
    response = jsonify(json)

    return HttpResponse(response, content_type="application/json")
