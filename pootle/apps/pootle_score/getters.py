# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.contrib.auth import get_user_model

from pootle.core.delegate import display, scores, score_updater
from pootle.core.plugin import getter
from pootle_language.models import Language
from pootle_project.models import Project, ProjectSet
from pootle_store.models import Store
from pootle_translationproject.models import TranslationProject

from .updater import StoreScoreUpdater
from .display import TopScoreDisplay
from .utils import (
    LanguageScores, ProjectScores, ProjectSetScores, Scores,
    TPScores, UserScores)


User = get_user_model()


@getter(display, sender=Scores)
def get_scores_display(**kwargs_):
    return TopScoreDisplay


@getter(scores, sender=Language)
def get_language_scores(**kwargs_):
    return LanguageScores


@getter(scores, sender=Project)
def get_project_scores(**kwargs_):
    return ProjectScores


@getter(scores, sender=ProjectSet)
def get_projectset_scores(**kwargs_):
    return ProjectSetScores


@getter(scores, sender=TranslationProject)
def get_tp_scores(**kwargs_):
    return TPScores


@getter(scores, sender=User)
def get_user_scores(**kwargs_):
    return UserScores


@getter(score_updater, sender=Store)
def score_updater_getter(**kwargs_):
    return StoreScoreUpdater
