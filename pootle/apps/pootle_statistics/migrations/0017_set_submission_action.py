# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-25 13:54
from __future__ import unicode_literals

from django.db import migrations

from pootle_statistics.models import (
    SubmissionActions, SubmissionFields, SubmissionTypes)


class OLDSubmissionTypes(object):
    NORMAL = 1
    UPLOAD = 4
    SYSTEM = 5

    MUTE_CHECK = 6
    UNMUTE_CHECK = 7
    SUGG_ACCEPT = 3
    SUGG_ADD = 8
    SUGG_REJECT = 9


def set_subs_action(apps, schema_editor):
    subs = apps.get_model("pootle_statistics.Submission").objects.all()

    # all suggestion-related subs are NORMAL
    subs.filter(type=OLDSubmissionTypes.SUGG_ADD).update(
        action=int(SubmissionActions.ADD),
        field=SubmissionFields.SUGGESTION,
        type=SubmissionTypes.NORMAL)
    subs.filter(type=OLDSubmissionTypes.SUGG_ACCEPT).update(
        action=int(SubmissionActions.ACCEPT),
        field=SubmissionFields.SUGGESTION,
        type=SubmissionTypes.NORMAL)
    subs.filter(type=OLDSubmissionTypes.SUGG_REJECT).update(
        action=int(SubmissionActions.REJECT),
        field=SubmissionFields.SUGGESTION,
        type=SubmissionTypes.NORMAL)
    subs.filter(type=OLDSubmissionTypes.MUTE_CHECK).update(
        action=int(SubmissionActions.MUTE),
        field=SubmissionFields.CHECK,
        type=SubmissionTypes.NORMAL)
    subs.filter(type=OLDSubmissionTypes.UNMUTE_CHECK).update(
        action=int(SubmissionActions.UNMUTE),
        field=SubmissionFields.CHECK,
        type=SubmissionTypes.NORMAL)


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_statistics', '0016_submission_action'),
    ]

    operations = [
        migrations.RunPython(set_subs_action),
    ]
