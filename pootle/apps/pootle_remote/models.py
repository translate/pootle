# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.db import models

from .abstracts import AbstractRemoteProject, AbstractRemoteSite


class RemoteSite(AbstractRemoteSite):
    pass


class RemoteProject(AbstractRemoteProject):
    site = models.ForeignKey(RemoteSite)
