# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from collections import OrderedDict

import pytest

from pytest_pootle.factories import ProjectDBFactory

from pootle.core.delegate import lang_mapper
from pootle_config.utils import ObjectConfig, SiteConfig
from pootle_language.models import Language


@pytest.mark.django_db
def test_lang_mapper_bad_preset(po_directory, english, caplog):
    project = ProjectDBFactory(source_language=english)
    mapper = lang_mapper.get(project.__class__, instance=project)
    assert mapper.lang_mappings == {}
    project_config = ObjectConfig(project)
    project_config[
        "pootle.core.use_lang_mapping_presets"] = ["PRESET_DOES_NOT_EXIST"]
    project.config.reload()
    mapper = lang_mapper.get(project.__class__, instance=project)
    assert mapper.lang_mappings == {}
    assert (
        "Unrecognised lang mapping preset"
        in ''.join([l.message for l in caplog.records]))


@pytest.mark.django_db
def test_lang_mapper_no_config(po_directory, english):
    project = ProjectDBFactory(source_language=english)
    mapper = lang_mapper.get(project.__class__, instance=project)

    # lang exists and its valid
    assert mapper["en"] == english
    assert mapper.get_pootle_code("en") == "en"
    assert mapper.get_upstream_code("en") == "en"
    assert "en" in mapper

    # The lang doesnt exist but its not excluded
    assert mapper["en_FOO"] is None
    assert mapper.get_pootle_code("en_FOO") == "en_FOO"
    assert mapper.get_upstream_code("en_FOO") == "en_FOO"
    assert "en_FOO" not in mapper


@pytest.mark.django_db
def test_lang_mapper_project_config(po_directory, english):
    project = ProjectDBFactory(source_language=english)
    project_config = ObjectConfig(project)
    # upstream_code="en_US", pootle_code="en"
    project_config["pootle.core.lang_mapping"] = dict(en_US="en")
    project.config.reload()
    mapper = lang_mapper.get(project.__class__, instance=project)
    assert mapper["en_US"] == english
    assert mapper.get_pootle_code("en_US") == "en"
    assert mapper.get_upstream_code("en") == "en_US"
    assert "en_US" in mapper

    # as en_US is mapped to pootle's en its not valid as upstream code
    assert mapper.get_upstream_code("en_US") is None
    # as en is mapped to en_US its not valid as a pootle_code
    assert mapper.get_pootle_code("en") is None
    assert "en" not in mapper

    # we can swap codes
    project_config["pootle.core.lang_mapping"] = dict(
        language0="en", en="language0")
    mapper = lang_mapper.get(project.__class__, instance=project)
    project.config.reload()
    language0 = Language.objects.get(code="language0")
    assert mapper["en"] == language0
    assert mapper["language0"] == english
    assert mapper.get_pootle_code("en") == "language0"
    assert mapper.get_pootle_code("language0") == "en"
    assert mapper.get_upstream_code("en") == "language0"
    assert mapper.get_upstream_code("language0") == "en"


@pytest.mark.django_db
def test_lang_mapper_preset_config(po_directory, english):
    project = ProjectDBFactory(source_language=english)
    project_config = ObjectConfig(project)
    site_config = SiteConfig()
    # add the preset
    site_config["pootle.core.lang_mapping_presets"] = dict(
        preset_1=dict(en_US="en"))

    # project not configured yet tho
    mapper = lang_mapper.get(project.__class__, instance=project)
    assert mapper["en_US"] is None
    assert mapper["en"] == english

    # configure project to use preset
    project_config["pootle.core.use_lang_mapping_presets"] = ["preset_1"]
    project.config.reload()
    mapper = lang_mapper.get(project.__class__, instance=project)
    assert mapper["en_US"] == english
    assert mapper["en"] is None


@pytest.mark.django_db
def test_lang_mapper_mappings(po_directory, english):
    project = ProjectDBFactory(source_language=english)
    _test_mapper(project)
    ObjectConfig(project)["pootle.core.lang_mapping"] = dict(lang0="language0")
    _test_mapper(project)
    ObjectConfig(project)["pootle.core.lang_mapping"] = dict(
        lang0="language1", lang1="language0")
    _test_mapper(project)
    SiteConfig()["pootle.core.lang_mapping_presets"] = dict(
        preset_1=dict(lang0="language1", lang1="language0"))
    _test_mapper(project)
    ObjectConfig(project)["pootle.core.lang_mapping"] = dict(
        lang0="language1", lang1="en")
    _test_mapper(project)
    ObjectConfig(project)["pootle.core.use_lang_mapping_presets"] = ["preset_1"]
    _test_mapper(project)
    ObjectConfig(project)["pootle.core.use_lang_mapping_presets"] = [
        "preset_1", "preset_2"]
    _test_mapper(project)
    ObjectConfig(project)["pootle.core.lang_mapping"] = dict(lang1="language1")
    _test_mapper(project, True)


def _test_mapper(project, debug=False):
    project.config.reload()
    mapper = lang_mapper.get(project.__class__, instance=project)
    assert mapper.site_config.items() == SiteConfig().items()
    assert mapper.project.config.items() == ObjectConfig(project).items()
    assert mapper.project_mappings == ObjectConfig(project).get(
        "pootle.core.lang_mapping", {})
    assert mapper.project_presets == ObjectConfig(project).get(
        "pootle.core.use_lang_mapping_presets", [])
    assert mapper.site_presets == SiteConfig().get(
        "pootle.core.lang_mapping_presets", {})

    _preset_mappings = OrderedDict()
    for preset_name in mapper.project_presets:
        if preset_name not in mapper.site_presets:
            continue
        _preset_mappings.update(
            mapper.site_presets[preset_name])

    assert mapper.mappings_from_presets == _preset_mappings

    _mapping = OrderedDict()

    def _add_lang_to_mapping(upstream_code, pootle_code):
        # as its a 1 to 1 mapping remove any previous items with
        # same value
        if pootle_code in _mapping.values():
            for k, v in _mapping.items():
                if v == pootle_code:
                    del _mapping[k]
                    break
        _mapping[upstream_code] = pootle_code
    mappings = OrderedDict(mapper.mappings_from_presets)
    mappings.update(OrderedDict(mapper.project_mappings))
    for upstream_code, pootle_code in mappings.items():
        _add_lang_to_mapping(upstream_code, pootle_code)

    assert mapper.lang_mappings == _mapping
    assert len(_mapping.values()) == len(set(_mapping.values()))
