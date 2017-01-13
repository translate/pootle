# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.conf.urls import url

from .views import (
    ProjectFSAdminView, ProjectFSFetchAdminView, ProjectFSStateAdminView,
    ProjectFSStateConflictingAdminView, ProjectFSStateTrackedAdminView,
    ProjectFSStateUnsyncedAdminView, ProjectFSStateUntrackedAdminView)


urlpatterns = [
    url(r'^admin/projects/(?P<project_code>[^/]*)/fs/?$',
        ProjectFSAdminView.as_view(),
        name='pootle-admin-project-fs'),
    url(r'^admin/projects/(?P<project_code>[^/]*)/fs/fetch/?$',
        ProjectFSFetchAdminView.as_view(),
        name='pootle-admin-project-fs-fetch'),
    url(r'^admin/projects/(?P<project_code>[^/]*)/fs/state/?$',
        ProjectFSStateAdminView.as_view(),
        name='pootle-admin-project-fs-state'),
    url(r'^admin/projects/(?P<project_code>[^/]*)/fs/state/tracked/?$',
        ProjectFSStateTrackedAdminView.as_view(),
        name='pootle-admin-project-fs-state-tracked'),
    url(r'^admin/projects/(?P<project_code>[^/]*)/fs/state/untracked/?$',
        ProjectFSStateUntrackedAdminView.as_view(),
        name='pootle-admin-project-fs-state-untracked'),
    url(r'^admin/projects/(?P<project_code>[^/]*)/fs/state/unsynced/?$',
        ProjectFSStateUnsyncedAdminView.as_view(),
        name='pootle-admin-project-fs-state-unsynced'),
    url(r'^admin/projects/(?P<project_code>[^/]*)/fs/state/conflicting/?$',
        ProjectFSStateConflictingAdminView.as_view(),
        name='pootle-admin-project-fs-state-conflicting')]
