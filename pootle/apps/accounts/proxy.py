# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from hashlib import md5

from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.html import format_html


class DisplayUser(object):

    def __init__(self, username, full_name, email=None):
        self.username = username
        self.full_name = full_name
        self.email = email

    @property
    def author_link(self):
        return format_html(
            u'<a href="{}">{}</a>',
            self.get_absolute_url(),
            self.display_name)

    @property
    def display_name(self):
        return (
            self.full_name.strip()
            if self.full_name.strip()
            else self.username)

    @property
    def email_hash(self):
        return md5(force_bytes(self.email)).hexdigest()

    def get_absolute_url(self):
        return reverse(
            'pootle-user-profile',
            args=[self.username])

    def gravatar_url(self, size=80):
        return (
            'https://secure.gravatar.com/avatar/%s?s=%d&d=mm'
            % (self.email_hash, size))

    def to_dict(self):
        userdict = {}
        props = [
            "username",
            "author_link", "display_name", "email_hash"]
        methods = [
            "get_absolute_url", "gravatar_url"]
        for prop in props:
            userdict[prop] = getattr(self, prop)
        for method in methods:
            userdict[method] = getattr(self, method)()
        return userdict
