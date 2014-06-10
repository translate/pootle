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


from datetime import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseBadRequest
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from pootle.core.decorators import admin_required
from pootle_misc.util import ajax_required, jsonify
from pootle_statistics.models import Submission, SubmissionFields, ScoreLog

from .forms import UserRatesForm


# Django field query aliases
LANG_CODE = 'translation_project__language__code'
LANG_NAME = 'translation_project__language__fullname'
PRJ_CODE = 'translation_project__project__code'
PRJ_NAME = 'translation_project__project__fullname'
INITIAL = 'old_value'
POOTLE_WORDCOUNT = 'unit__source_wordcount'

# field aliases
DATE = 'creation_time_date'

STAT_FIELDS = ['n1']
INITIAL_STATES = ['new', 'edit']


@admin_required
def evernote_reports(request, context={}):
    User = get_user_model()
    cxt = context
    cxt.update({
        'users': map(
            lambda x: {'code': x.username, 'name': u'%s' % x },
            User.objects.hide_defaults()
        ),
        'user_rates_form': UserRatesForm(),
    })

    return render_to_response('admin/reports.html', cxt,
                              context_instance=RequestContext(request))

@admin_required
def evernote_reports_detailed(request):
    user = request.GET.get('user', None)
    start_date = request.GET.get('start', None)
    end_date = request.GET.get('end', None)

    try:
        User = get_user_model()
        user = User.objects.get(username=user)
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
                score.action = 1
                score.subtotal = score.rate * translated
                score.words = score.wordcount * (1 - score.get_similarity())
            elif reviewed:
                score.action = 2
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

    cxt = {
        'scores': scores,
        'user': user,
        'start': start,
        'end': end,
        'totals': totals,
        'utc_offset': start.strftime("%z"),
        'http_host': request.META['HTTP_HOST'],
    }

    return render_to_response('admin/detailed_reports.html', cxt,
                              context_instance=RequestContext(request))


def get_date_interval(start_date, end_date):
    if start_date:
        start = datetime.strptime(start_date, '%Y-%m-%d')
    else:
        start = datetime.now()

    if end_date:
        end = datetime.strptime(end_date, '%Y-%m-%d')
    else:
        end = datetime.now()

    if settings.USE_TZ:
        tz = timezone.get_default_timezone()
        start = timezone.make_aware(start, tz)
        end = timezone.make_aware(end, tz)

    start = start.replace(hour=0, minute=0, second=0)
    end = end.replace(hour=23, minute=59, second=59)

    return [start, end]


@ajax_required
@admin_required
def update_user_rates(request):
    form = UserRatesForm(request.POST)

    if form.is_valid():
        try:
            User = get_user_model()
            user = User.objects.get(username=form.cleaned_data['username'])
        except User.ObjectDoesNotExist:
            error_text = _("User %s not found" % form.cleaned_data['username'])

            return HttpResponseNotFound(jsonify({'msg': error_text}),
                                        content_type="application/json")

        user.currency = form.cleaned_data['currency']
        user.rate = form.cleaned_data['rate']
        user.review_rate = form.cleaned_data['review_rate']

        scorelog_filter = {'user': user}
        if form.cleaned_data['effective_from'] is not None:
            effective_from = form.cleaned_data['effective_from']
            scorelog_filter.update({
                'creation_time__gte': effective_from
            })
        scorelog_query = ScoreLog.objects.filter(**scorelog_filter)
        updated_count = scorelog_query.count()

        scorelog_query.update(rate=user.rate, review_rate=user.review_rate)
        user.save()

        return HttpResponse(jsonify({'updated_count': updated_count}),
                            content_type="application/json")


    return HttpResponseBadRequest(jsonify({'html': form.errors}),
                                  content_type="application/json")


@ajax_required
@admin_required
def user_date_prj_activity(request):
    user = request.GET.get('user', None)
    start_date = request.GET.get('start', None)
    end_date = request.GET.get('end', None)

    try:
        User = get_user_model()
        user = User.objects.get(username=user)
    except:
        user = ''

    [start, end] = get_date_interval(start_date, end_date)

    def get_item_stats(r={}):
        res = {}
        for f in STAT_FIELDS:
            res[f] = r[f] if (r.has_key(f) and r[f] is not None) else 0
        return res

    def create_total():
        return {
            INITIAL_STATES[0]: get_item_stats(),
            INITIAL_STATES[1]: get_item_stats()
        }

    json = {'total': create_total()}

    def aggregate(total, item):
        for f in STAT_FIELDS:
            total[f] += item[f]

    def add2total(total, subtotal):
        for t in ['new', 'edit']:
            aggregate(total[t], subtotal[t])

    if user:
        rr = Submission.objects.filter(
                submitter=user,
                creation_time__gte=start,
                creation_time__lte=end,
                field=SubmissionFields.TARGET
            ).extra(select={
                DATE: "DATE(`pootle_app_submission`.`creation_time`)",
            }).values(LANG_CODE, LANG_NAME, PRJ_CODE, PRJ_NAME, DATE, INITIAL) \
             .annotate(
                n1=Sum(POOTLE_WORDCOUNT),
            ).order_by(LANG_CODE, DATE)

        projects = {}
        res = {}

        saved_lang = None
        res_date = None
        lang_data = None

        for r in rr:
            cur_lang = r[LANG_CODE]
            cur_prj = r[PRJ_CODE]
            cur = get_item_stats(r)

            if cur_lang != saved_lang:
                if saved_lang != None and lang_data != None:
                    add2total(lang_data['total'], res_date['total'])
                    add2total(json['total'], lang_data['total'])

                saved_lang = cur_lang
                res[cur_lang] = {
                    'name': r[LANG_NAME],
                    'dates': [],
                    'sums': {},
                    'total': create_total()
                }

                lang_data = res[cur_lang]
                sums = lang_data['sums']

                saved_date = None

            if saved_date != r[DATE]:
                if saved_date is not None:
                    after_break = (r[DATE] - saved_date).days > 1
                    add2total(lang_data['total'], res_date['total'])

                else:
                    after_break = False

                saved_date = r[DATE]
                res_date = {
                    'date': datetime.strftime(saved_date, '%Y-%m-%d'),
                    'projects': {},
                    'after_break': after_break,
                    'total': create_total()
                }

                lang_data['dates'].append(res_date)

            if res_date is not None:
                if r[INITIAL] == '':
                    states = INITIAL_STATES
                else:
                    states = INITIAL_STATES[::-1]

                if sums.has_key(cur_prj):
                    aggregate(sums[cur_prj][states[0]], cur)
                else:
                    sums[cur_prj] = {
                        states[0]: get_item_stats(cur),
                        states[1]: get_item_stats()
                    }

                if res_date['projects'].has_key(cur_prj):
                    res_date['projects'][cur_prj].update({
                        states[0]: get_item_stats(cur)
                    })
                else:
                    res_date['projects'][cur_prj] = {
                        states[0]: get_item_stats(cur)
                    }

                aggregate(res_date['total'][states[0]], cur)
                projects[cur_prj] = r[PRJ_NAME]

        if lang_data is not None and res_date is not None:
            add2total(lang_data['total'], res_date['total'])
            add2total(json['total'], lang_data['total'])

        json['all_projects'] = projects
        json['results'] = res

    user_dict = {
        'username': user.username,
        'currency': user.currency,
        'rate': user.rate,
        'review_rate': user.review_rate,
    } if user != '' else user

    json['meta'] = {'user': user_dict, 'start': start_date, 'end': end_date}
    if user != '':
        json['scores'] = get_paid_words(user, start, end)
    response = jsonify(json)

    return HttpResponse(response, content_type="application/json")


def get_paid_words(user, start, end):
    rate = review_rate = row = None
    result = []

    scores = ScoreLog.objects \
        .filter(user=user,
                creation_time__gte=start,
                creation_time__lte=end) \
        .order_by('creation_time')

    for score in scores:
        if score.rate != rate or score.review_rate != review_rate:
            rate = score.rate
            review_rate = score.review_rate
            row = {
                'translated': 0,
                'reviewed': 0,
                'score_delta': 0,
                'rate': rate,
                'review_rate': review_rate,
                'start': score.creation_time.strftime('%Y-%m-%d'),
                'end': score.creation_time.strftime('%Y-%m-%d'),
            }
            result.append(row)

        translated_words, reviewed_words = score.get_paid_words()
        row['translated'] += translated_words
        row['reviewed'] += reviewed_words
        row['score_delta'] += score.score_delta
        row['end'] = score.creation_time.strftime('%Y-%m-%d')

    if result:
        result[0]['start'] = start.strftime('%Y-%m-%d')
        result[-1]['end'] = end.strftime('%Y-%m-%d')

    return result


def users(request):
    User = get_user_model()
    json = list(
        User.objects.hide_defaults()
                    .select_related('evernote_account')
                    .values('id', 'username', 'first_name', 'last_name')
    )
    response = jsonify(json)

    return HttpResponse(response, content_type="application/json")
