# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.core.exceptions import ValidationError

from pootle_fs.delegate import fs_translation_mapping_validator, fs_url_validator
from pootle_fs.finder import TranslationMappingValidator
from pootle_fs.localfs import LocalFSPlugin, LocalFSUrlValidator


@pytest.mark.django_db
def test_validator_localfs():
    validator = fs_url_validator.get(LocalFSPlugin)()
    assert isinstance(validator, LocalFSUrlValidator)
    with pytest.raises(ValidationError):
        validator.validate("foo/bar")
    validator.validate("/foo/bar")


@pytest.mark.django_db
def test_validator_translation_mapping():
    validator = fs_translation_mapping_validator.get()("asdf")
    assert isinstance(validator, TranslationMappingValidator)
