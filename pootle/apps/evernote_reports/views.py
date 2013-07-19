#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Evernote Corporation

from datetime import datetime

from django.contrib.auth.models import User
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext

from pootle_app.views.admin.util import user_is_admin
from pootle_misc.util import jsonify
from pootle_statistics.models import Submission


# Django field query aliases
LANG_CODE = 'translation_project__language__code'
LANG_NAME = 'translation_project__language__fullname'
PRJ_CODE = 'translation_project__project__code'
PRJ_NAME = 'translation_project__project__fullname'
INITIAL = 'submissionstats__initial_translation'
POOTLE_WORDCOUNT = 'unit__source_wordcount'
SOURCE_WORDCOUNT = 'submissionstats__source_wordcount'
ADDED_WORDS = 'submissionstats__words_added'
REMOVED_WORDS = 'submissionstats__words_removed'

# field aliases
DATE = 'creation_time_date'


@user_is_admin
def evernote_reports(request, context={}):
    cxt = context
    cxt.update({
        'users': map(
            lambda x: {'code': x.username, 'name': u'%s' % x },
            User.objects.hide_defaults()
        )
    })

    return render_to_response('evernote/reports.html', cxt,
                              context_instance=RequestContext(request))


def user_date_prj_activity(request):
    user = request.GET.get('user', None)

    try:
        user = User.objects.get(username=user)
    except:
        user = ''

    start_date = request.GET.get('start', None)
    end_date = request.GET.get('end', None)

    if start_date:
        start = datetime.strptime(start_date, '%Y-%m-%d')
    else:
        start = datetime.now()

    if end_date:
        end = datetime.strptime(end_date, '%Y-%m-%d')
    else:
        end = datetime.now()

    start = start.replace(hour=0, minute=0, second=0)
    end = end.replace(hour=23, minute=59, second=59)

    json = {'total': {'n1': 0, 'pootle_n1': 0}}

    def add2total(total, n1, pootle_n1):
        total['n1'] += n1
        total['pootle_n1'] += pootle_n1

    if user:
        rr = Submission.objects.filter(
                submitter=user.pootleprofile,
                submissionstats__initial_translation=True,
                creation_time__gte=start,
                creation_time__lte=end
            ).extra(select={DATE: "DATE(creation_time)"}) \
             .values(LANG_CODE, LANG_NAME, PRJ_CODE, PRJ_NAME, DATE) \
             .annotate(
                pootle_n1=Sum(POOTLE_WORDCOUNT),
                n1=Sum(SOURCE_WORDCOUNT),
                added=Sum(ADDED_WORDS),
                removed=Sum(REMOVED_WORDS)
            ).order_by(LANG_CODE, DATE)

        projects = {}
        res = {}

        saved_lang = None
        res_date = None
        lang_data = None

        for r in rr:
            cur_lang = r[LANG_CODE]
            cur_prj = r[PRJ_CODE]

            n1_cond = r.has_key('n1') and r['n1'] is not None
            pootle_n1_cond = (r.has_key('pootle_n1') and
                              r['pootle_n1'] is not None)
            cur_n1 = r['n1'] if n1_cond else 0
            cur_pootle_n1 = r['pootle_n1'] if pootle_n1_cond else 0

            if cur_lang != saved_lang:
                if saved_lang != None and lang_data != None:
                    add2total(json['total'], lang_data['total']['n1'],
                              lang_data['total']['pootle_n1'])
                    add2total(lang_data['total'], res_date['total']['n1'],
                              res_date['total']['pootle_n1'])

                saved_lang = cur_lang
                res[cur_lang] = {
                    'name': r[LANG_NAME],
                    'dates': [],
                    'sums': {},
                    'total': {'n1': 0, 'pootle_n1': 0}
                }

                lang_data = res[cur_lang]
                sums = lang_data['sums']

                saved_date = None

            if saved_date != r[DATE]:
                if saved_date is not None:
                    after_break = (r[DATE] - saved_date).days > 1
                    add2total(lang_data['total'], res_date['total']['n1'],
                              res_date['total']['pootle_n1'])

                else:
                    after_break = False

                saved_date = r[DATE]
                res_date = {
                    'date': datetime.strftime(saved_date, '%Y-%m-%d'),
                    'projects': {},
                    'after_break': after_break,
                    'total': {'n1': 0, 'pootle_n1': 0}
                }

                lang_data['dates'].append(res_date)

            if res_date is not None:
                if sums.has_key(cur_prj):
                    sums[cur_prj]['n1'] += cur_n1
                    sums[cur_prj]['pootle_n1'] += cur_pootle_n1
                else:
                    sums[cur_prj] = {'n1': cur_n1, 'pootle_n1': cur_pootle_n1}

                res_date['projects'].update({
                    cur_prj: {
                        'n1': cur_n1,
                        'pootle_n1': cur_pootle_n1
                    }
                })
                add2total(res_date['total'], cur_n1, cur_pootle_n1)

                projects[cur_prj] = r[PRJ_NAME]

        if lang_data is not None and res_date is not None:
            add2total(lang_data['total'], res_date['total']['n1'],
                      res_date['total']['pootle_n1'])
            add2total(json['total'], lang_data['total']['n1'],
                      lang_data['total']['pootle_n1'])

        json['all_projects'] = projects
        json['results'] = res

    json['meta'] = {'user': u'%s' % user, 'start': start_date, 'end': end_date}
    response = jsonify(json)

    return HttpResponse(response, mimetype="application/json")


def users(request):
    json = list(
        User.objects.hide_defaults()
                    .select_related('evernote_account')
                    .values('id', 'username', 'first_name', 'last_name')
    )
    response = jsonify(json)

    return HttpResponse(response, mimetype="application/json")
