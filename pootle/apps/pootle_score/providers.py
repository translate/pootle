# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle.core.delegate import event_score
from pootle.core.plugin import provider
from pootle_log.utils import LogEvent

from . import scores


@provider(event_score, sender=LogEvent)
def event_log_score_provider(**kwargs_):
    return dict(
        suggestion_created=scores.SuggestionCreatedScore,
        suggestion_accepted=scores.SuggestionAcceptedScore,
        suggestion_rejected=scores.SuggestionRejectedScore,
        target_updated=scores.TargetUpdatedScore,
        state_updated=scores.StateUpdatedScore,
        comment_updated=scores.CommentUpdatedScore)
