#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2004-2009 Zuza Software Foundation
#
# This file is part of translate.
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

import re
from django.utils.translation import ugettext as _


def shortdescription(descr):
    """Returns a short description by removing markup and only
    including up to the first br-tag"""

    stopsign = descr.find('<br')
    if stopsign >= 0:
        descr = descr[:stopsign]
    return re.sub('<[^>]*>', '', descr).strip()

def map_num_contribs(sub, user):
    user.num_contribs = sub.num_contribs
    return user

def users_form_suggestions(sugs):
    """Get the Users associated with the Suggestions. Also assign the
    num_contribs attribute from the Suggestion to the User"""

    return [map_num_contribs(sug, sug.suggester.user) for sug in sugs]

def users_form_submissions(subs):
    """Get the Users associated with the Submissions. Also assign the
    num_contribs attribute from the Submission to the User"""

    return [map_num_contribs(sub, sub.submitter.user) for sub in subs]

def gentopstats(topsugg, topreview, topsub):
    ranklabel = _('Rank')
    namelabel = _('Name')
    topstats = []
    topstats.append({
        'data': users_form_suggestions(topsugg),
        'headerlabel': _('Suggestions'),
        'ranklabel': ranklabel,
        'namelabel': namelabel,
        'vallabel': _('Suggestions'),
        })
    topstats.append({
        'data': users_form_suggestions(topreview),
        'headerlabel': _('Reviews'),
        'ranklabel': ranklabel,
        'namelabel': namelabel,
        'vallabel': _('Reviews'),
        })
    topstats.append({
        'data': users_form_submissions(topsub),
        'headerlabel': _('Submissions'),
        'ranklabel': ranklabel,
        'namelabel': namelabel,
        'vallabel': _('Submissions'),
        })
    return topstats




