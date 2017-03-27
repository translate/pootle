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
def test_contact_form_subject(admin, rf, mailoutbox):
    request = rf.request()
    request.user = admin
    data = {
        'name': admin.full_name,
        'email': admin.email,
        'email_subject': "a" * 101,
        'body': "Whatever",
    }
    form = ContactForm(request=request, data=data)
    assert not form.is_valid()

    data['email_subject'] = "a" * 100
    form = ContactForm(request=request, data=data)
    assert form.is_valid()


@pytest.mark.django_db
def test_contact_form_required_fields(admin, rf, mailoutbox):
    request = rf.request()
    request.user = admin
    form = ContactForm(request=request, data={})
    assert not form.is_valid()
    assert 'email' in form.errors
    assert form.errors['email'] == [u'This field is required.']
    assert 'name' in form.errors
    assert form.errors['name'] == [u'This field is required.']
    assert 'email_subject' in form.errors
    assert form.errors['email_subject'] == [u'This field is required.']
    assert 'body' in form.errors
    assert form.errors['body'] == [u'This field is required.']


def _test_report_form(unit, recipient_email, user, rf, mailoutbox):
    request = rf.request()
    request.user = user

    # Get initial data for the form.
    subject_ctx = {
        'unit': unit,
        'language': unit.store.translation_project.language.code,
        'project': unit.store.translation_project.project.code,
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
        'name': user.full_name,
        'email': user.email,
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


@pytest.mark.django_db
@pytest.mark.xfail(reason="subject rendering is broken")
def test_report_error_form_settings_email(admin, rf, mailoutbox):
    unit = Unit.objects.select_related(
        'store__translation_project__project',
        'store__translation_project__language',
    ).last()
    recipient_email = getattr(settings, 'POOTLE_CONTACT_REPORT_EMAIL',
                              settings.POOTLE_CONTACT_EMAIL)

    _test_report_form(unit, recipient_email, admin, rf, mailoutbox)


@pytest.mark.django_db
@pytest.mark.xfail(reason="subject rendering is broken")
def test_report_error_form_project_email(admin, rf, mailoutbox):
    unit = Unit.objects.select_related(
        'store__translation_project__project',
        'store__translation_project__language',
    ).last()
    project = unit.store.translation_project.project
    project.report_email = "errors@example.net"
    project.save()

    _test_report_form(unit, project.report_email, admin, rf, mailoutbox)


@pytest.mark.django_db
@pytest.mark.xfail(reason="context field not yet implemented")
def test_report_error_form_context_cannot_be_altered(admin, rf, mailoutbox):
    request = rf.request()
    request.user = admin

    unit = Unit.objects.select_related(
        'store__translation_project__project',
        'store__translation_project__language',
    ).last()
    context_ctx = {
        'unit': unit,
        'unit_absolute_url':
            request.build_absolute_uri(unit.get_translate_url()),
    }
    context = render_to_string('contact_form/report_form_context.txt',
                               context=context_ctx)
    context = context.strip()
    initial = {
        'name': admin.full_name,
        'email': admin.email,
        'context': context,
        'body': "The string is wrong",
    }
    data = initial.copy()
    sent_context = "Different context"
    data['context'] = sent_context

    # Instantiate form and test.
    form = ReportForm(request=request, initial=initial, data=data, unit=unit)
    assert form.is_valid()
    form.save()
    assert len(mailoutbox) == 1
    message = mailoutbox[0]
    assert sent_context not in message.body


@pytest.mark.django_db
def test_report_error_form_required_fields(admin, rf, mailoutbox):
    request = rf.request()
    request.user = admin

    # Instantiate form and test.
    form = ReportForm(request=request, initial={}, data={})
    assert not form.is_valid()
    assert 'email' in form.errors
    assert form.errors['email'] == [u'This field is required.']
    assert 'name' in form.errors
    assert form.errors['name'] == [u'This field is required.']
    assert 'body' in form.errors
    assert form.errors['body'] == [u'This field is required.']
