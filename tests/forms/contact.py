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

from contact.forms import ContactForm


@pytest.mark.django_db
def test_contact_form(admin, rf, mailoutbox):
    request = rf.request()
    request.user = admin
    data = {
        'name': admin.full_name,
        'email': admin.email,
        'email_subject': "My subject",
        'body': "First paragraph of message\n\nSecond paragraph of message.",
    }
    form = ContactForm(request=request, data=data)
    assert form.is_valid()
    form.save()
    assert len(mailoutbox) == 1
    message = mailoutbox[0]
    reply_to = u'%s <%s>' % (data['name'], data['email'])
    assert reply_to == message.extra_headers['Reply-To']
    subject = u'[%s] %s' % (settings.POOTLE_TITLE, data['email_subject'])
    assert subject == message.subject
    assert data['body'] in message.body
