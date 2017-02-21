# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from __future__ import absolute_import

import pytest

from django.conf import settings
from django.template.loader import render_to_string

from contact.forms import ContactForm, ReportForm
from pootle_store.models import Unit


@pytest.mark.django_db
def test_contact_form(admin, rf, mailoutbox):
    request = rf.request()
    request.user = admin
    recipient_email = settings.POOTLE_CONTACT_EMAIL
    specified_subject = "My subject"
    subject = "[%s] %s" % (settings.POOTLE_TITLE, specified_subject)
    data = {
        'name': admin.full_name,
        'email': admin.email,
        'email_subject': specified_subject,
        'body': "First paragraph of message\n\nSecond paragraph of message.",
    }
    form = ContactForm(request=request, data=data)
    assert form.is_valid()
    form.save()
    assert len(mailoutbox) == 1
    message = mailoutbox[0]
    assert message.from_email == settings.DEFAULT_FROM_EMAIL
    reply_to = u'%s <%s>' % (data['name'], data['email'])
    assert reply_to == message.extra_headers['Reply-To']
    assert [recipient_email] == message.recipients()
    assert subject == message.subject
    assert data['body'] in message.body


@pytest.mark.django_db
@pytest.mark.xfail(reason="subject rendering is broken")
def test_report_error_form(admin, rf, mailoutbox):
    request = rf.request()
    request.user = admin

    # Get initial data for the form.
    unit = Unit.objects.select_related(
        'store__translation_project__project',
        'store__translation_project__language',
    ).last()
    tp = unit.store.translation_project
    recipient_email = "errors@example.net"
    tp.project.report_email = recipient_email
    tp.project.save()
    subject_ctx = {
        'unit': unit,
        'language': tp.language.code,
        'project': tp.project.code,
    }
    subject = render_to_string('contact_form/report_form_subject.txt',
                               context=subject_ctx)
    subject = subject.strip()
    body_ctx = {
        'unit': unit,
        'unit_absolute_url':
            request.build_absolute_uri(unit.get_translate_url()),
    }
    body = render_to_string('contact_form/report_form_body.txt',
                            context=body_ctx)
    data = {
        'name': admin.full_name,
        'email': admin.email,
        'email_subject': subject,
        'body': body.strip(),
        'report_email': recipient_email,
    }

    # Instantiate form and test.
    form = ReportForm(request=request, data=data)
    assert form.is_valid()
    form.save()
    assert len(mailoutbox) == 1
    message = mailoutbox[0]
    assert message.from_email == settings.DEFAULT_FROM_EMAIL
    reply_to = u'%s <%s>' % (data['name'], data['email'])
    assert reply_to == message.extra_headers['Reply-To']
    assert [recipient_email] == message.recipients()
    assert subject == message.subject
    assert data['body'] in message.body
