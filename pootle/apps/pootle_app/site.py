# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from urlparse import urlparse

from django.conf import settings
from django.contrib.sites.models import Site as ContribSite


class PootleSite(object):

    @property
    def use_insecure_http(self):
        if not self.uses_sites:
            return urlparse(settings.POOTLE_CANONICAL_URL).scheme == "http"
        return (
            getattr(settings, "USE_INSECURE_HTTP", False)
            and True or False)

    @property
    def use_http_port(self):
        if not self.uses_sites:
            return urlparse(settings.POOTLE_CANONICAL_URL).port or 80
        return getattr(settings, "USE_HTTP_PORT", 80)

    @property
    def uses_sites(self):
        return (
            "django.contrib.sites" not in settings.INSTALLED_APPS
            or not settings.POOTLE_CANONICAL_URL)

    @property
    def contrib_site(self):
        if self.uses_sites:
            return ContribSite.objects.get_current()

    @property
    def domain(self):
        if self.uses_sites:
            return self.contrib_site.domain
        return urlparse(settings.POOTLE_CANONICAL_URL).hostname

    @property
    def canonical_url(self):
        if not self.uses_sites:
            return settings.POOTLE_CANONICAL_URL
        protocol = (
            "http"
            if self.use_insecure_http
            else "https")
        port = (
            ":%s" % self.use_http_port
            if self.use_http_port != 80
            else "")
        return (
            "%s://%s%s"
            % (protocol,
               self.domain,
               port))

    def build_absolute_uri(self, url):
        return "%s%s" % (self.canonical_url, url)
