# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.dispatch import receiver

from pootle.core.signals import config_updated
from pootle_config.utils import ModelConfig, SiteConfig


@pytest.mark.django_db
def test_signal_object_config_set(project0):
    signal_recv = config_updated.receivers
    signal_cache = config_updated.sender_receivers_cache

    class Result(object):
        pass
    result = Result()

    @receiver(config_updated, sender=project0.__class__)
    def project_config_updated(**kwargs):
        result.sender = kwargs["sender"]
        result.instance = kwargs["instance"]
        result.key = kwargs["key"]
        result.value = kwargs["value"]
        result.old_value = kwargs["old_value"]

    project0.config["foo.setting"] = 1
    assert result.sender == project0.__class__
    assert result.instance == project0
    assert result.key == "foo.setting"
    assert result.value == 1
    assert result.old_value is None

    project0.config["foo.setting"] = 2
    assert result.instance == project0
    assert result.key == "foo.setting"
    assert result.value == 2
    assert result.old_value == 1

    config_updated.receivers = signal_recv
    config_updated.sender_receivers_cache = signal_cache


@pytest.mark.django_db
def test_signal_model_config_set(project0):
    signal_recv = config_updated.receivers
    signal_cache = config_updated.sender_receivers_cache

    class Result(object):
        pass
    result = Result()

    @receiver(config_updated, sender=project0.__class__)
    def project_model_config_updated(**kwargs):
        result.sender = kwargs["sender"]
        result.instance = kwargs["instance"]
        result.key = kwargs["key"]
        result.value = kwargs["value"]
        result.old_value = kwargs["old_value"]

    config = ModelConfig(project0.__class__)
    config["foo.setting"] = 1
    assert result.sender == project0.__class__
    assert result.instance is None
    assert result.key == "foo.setting"
    assert result.value == 1
    assert result.old_value is None

    config["foo.setting"] = 2
    assert result.sender == project0.__class__
    assert result.instance is None
    assert result.key == "foo.setting"
    assert result.value == 2
    assert result.old_value == 1

    config_updated.receivers = signal_recv
    config_updated.sender_receivers_cache = signal_cache


@pytest.mark.django_db
def test_signal_site_config_set(project0):
    signal_recv = config_updated.receivers
    signal_cache = config_updated.sender_receivers_cache

    class Result(object):
        pass
    result = Result()

    @receiver(config_updated, sender=type(None))
    def site_config_updated(**kwargs):
        result.sender = kwargs["sender"]
        result.instance = kwargs["instance"]
        result.key = kwargs["key"]
        result.value = kwargs["value"]
        result.old_value = kwargs["old_value"]

    config = SiteConfig()
    config["foo.setting"] = 1
    assert isinstance(None, result.sender)
    assert result.instance is None
    assert result.key == "foo.setting"
    assert result.value == 1
    assert result.old_value is None

    config["foo.setting"] = 2
    assert isinstance(None, result.sender)
    assert result.instance is None
    assert result.key == "foo.setting"
    assert result.value == 2
    assert result.old_value == 1

    config_updated.receivers = signal_recv
    config_updated.sender_receivers_cache = signal_cache
