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
from django.template.defaultfilters import escape
from django.template.loader import render_to_string

from contact.forms import ContactForm, ReportForm
from pootle_store.models import Unit


@pytest.mark.django_db
def test_contact_form(admin, rf, mailoutbox):
    request = rf.request()
    request.user = admin
    request.META['REMOTE_ADDR'] = '127.0.0.1'
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
    assert "Your question or comment:" not in message.body


@pytest.mark.django_db
def test_contact_form_escaped_tags(admin, rf, mailoutbox):
    request = rf.request()
    request.user = admin
    request.META['REMOTE_ADDR'] = '127.0.0.1'
    recipient_email = settings.POOTLE_CONTACT_EMAIL
    specified_subject = "My <tag> subject"
    subject = "[%s] %s" % (settings.POOTLE_TITLE, specified_subject)
    data = {
        'name': admin.full_name,
        'email': admin.email,
        'email_subject': specified_subject,
        'body': "First <tag> of message.",
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
    assert escape(subject) == message.subject
    assert escape(data['body']) in message.body
    assert "Your question or comment:" not in message.body


@pytest.mark.django_db
def test_contact_form_subject(admin, rf, mailoutbox):
    request = rf.request()
    request.user = admin
    request.META['REMOTE_ADDR'] = '127.0.0.1'
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
    request.META['REMOTE_ADDR'] = '127.0.0.1'
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
    request.META['REMOTE_ADDR'] = '127.0.0.1'

    # Get initial data for the form.
    subject_ctx = {
        'server_name': settings.POOTLE_TITLE,
        'unit': unit.pk,
        'language': unit.store.translation_project.language.code,
        'project': unit.store.translation_project.project.code,
    }
    subject = render_to_string('contact_form/report_form_subject.txt',
                               context=subject_ctx)
    subject = subject.strip()
    context_ctx = {
        'unit': unit,
        'unit_absolute_url':
            request.build_absolute_uri(unit.get_translate_url()),
    }
    context = render_to_string('contact_form/report_form_context.txt',
                               context=context_ctx)
    context = context.strip()
    translator_comment = "The string is wrong"
    data = {
        'name': user.full_name,
        'email': user.email,
        'context': context,
        'body': translator_comment,
    }
    email_body_ctx = {
        'request': request,
        'context': context,
        'ip_address': '127.0.0.1',
        'body': translator_comment,
    }
    email_body = render_to_string('contact_form/report_form.txt',
                                  context=email_body_ctx)

    # Instantiate form and test.
    form = ReportForm(request=request, initial=data, data=data, unit=unit)
    assert form.is_valid()
    form.save()
    assert len(mailoutbox) == 1
    message = mailoutbox[0]
    assert message.from_email == settings.DEFAULT_FROM_EMAIL
    reply_to = u'%s <%s>' % (data['name'], data['email'])
    assert reply_to == message.extra_headers['Reply-To']
    assert [recipient_email] == message.recipients()
    assert message.subject.startswith(u'[%s] ' % settings.POOTLE_TITLE)
    assert subject == message.subject
    assert email_body in message.body


@pytest.mark.django_db
def test_report_error_form_settings_email(admin, rf, mailoutbox):
    unit = Unit.objects.select_related(
        'store__translation_project__project',
        'store__translation_project__language',
    ).last()
    recipient_email = getattr(settings, 'POOTLE_CONTACT_REPORT_EMAIL',
                              settings.POOTLE_CONTACT_EMAIL)

    _test_report_form(unit, recipient_email, admin, rf, mailoutbox)


@pytest.mark.django_db
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
def test_report_error_form_context_cannot_be_altered(admin, rf, mailoutbox):
    request = rf.request()
    request.user = admin
    request.META['REMOTE_ADDR'] = '127.0.0.1'

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
def test_report_error_form_escaped_tags(admin, rf, mailoutbox):
    request = rf.request()
    request.user = admin
    request.META['REMOTE_ADDR'] = '127.0.0.1'

    unit_target = "some <tag>"
    unit = Unit.objects.select_related(
        'store__translation_project__project',
        'store__translation_project__language',
    ).last()
    unit.target = unit_target
    unit.save()
    context_ctx = {
        'unit': unit,
        'unit_absolute_url':
            request.build_absolute_uri(unit.get_translate_url()),
    }
    context = render_to_string('contact_form/report_form_context.txt',
                               context=context_ctx)
    context = context.strip()
    data = {
        'name': admin.full_name,
        'email': admin.email,
        'context': context,
        'body': "The string <tag> is wrong",
    }

    # Instantiate form and test.
    form = ReportForm(request=request, initial=data, data=data, unit=unit)
    assert form.is_valid()
    form.save()
    assert len(mailoutbox) == 1
    message = mailoutbox[0]
    assert escape(unit_target) in message.body
    assert escape(data['body']) in message.body


@pytest.mark.django_db
def test_report_error_form_required_fields(admin, rf, mailoutbox):
    request = rf.request()
    request.user = admin
    request.META['REMOTE_ADDR'] = '127.0.0.1'

    unit = Unit.objects.select_related(
        'store__translation_project__project',
        'store__translation_project__language',
    ).last()

    # Instantiate form and test.
    form = ReportForm(request=request, initial={}, data={}, unit=unit)
    assert not form.is_valid()
    assert 'email' in form.errors
    assert form.errors['email'] == [u'This field is required.']
    assert 'name' in form.errors
    assert form.errors['name'] == [u'This field is required.']
    assert 'context' in form.errors
    assert form.errors['context'] == [u'This field is required.']
    assert 'body' in form.errors
    assert form.errors['body'] == [u'This field is required.']
