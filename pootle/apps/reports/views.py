# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.


import calendar
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, DetailView

from accounts.models import CURRENCIES
from pootle.core.decorators import admin_required
from pootle.core.http import (JsonResponse, JsonResponseBadRequest,
                              JsonResponseNotFound)
from pootle.core.log import PAID_TASK_ADDED, PAID_TASK_DELETED, log
from pootle.core.utils.timezone import make_aware, make_naive
from pootle.core.views.mixins import (AjaxResponseMixin, NoDefaultUserMixin,
                                      TestUserFieldMixin, UserObjectMixin)
from pootle.i18n.gettext import ugettext_lazy as _
from pootle_misc.util import (ajax_required, get_date_interval,
                              get_max_month_datetime, import_func)
from pootle_statistics.models import ScoreLog

from .forms import PaidTaskForm, UserRatesForm
from .models import PaidTask, PaidTaskTypes, ReportActionTypes
from .utils import get_grouped_word_stats


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


class UserStatsView(NoDefaultUserMixin, UserObjectMixin, DetailView):
    template_name = 'user/stats.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(UserStatsView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(UserStatsView, self).get_context_data(**kwargs)
        now = make_aware(datetime.now())
        ctx.update({
            'now': now.strftime('%Y-%m-%d %H:%M:%S'),
        })
        if self.object.rate > 0:
            ctx.update({
                'paid_task_form': PaidTaskForm(user=self.object),
                'paid_task_types': PaidTaskTypes,
            })

        return ctx


class UserActivityView(NoDefaultUserMixin, UserObjectMixin, DetailView):

    @method_decorator(login_required)
    @method_decorator(ajax_required)
    def dispatch(self, request, *args, **kwargs):
        self.month = request.GET.get('month', None)
        return super(UserActivityView, self).dispatch(request, *args, **kwargs)

    def get(self, *args_, **kwargs_):
        data = get_activity_data(self.request, self.get_object(), self.month)
        return JsonResponse(data)


class UserDetailedStatsView(NoDefaultUserMixin, UserObjectMixin, DetailView):
    template_name = 'user/detailed_stats.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.month = request.GET.get('month', None)
        self.user = request.user
        return super(UserDetailedStatsView, self).dispatch(request, *args,
                                                           **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(UserDetailedStatsView, self).get_context_data(**kwargs)
        ob = self.get_object()
        ctx.update(get_detailed_report_context(user=ob, month=self.month))
        ctx.update({'own_report': ob.username == self.user.username})
        return ctx


class AddUserPaidTaskView(NoDefaultUserMixin, TestUserFieldMixin,
                          AjaxResponseMixin, UserObjectMixin, CreateView):
    form_class = PaidTaskForm
    template_name = 'admin/reports/paid_task_form.html'

    @method_decorator(ajax_required)
    def dispatch(self, request, *args, **kwargs):
        return super(AddUserPaidTaskView, self).dispatch(request, *args, **kwargs)

    def get_success_url(self):
        # XXX: This is unused but enforced by `CreateView`
        return reverse('pootle-user-stats', kwargs=self.kwargs)

    def form_valid(self, form):
        super(AddUserPaidTaskView, self).form_valid(form)
        # ignore redirect response
        log('%s\t%s\t%s' % (self.object.user.username, PAID_TASK_ADDED,
                            self.object))
        return JsonResponse({'result': self.object.id})


@admin_required
def reports(request):
    User = get_user_model()
    now = make_aware(datetime.now())

    ctx = {
        'page': 'admin-reports',
        'users': map(
            lambda x: {'id': x.username, 'text': x.formatted_name},
            User.objects.hide_meta()
        ),
        'user_rates_form': UserRatesForm(),
        'paid_task_form': PaidTaskForm(),
        'now': now.strftime('%Y-%m-%d %H:%M:%S'),
        'admin_report': True,
        'paid_task_types': PaidTaskTypes,
    }

    return render_to_response('admin/reports.html', ctx,
                              context_instance=RequestContext(request))


def get_detailed_report_context(user, month):
    [start, end] = get_date_interval(month)

    totals = {'translated': {}, 'reviewed': {}, 'suggested': 0,
              'paid_tasks': {},
              'all': 0}
    items = []

    if user and start and end:
        scores = ScoreLog.objects \
            .select_related('submission__unit__store') \
            .filter(user=user,
                    creation_time__gte=start,
                    creation_time__lte=end) \
            .order_by('creation_time')

        tasks = PaidTask.objects.filter(user=user, datetime__gte=start,
                                        datetime__lte=end).order_by('datetime')

        items = []

        for score in scores.iterator():
            action = None
            subtotal = None
            wordcount = None

            translated, reviewed = score.get_paid_wordcounts()
            translated_details = {}
            if translated is not None:
                action = ReportActionTypes.TRANSLATION
                subtotal = score.rate * translated
                wordcount = translated
                translated_details['raw_rate'] = score.rate - score.review_rate
                translated_details['raw_translated_wordcount'] = \
                    score.wordcount * (1 - score.get_similarity())
                translated_details['raw_subtotal'] = \
                    (translated_details['raw_translated_wordcount'] *
                     translated_details['raw_rate'])
                translated_details['review_subtotal'] = \
                    score.wordcount * score.review_rate
                if score.rate in totals['translated']:
                    totals['translated'][score.rate]['words'] += translated
                else:
                    totals['translated'][score.rate] = {'words': translated}

            elif reviewed is not None:
                action = ReportActionTypes.REVIEW
                subtotal = score.review_rate * reviewed
                wordcount = reviewed

                if score.review_rate in totals['reviewed']:
                    totals['reviewed'][score.review_rate]['words'] += reviewed
                else:
                    totals['reviewed'][score.review_rate] = {'words': reviewed}

            suggested = score.get_suggested_wordcount()
            if suggested is not None:
                action = ReportActionTypes.SUGGESTION
                wordcount = suggested

                totals['suggested'] += suggested

            if action is not None:
                items.append({
                    'score': score,
                    'action': action,
                    'action_name': ReportActionTypes.NAMES_MAP[action],
                    'similarity': score.get_similarity() * 100,
                    'subtotal': subtotal,
                    'wordcount': wordcount,
                    'source_wordcount': score.wordcount,
                    'translated_details': translated_details,
                    'creation_time': score.creation_time,
                })

        paid_tasks = totals['paid_tasks']
        for task in tasks.iterator():
            subtotal = task.amount * task.rate
            items.append({
                'action': task.task_type,
                'action_name': PaidTask.get_task_type_title(task.task_type),
                'subtotal': subtotal,
                'task': task,
                'creation_time': task.datetime,
            })

            totals['all'] += subtotal

            if task.task_type not in paid_tasks:
                paid_tasks[task.task_type] = {
                    'rates': {},
                    'action': PaidTask.get_task_type_title(task.task_type),
                }

            if task.rate in paid_tasks[task.task_type]['rates']:
                current = paid_tasks[task.task_type]['rates'][task.rate]
                current['amount'] += task.amount
                current['subtotal'] += subtotal
            else:
                paid_tasks[task.task_type]['rates'][task.rate] = {
                    'amount': task.amount,
                    'subtotal': subtotal,
                }

        for rate in totals['translated']:
            totals['translated'][rate]['rounded_words'] = \
                int(round(totals['translated'][rate]['words']))
            totals['translated'][rate]['subtotal'] = \
                rate * totals['translated'][rate]['rounded_words']
            totals['all'] += totals['translated'][rate]['subtotal']

        for rate in totals['reviewed']:
            totals['reviewed'][rate]['subtotal'] = (
                rate * totals['reviewed'][rate]['words'])
            totals['all'] += totals['reviewed'][rate]['subtotal']

        totals['all'] = round(totals['all'], 2) + 0

        items = sorted(items, key=lambda x: x['creation_time'])

    if user != '' and user.currency is None:
        user.currency = CURRENCIES[0][0]

    return {
        'items': items,
        'object': user,
        'start': start,
        'end': end,
        'next': start.replace(day=1) + timedelta(days=31),
        'previous': start.replace(day=1) - timedelta(days=1),
        'totals': totals,
        'utc_offset': start.strftime("%z"),
        'action_types': ReportActionTypes,
    }


@admin_required
def reports_detailed(request):
    username = request.GET.get('username', None)
    month = request.GET.get('month', None)
    User = get_user_model()

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        user = ''

    ctx = get_detailed_report_context(user=user, month=month)
    ctx.update({'admin_report': True})

    return render_to_response('admin/detailed_reports.html', ctx,
                              context_instance=RequestContext(request))


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
            error_text = _("User %s not found", form.cleaned_data['username'])
            return JsonResponseNotFound({'msg': error_text})

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
                'datetime__gte': effective_from
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
                PaidTaskTypes.CORRECTION: 1,
            }.get(task_type, 0)

        for task in paid_task_query:
            task.rate = get_task_rate_for(user, task.task_type)
            task.save()

        user.save()

        return JsonResponse({
            'scorelog_count': scorelog_count,
            'paid_task_count': paid_task_count,
        })

    return JsonResponseBadRequest({'errors': form.errors})


@ajax_required
@admin_required
def add_paid_task(request):
    form = PaidTaskForm(request.POST)
    if form.is_valid():
        form.save()
        obj = form.instance
        log('%s\t%s\t%s' % (request.user.username, PAID_TASK_ADDED, obj))
        return JsonResponse({'result': obj.id})

    return JsonResponseBadRequest({'errors': form.errors})


@ajax_required
@admin_required
def remove_paid_task(request, task_id=None):
    if request.method == 'DELETE':
        try:
            obj = PaidTask.objects.get(id=task_id)
            string = (
                '%s\t%s\t%s'
                % (request.user.username,
                   PAID_TASK_DELETED, obj))
            obj.delete()
            log(string)
            return JsonResponse({'removed': 1})

        except PaidTask.DoesNotExist:
            return JsonResponseNotFound({})

    return JsonResponseBadRequest({'error': _('Invalid request method')})


def get_activity_data(request, user, month):
    [start, end] = get_date_interval(month)

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

    now = make_aware(datetime.now())

    json['meta'] = {
        'user': user_dict,
        'month': month,
        'now': now.strftime('%Y-%m-%d %H:%M:%S'),
        'start': start.strftime('%Y-%m-%d'),
        'end': end.strftime('%Y-%m-%d'),
        'utc_offset': start.strftime("%z"),
        'admin_permalink': request.build_absolute_uri(
            reverse('pootle-reports')),
    }

    if user != '':
        scores = ScoreLog.objects.for_user_in_range(user, start, end)
        scores = list(scores.order_by(SCORE_TRANSLATION_PROJECT))
        json['grouped'] = get_grouped_word_stats(scores, user, month)
        scores.sort(key=lambda x: x.creation_time)
        json['daily'] = get_daily_activity(user, scores, start, end)
        json['summary'] = get_summary(scores, start, end)
        tasks = get_paid_tasks(user, start, end)
        for task in tasks:
            if settings.USE_TZ:
                task['datetime'] = timezone.localtime(task['datetime'])
            task['datetime'] = task['datetime'].strftime('%Y-%m-%d %H:%M:%S')

        json['paid_tasks'] = tasks

    return json


@ajax_required
@admin_required
def user_date_prj_activity(request):
    username = request.GET.get('username', None)
    month = request.GET.get('month', None)

    try:
        User = get_user_model()
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        user = ''

    data = get_activity_data(request, user, month)
    return JsonResponse(data)


def get_daily_activity(user, scores, start, end):
    result_translated = {
        'label': ReportActionTypes.NAMES_MAP[ReportActionTypes.TRANSLATION],
        'data': [],
    }
    result_reviewed = {
        'label': ReportActionTypes.NAMES_MAP[ReportActionTypes.REVIEW],
        'data': [],
    }
    result_suggested = {
        'label': ReportActionTypes.NAMES_MAP[ReportActionTypes.SUGGESTION],
        'data': [],
    }

    result = {
        'data': [result_translated, result_reviewed, result_suggested],
        'max_day_score': 10,
        'min_ts': "%d" % (calendar.timegm(start.timetuple()) * 1000),
        'max_ts': "%d" % (calendar.timegm(end.timetuple()) * 1000),
        'nonempty': False,
    }

    if settings.POOTLE_REPORTS_MARK_FUNC:
        try:
            get_mark_data = import_func(settings.POOTLE_REPORTS_MARK_FUNC)
            result['data'].append({
                'data': [],
                'marks': {'show': True},
                'markdata': get_mark_data(user, start, end)
            })
        except ImproperlyConfigured:
            pass

    saved_date = None
    current_day_score = 0
    translated_group = {}
    reviewed_group = {}
    suggested_group = {}
    for score in scores:
        score_time = make_naive(score.creation_time)
        date = score_time.date()

        translated, reviewed = score.get_paid_wordcounts()
        suggested = score.get_suggested_wordcount()

        if any(map(lambda x: x is not None, [translated, reviewed,
                                             suggested])):
            translated = 0 if translated is None else translated
            reviewed = 0 if reviewed is None else reviewed
            suggested = 0 if suggested is None else suggested

            if saved_date != date:
                saved_date = date
                reviewed_group[date] = 0
                translated_group[date] = 0
                suggested_group[date] = 0
                if result['max_day_score'] < current_day_score:
                    result['max_day_score'] = current_day_score
                current_day_score = 0
            current_day_score += int(reviewed + translated + suggested)
            result['nonempty'] |= current_day_score > 0

            translated_group[date] += translated
            reviewed_group[date] += reviewed
            suggested_group[date] += suggested

    if result['max_day_score'] < current_day_score:
        result['max_day_score'] = current_day_score

    for group, res in [(translated_group, result_translated),
                       (reviewed_group, result_reviewed),
                       (suggested_group, result_suggested)]:
        for date, item in sorted(group.items(), key=lambda x: x[0]):
            ts = int(calendar.timegm(date.timetuple()) * 1000)
            res['data'].append((ts, item))

    return result


def get_rates(user, start, end):
    """Get user rates that were set for the user during a period
    from start to end. Raise an exception if the user has multiple rates
    during the period.

    :param user: get rates for this User object.
    :param start: datetime
    :param end: datetime
    :return: a tuple ``(rate, review_rate, hourly_rate)`` where ``rate`` is the
        translation rate, and ``review_rate`` is the review rate, and
        ``hourly_rate`` is the rate for hourly work that can be added as
        PaidTask.
    """
    scores = ScoreLog.objects.for_user_in_range(user, start, end)
    rate, review_rate, hourly_rate = 0, 0, 0
    rates = scores.values('rate', 'review_rate').distinct()
    if len(rates) > 1:
        raise Exception("Multiple user [%s] rate values." % user.username)
    elif len(rates) == 1:
        rate = rates[0]['rate']
        review_rate = rates[0]['review_rate']

    tasks = PaidTask.objects.for_user_in_range(user, start, end)
    task_rates = tasks.values('task_type', 'rate').distinct()
    for task_rate in task_rates:
        if (task_rate['task_type'] == PaidTaskTypes.TRANSLATION and
            rate > 0 and
            task_rate['rate'] != rate):
            raise Exception("Multiple user [%s] rate values." % user.username)
        if (task_rate['task_type'] == PaidTaskTypes.REVIEW and
            review_rate > 0 and
            task_rate['rate'] != review_rate):
            raise Exception("Multiple user [%s] rate values." % user.username)
        if task_rate['task_type'] == PaidTaskTypes.HOURLY_WORK:
            if hourly_rate > 0 and task_rate['rate'] != hourly_rate:
                raise Exception("Multiple user [%s] rate values." %
                                user.username)
            hourly_rate = task_rate['rate']

    rate = rate if rate > 0 else user.rate
    review_rate = review_rate if review_rate > 0 else user.review_rate
    hourly_rate = hourly_rate if hourly_rate > 0 else user.hourly_rate

    return rate, review_rate, hourly_rate


def get_paid_tasks(user, start, end):
    result = []

    tasks = PaidTask.objects.for_user_in_range(user, start, end)

    for task in tasks:
        result.append({
            'id': task.id,
            'description': task.description,
            'amount': task.amount,
            'type': task.task_type,
            'action': PaidTask.get_task_type_title(task.task_type),
            'rate': task.rate,
            'datetime': task.datetime,
        })

    return result


def get_summary(scores, start, end):
    rate = review_rate = None
    translation_month = review_month = None
    translated_row = reviewed_row = None

    translations = []
    reviews = []

    start = make_naive(start)
    end = make_naive(end)

    for score in scores:
        score_time = make_naive(score.creation_time)

        if (score.rate != rate or
            translation_month != score_time.month):
            rate = score.rate
            translation_month = score_time.month
            translated_row = {
                'type': PaidTaskTypes.TRANSLATION,
                'action': PaidTaskTypes.TRANSLATION,
                'amount': 0,
                'rate': score.rate,
                'start': score_time,
                'end': score_time,
            }
            translations.append(translated_row)
        if (score.review_rate != review_rate or
            review_month != score_time.month):
            review_rate = score.review_rate
            review_month = score_time.month
            reviewed_row = {
                'type': PaidTaskTypes.REVIEW,
                'action': PaidTaskTypes.REVIEW,
                'amount': 0,
                'rate': score.review_rate,
                'start': score_time,
                'end': score_time,
            }
            reviews.append(reviewed_row)

        translated_words, reviewed_words = score.get_paid_wordcounts()

        if translated_words is not None:
            translated_row['end'] = score_time
            translated_row['amount'] += translated_words
        elif reviewed_words is not None:
            reviewed_row['end'] = score_time
            reviewed_row['amount'] += reviewed_words

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

    for item in result:
        item['type'] = item['action']
        item['action'] = PaidTask.get_task_type_title(item['action'])

    for item in result:
        item['start'] = item['start'].strftime('%Y-%m-%d')
        item['end'] = item['end'].strftime('%Y-%m-%d')

    return result


@ajax_required
@admin_required
def users(request):
    User = get_user_model()
    data = list(
        User.objects.hide_meta()
                    .values('id', 'username', 'full_name')
    )
    return JsonResponse(data)
