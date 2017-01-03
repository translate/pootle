# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from accounts.proxy import DisplayUser
from pootle.i18n import formatter


class TopScoreDisplay(object):

    def __init__(self, top_scores, language=None):
        self.top_scores = top_scores
        self.language = language

    def __iter__(self):
        for score in self.top_scores:
            yield dict(
                user=DisplayUser(
                    score["user__username"],
                    score["user__full_name"],
                    score["user__email"]),
                public_total_score=formatter.number(
                    int(round(score["score__sum"]))))
