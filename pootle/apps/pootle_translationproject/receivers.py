# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.dispatch import receiver
from django.template.loader import render_to_string

from pootle.core.mail import send_mail
from pootle.core.url_helpers import urljoin
from pootle.i18n.gettext import ugettext_lazy as _

from .models import TranslationProject
from .signals import tp_init_failed_async, tp_inited_async


def get_recipients(project):
    User = get_user_model()
    return list(set(User.objects.filter(
        Q(permissionset__positive_permissions__codename="administrate",
          permissionset__directory__pootle_path=project.pootle_path) |
        Q(is_superuser=True)).values_list("email", flat=True)))


@receiver(tp_inited_async, sender=TranslationProject)
def tp_inited_async_handler(**kwargs):
    instance = kwargs["instance"]
    response_url = kwargs["response_url"]
    ctx = {"tp": instance,
           "url": urljoin(response_url, instance.get_absolute_url())}
    message = render_to_string(
        'projects/admin/email/translation_project_created.txt', context=ctx)
    subject = _(u"Translation project (%s) created" % instance)
    recipients = get_recipients(instance.project)
    send_mail(subject, message, from_email=None,
              recipient_list=[], fail_silently=True, bcc=recipients)


@receiver(tp_init_failed_async, sender=TranslationProject)
def tp_init_failed_async_handler(**kwargs):
    instance = kwargs["instance"]

    ctx = {"tp": instance}
    message = render_to_string(
        'projects/admin/email/translation_project_creation_failed.txt',
        context=ctx)
    subject = _(u"Translation project (%s) creation failed" % instance)
    recipients = get_recipients(instance.project)
    send_mail(subject, message, from_email=None,
              recipient_list=[], fail_silently=True, bcc=recipients)
