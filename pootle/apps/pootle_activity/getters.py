
from django.contrib.auth import get_user_model

from pootle_comment.models import Comment
from pootle.core.delegate import event, timeline
from pootle.core.plugin import getter
from pootle_language.models import Language
from pootle_project.models import Project
from pootle_statistics.models import Submission
from pootle_store.models import Store
from pootle_translationproject.models import TranslationProject

from .utils import (
    CommentEvent, SubmissionEvent, LanguageTimeline,
    ProjectTimeline, StoreTimeline, TPTimeline, UserTimeline)


User = get_user_model()


@getter(timeline, sender=User)
def user_timeline_getter(**kwargs_):
    return UserTimeline


@getter(timeline, sender=Language)
def language_timeline_getter(**kwargs_):
    return LanguageTimeline


@getter(timeline, sender=Project)
def project_timeline_getter(**kwargs_):
    return ProjectTimeline


@getter(timeline, sender=Store)
def store_timeline_getter(**kwargs_):
    return StoreTimeline


@getter(timeline, sender=TranslationProject)
def tp_timeline_getter(**kwargs_):
    return TPTimeline


@getter(event, sender=Submission)
def submission_event_getter(**kwargs_):
    return SubmissionEvent


@getter(event, sender=Comment)
def comment_event_getter(**kwargs_):
    return CommentEvent
