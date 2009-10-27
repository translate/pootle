#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2009 Zuza Software Foundation
# 
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# Pootle is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Pootle; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from django.utils.translation import ugettext as _

from pootle_app.models import Suggestion, Submission

def map_num_contribs(sub, user):
    user.num_contribs = sub.num_contribs
    return user

def users_from_suggestions(sugs):
    """Get the Users associated with the Suggestions. Also assign
    the num_contribs attribute from the Suggestion to the User"""
    return [map_num_contribs(sug, sug.suggester.user) for sug in sugs]

def users_from_submissions(subs):
    """Get the Users associated with the Submissions. Also assign
    the num_contribs attribute from the Submission to the User"""
    return [map_num_contribs(sub, sub.submitter.user) for sub in subs]

def gen_top_stat(data, header_label):
    return {
        'data':        data,
        'headerlabel': header_label,
        'ranklabel':   _('Rank'),
        'namelabel':   _('Name'),
        'vallabel':    header_label }

def limit(query):
    return query[:5]

def gentopstats(narrow_search_results):
    """Generate the top contributor stats to be displayed
    for an entire Pootle installation, a language or a project.
    'narrow_search_results' is a function taking a Django
    query and should filter the results to give the results
    for a particular project or language (or whatever is required).
    For example the narrowing function
        lambda query: query.filter(project='pootle', language='en')
    will get the top contributor results for the project 'pootle'
    in the language 'en'.

    The output of this function looks something like this:
      {'data':        [],
       'headerlabel': u'Suggestions',
       'namelabel':   u'Name',
       'ranklabel':   u'Rank',
       'vallabel':    u'Suggestions'},
      {'data':        [],
       'headerlabel': u'Reviews',
       'namelabel':   u'Name',
       'ranklabel':   u'Rank',
       'vallabel':    u'Reviews'},
      {'data':        [],
       'headerlabel': u'Submissions',
       'namelabel':   u'Name',
       'ranklabel':   u'Rank',
       'vallabel':    u'Submissions'}]
    """
    top_sugg   = limit(narrow_search_results(Suggestion.objects.get_top_suggesters()))
    top_review = limit(narrow_search_results(Suggestion.objects.get_top_reviewers()))
    top_sub    = limit(narrow_search_results(Submission.objects.get_top_submitters()))

    return [
        gen_top_stat(users_from_suggestions(top_sugg),   _('Suggestions')),
        gen_top_stat(users_from_suggestions(top_review), _('Reviews')),
        gen_top_stat(users_from_submissions(top_sub),    _('Submissions')) ]
