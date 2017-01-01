# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.contrib.auth import get_user_model

from pootle.core.delegate import scores
from pootle.core.plugin import getter
from pootle_language.models import Language
from pootle_project.models import Project, ProjectSet
from pootle_translationproject.models import TranslationProject

from .utils import (
    LanguageScores, ProjectScores, ProjectSetScores, TPScores, UserScores)


User = get_user_model()


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
