# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from collections import OrderedDict

import pytest

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

from pootle.core.delegate import config
from pootle.core.plugin import getter
from pootle_config.delegate import (
    config_should_not_be_set, config_should_not_be_appended)
from pootle_config.exceptions import ConfigurationError
from pootle_config.models import Config
from pootle_config.utils import (
    ConfigDict, ModelConfig, ObjectConfig, SiteConfig)
from pootle_project.models import Project


def _test_config_bad_create(create_func):

    # a config object must have a key
    with pytest.raises(ValidationError):
        create_func().save()

    # you cant set object_pk if content_type is not set
    with pytest.raises(ValidationError):
        create_func(
            key="foo4", value="bar", object_pk="23").save()


def _test_config_ob(**kwargs):
    conf = Config.objects.get(
        content_type=kwargs["content_type"],
        object_pk=kwargs["object_pk"])

    for k, v in kwargs.items():
        if isinstance(v, tuple):
            v = list(v)
        assert getattr(conf, k) == v


def _test_config_create(create_func):

    # Create a site config
    create_func(key="foo")
    _test_config_ob(
        key=u"foo",
        value="",
        content_object=None,
        content_type=None,
        object_pk=None)

    project = Project.objects.get(code="project0")
    project_pk = str(project.pk)
    project_ct = ContentType.objects.get_for_model(project)

    # Create config for all projects
    create_func(
        key="foo",
        value="bar",
        content_type=project_ct)
    _test_config_ob(
        key=u"foo",
        value=u"bar",
        content_object=None,
        content_type=project_ct,
        object_pk=None)

    # Create config for a project
    create_func(
        key="foo",
        value="bar",
        content_object=project)
    _test_config_ob(
        key=u"foo",
        value=u"bar",
        content_object=project,
        content_type=project_ct,
        object_pk=project_pk)


def _test_config_clear(**kwargs):
    Config.objects.set_config(**kwargs)
    if kwargs.get("model"):
        conf = Config.objects.config_for(
            kwargs["model"]).get(key=kwargs["key"])
    else:
        conf = Config.objects.site_config().get(key=kwargs["key"])
    assert conf.pk in Config.objects.values_list("pk", flat=True)
    Config.objects.clear_config(**kwargs)
    assert conf.pk not in Config.objects.values_list("pk", flat=True)


@pytest.mark.django_db
def test_config_create(no_config_env):
    _test_config_create(Config.objects.create)
    _test_config_create(Config)


@pytest.mark.django_db
def test_config_bad_create(no_config_env):
    _test_config_bad_create(Config.objects.create)
    _test_config_bad_create(Config)


@pytest.mark.django_db
def test_config_bad_getter(no_config_env):
    project = Project.objects.get(code="project0")
    with pytest.raises(ConfigurationError):
        config.get(instance=project)
    with pytest.raises(ConfigurationError):
        config.get(str, instance=project)


@pytest.mark.django_db
def test_config_set(no_config_env):

    # set site-wide config
    Config.objects.set_config("foo")
    _test_config_ob(
        key=u"foo",
        value="",
        content_type=None,
        object_pk=None)
    Config.objects.set_config("foo", "bar")
    _test_config_ob(
        key=u"foo",
        value="bar",
        content_type=None,
        object_pk=None)

    project = Project.objects.get(code="project0")
    project_pk = project.pk
    project_ct = ContentType.objects.get_for_model(project)

    # set config for all projects
    Config.objects.set_config(key="foo", model=Project)
    _test_config_ob(
        key="foo",
        value="",
        content_type=project_ct,
        object_pk=None,
        content_object=None)
    Config.objects.set_config(key="foo", value="bar", model=Project)
    _test_config_ob(
        key="foo",
        value="bar",
        content_type=project_ct,
        object_pk=None,
        content_object=None)

    # set config for project
    Config.objects.set_config(key="foo", model=project)
    _test_config_ob(
        key="foo",
        value="",
        content_type=project_ct,
        object_pk=str(project_pk),
        content_object=project)
    # reset config for project
    Config.objects.set_config(key="foo", value="bar", model=project)
    _test_config_ob(
        key="foo",
        value="bar",
        content_type=project_ct,
        object_pk=str(project_pk),
        content_object=project)


@pytest.mark.django_db
def test_config_clear(no_config_env):
    _test_config_clear(**dict(key="foo"))
    _test_config_clear(**dict(key="foo", model=Project))
    project = Project.objects.get(code="project0")
    _test_config_clear(**dict(key="foo", model=project))


@pytest.mark.django_db
def test_config_get(no_config_env):
    Config.objects.set_config("foo", ["bar"])
    assert Config.objects.get_config("foo") == ["bar"]

    Config.objects.set_config("foo", ["bar2"], Project)
    assert Config.objects.get_config("foo") == ["bar"]
    assert Config.objects.get_config("foo", Project) == ["bar2"]

    project = Project.objects.get(code="project0")
    Config.objects.set_config("foo", ["bar3"], project)
    assert Config.objects.get_config("foo") == ["bar"]
    assert Config.objects.get_config("foo", Project) == ["bar2"]

    assert Config.objects.get_config("foo", project) == ["bar3"]


@pytest.mark.django_db
def test_config_list(no_config_env):
    Config.objects.set_config("foo", ["bar"])
    assert Config.objects.list_config("foo") == [("foo", ["bar"])]

    Config.objects.set_config("foo", ["bar2"], Project)
    assert Config.objects.list_config("foo") == [("foo", ["bar"])]
    assert Config.objects.list_config("foo", Project) == [("foo", ["bar2"])]

    project = Project.objects.get(code="project0")
    Config.objects.set_config("foo", ["bar3"], project)
    assert Config.objects.list_config("foo") == [("foo", ["bar"])]
    assert Config.objects.list_config("foo", Project) == [("foo", ["bar2"])]
    assert Config.objects.list_config("foo", project) == [("foo", ["bar3"])]


@pytest.mark.django_db
def test_config_append(no_config_env):
    Config.objects.append_config("foo", ["bar"])
    assert Config.objects.list_config("foo") == [("foo", ["bar"])]
    Config.objects.append_config("foo", ["bar"])
    assert Config.objects.list_config("foo") == [
        ("foo", ["bar"]), ("foo", ["bar"])]

    Config.objects.set_config("foo", ["bar2"], Project)
    assert Config.objects.list_config("foo") == [
        ("foo", ["bar"]), ("foo", ["bar"])]
    assert Config.objects.list_config("foo", Project) == [
        ("foo", ["bar2"])]
    Config.objects.append_config("foo", ["bar2"], Project)
    assert Config.objects.list_config("foo") == [
        ("foo", ["bar"]), ("foo", ["bar"])]
    assert Config.objects.list_config("foo", Project) == [
        ("foo", ["bar2"]), ("foo", ["bar2"])]

    project = Project.objects.get(code="project0")
    Config.objects.set_config("foo", ["bar3"], project)
    assert Config.objects.list_config("foo") == [
        ("foo", ["bar"]), ("foo", ["bar"])]
    assert Config.objects.list_config("foo", Project) == [
        ("foo", ["bar2"]), ("foo", ["bar2"])]
    assert Config.objects.list_config("foo", project) == [
        ("foo", ["bar3"])]
    Config.objects.append_config("foo", ["bar3"], project)
    assert Config.objects.list_config("foo") == [
        ("foo", ["bar"]), ("foo", ["bar"])]
    assert Config.objects.list_config("foo", Project) == [
        ("foo", ["bar2"]), ("foo", ["bar2"])]
    assert Config.objects.list_config("foo", project) == [
        ("foo", ["bar3"]), ("foo", ["bar3"])]


@pytest.mark.django_db
def test_config_getter(no_config_env):
    # getting a non-existent key returns None
    assert config.get(key="DOESNT_EXIST") is None

    Config.objects.set_config("foo", ["bar"])
    # if key is not specified to the getter it returns the qs
    assert config.get().get(key="foo").value == ["bar"]
    # you can use get_config(key) with the qs
    assert config.get().get_config("foo") == ["bar"]
    # if key is specified it returns the key value
    assert config.get(key="foo") == ["bar"]

    Config.objects.set_config("foo", ["bar2"], Project)
    # previous tests still work
    assert config.get().get(key="foo").value == ["bar"]
    assert config.get().get_config("foo") == ["bar"]
    assert config.get(key="foo") == ["bar"]
    # specifying only model gets the queryset
    assert config.get(Project).get(key="foo").value == ["bar2"]
    # which we can use get_config with
    assert config.get(Project).get_config("foo") == ["bar2"]
    # specifying key also gets the value
    assert config.get(Project, key="foo") == ["bar2"]

    project = Project.objects.get(code="project0")
    Config.objects.set_config("foo", ["bar3"], project)
    # previous tests still work
    assert config.get().get(key="foo").value == ["bar"]
    assert config.get().get_config("foo") == ["bar"]
    assert config.get(key="foo") == ["bar"]
    assert config.get(Project).get(key="foo").value == ["bar2"]
    assert config.get(Project).get_config("foo") == ["bar2"]
    assert config.get(Project, key="foo") == ["bar2"]

    # we can get settings for an indiv project like so...
    assert config.get(Project, instance=project).get(key="foo").value == ["bar3"]
    assert config.get(Project, instance=project).get_config("foo") == ["bar3"]
    assert config.get(Project, instance=project, key="foo") == ["bar3"]


@pytest.mark.django_db
def test_config_getter_list(no_config_env):
    assert config.get(key=[]) == []

    config.get().set_config("foo", ["bar0"])
    config.get().append_config("foo", ["bar0"])

    with pytest.raises(ConfigurationError):
        config.get(key="foo")

    # if we pass a list as key we get a k, v list mapping
    assert config.get(key=["foo"]) == [
        (u'foo', [u'bar0']), (u'foo', [u'bar0'])]
    assert config.get(key=[]) == [
        (u'foo', [u'bar0']), (u'foo', [u'bar0'])]

    config.get().set_config("foo2", ["bar1"])

    # this still works
    assert config.get(key=["foo"]) == [
        (u'foo', [u'bar0']), (u'foo', [u'bar0'])]

    # this still works
    assert config.get(key=["foo2"]) == [(u'foo2', [u'bar1'])]

    # both keys are returned for key=[]
    assert config.get(key=[]) == [
        (u'foo', [u'bar0']),
        (u'foo', [u'bar0']),
        (u'foo2', [u'bar1'])]

    assert config.get(Project, key=[]) == []

    config.get(Project).set_config("foo", ["bar2"])
    config.get(Project).append_config("foo", ["bar2"])

    with pytest.raises(ConfigurationError):
        config.get(Project, key="foo")

    # if we pass a list as key we get a k, v list mapping
    assert config.get(Project, key=["foo"]) == [
        (u'foo', [u'bar2']), (u'foo', [u'bar2'])]
    assert config.get(Project, key=[]) == [
        (u'foo', [u'bar2']), (u'foo', [u'bar2'])]

    config.get(Project).set_config("foo2", ["bar3"])

    # this still works
    assert config.get(Project, key=["foo"]) == [
        (u'foo', [u'bar2']), (u'foo', [u'bar2'])]

    # this still works
    assert config.get(
        Project, key=["foo2"]) == [(u'foo2', [u'bar3'])]

    # both keys are returned for key=[]
    assert config.get(Project, key=[]) == [
        (u'foo', [u'bar2']),
        (u'foo', [u'bar2']),
        (u'foo2', [u'bar3'])]

    # site config still works
    assert config.get(key=[]) == [
        (u'foo', [u'bar0']),
        (u'foo', [u'bar0']),
        (u'foo2', [u'bar1'])]

    project = Project.objects.get(code="project0")
    assert config.get(
        Project, instance=project, key=[]) == []

    config.get(
        Project,
        instance=project).set_config("foo", ["bar3"])
    config.get(
        Project,
        instance=project).append_config("foo", ["bar3"])

    with pytest.raises(ConfigurationError):
        config.get(Project, instance=project, key="foo")

    # if we pass a list as key we get a k, v list mapping
    assert config.get(Project, instance=project, key=["foo"]) == [
        (u'foo', [u'bar3']), (u'foo', [u'bar3'])]
    assert config.get(Project, instance=project, key=[]) == [
        (u'foo', [u'bar3']), (u'foo', [u'bar3'])]

    config.get(Project, instance=project).set_config("foo2", ["bar4"])

    # this still works
    assert config.get(Project, instance=project, key=["foo"]) == [
        (u'foo', [u'bar3']), (u'foo', [u'bar3'])]

    # this still works
    assert config.get(
        Project,
        instance=project,
        key=["foo2"]) == [(u'foo2', [u'bar4'])]

    # both keys are returned for key=[]
    assert config.get(Project, instance=project, key=[]) == [
        (u'foo', [u'bar3']),
        (u'foo', [u'bar3']),
        (u'foo2', [u'bar4'])]

    # model config still works
    assert config.get(Project, key=[]) == [
        (u'foo', [u'bar2']),
        (u'foo', [u'bar2']),
        (u'foo2', [u'bar3'])]

    # site config still works
    assert config.get(key=[]) == [
        (u'foo', [u'bar0']),
        (u'foo', [u'bar0']),
        (u'foo2', [u'bar1'])]


@pytest.mark.django_db
def test_config_setter(no_config_env):
    config.get().set_config("foo", ["bar"])
    assert config.get(key="foo") == ["bar"]

    config.get(Project).set_config("foo", ["bar2"])
    assert config.get(Project, key="foo") == ["bar2"]

    project = Project.objects.get(code="project0")
    config.get(Project).set_config("foo", ["bar3"], project)
    assert config.get(Project, instance=project, key="foo") == ["bar3"]


@pytest.mark.django_db
def test_config_set_json(no_config_env, json_objects):

    # set site-wide config
    Config.objects.set_config("foo", json_objects)
    _test_config_ob(
        key=u"foo",
        value=json_objects,
        content_type=None,
        object_pk=None)

    project = Project.objects.get(code="project0")
    project_pk = project.pk
    project_ct = ContentType.objects.get_for_model(project)

    # set config for all projects
    Config.objects.set_config("foo", json_objects, model=Project)
    _test_config_ob(
        key="foo",
        value=json_objects,
        content_type=project_ct,
        object_pk=None,
        content_object=None)

    # set config for project
    Config.objects.set_config("foo", json_objects, model=project)
    _test_config_ob(
        key="foo",
        value=json_objects,
        content_type=project_ct,
        object_pk=str(project_pk),
        content_object=project)


@pytest.mark.django_db
def test_config_no_set(no_config_env):

    @getter(config_should_not_be_set)
    def config_should_be_set_checker(**kwargs):
        if kwargs["key"] == "foo":
            return True

    with pytest.raises(ConfigurationError):
        config.get().set_config("foo", "bar")
    config.get().set_config("foo2", "bar")

    @getter(config_should_not_be_set, sender=Project)
    def config_should_be_set_model_checker(**kwargs):
        if kwargs["key"] == "foo2":
            return True

    config.get().set_config("foo2", "bar")
    with pytest.raises(ConfigurationError):
        config.get(Project).set_config("foo2", "bar")
    config.get(Project).set_config("foo3", "bar")


@pytest.mark.django_db
def test_config_no_append(no_config_env):

    @getter(config_should_not_be_appended)
    def config_should_be_appended_checker(**kwargs):
        if kwargs["key"] == "foo":
            return True

    with pytest.raises(ConfigurationError):
        config.get().append_config("foo", "bar")
    config.get().append_config("foo2", "bar")

    @getter(config_should_not_be_appended, sender=Project)
    def config_should_be_appended_model_checker(**kwargs):
        if kwargs["key"] == "foo2":
            return True

    config.get().append_config("foo2", "bar")
    with pytest.raises(ConfigurationError):
        config.get(Project).append_config("foo2", "bar")
    config.get(Project).append_config("foo3", "bar")


@pytest.mark.django_db
def test_config_site_util(no_config_env):
    conf = SiteConfig()
    assert conf.items() == conf.values() == conf.keys() == []
    # keys are returned order by key
    other_dict = OrderedDict()
    other_dict["foo.a"] = "bar"
    other_dict["foo.b"] = dict(bar=23)
    other_dict["foo.c"] = [1, 2, 3]
    conf["foo.a"] = "bar"
    conf["foo.b"] = dict(bar=23)
    conf["foo.c"] = [1, 2, 3]
    assert conf.items() == other_dict.items()
    assert conf.values() == other_dict.values()
    assert conf.keys() == other_dict.keys()
    assert [x for x in conf] == other_dict.keys()
    assert all(x in conf for x in other_dict)
    assert all(conf[k] == v for k, v in other_dict.items())
    assert all(conf.get(k) == v for k, v in other_dict.items())
    assert conf.get("DOESNOTEXIST") is None
    assert conf.get("DOESNOTEXIST", "foo") == "foo"
    with pytest.raises(KeyError):
        conf["DOESNOTEXIST"]
    assert SiteConfig().items() == other_dict.items()
    assert SiteConfig().values() == other_dict.values()
    assert SiteConfig().keys() == other_dict.keys()
    assert [x for x in SiteConfig()] == other_dict.keys()
    assert all(x in SiteConfig() for x in other_dict)
    assert all(SiteConfig()[k] == v for k, v in other_dict.items())
    assert all(SiteConfig().get(k) == v for k, v in other_dict.items())
    assert SiteConfig().get("DOESNOTEXIST") is None
    assert SiteConfig().get("DOESNOTEXIST", "foo") == "foo"
    with pytest.raises(KeyError):
        SiteConfig()["DOESNOTEXIST"]


@pytest.mark.django_db
def test_config_model_util(no_config_env):
    conf = ModelConfig(Project)
    assert conf.items() == conf.values() == conf.keys() == []
    # keys are returned order by key
    other_dict = OrderedDict()
    other_dict["foo.a"] = "bar"
    other_dict["foo.b"] = dict(bar=23)
    other_dict["foo.c"] = [1, 2, 3]
    conf["foo.a"] = "bar"
    conf["foo.b"] = dict(bar=23)
    conf["foo.c"] = [1, 2, 3]
    assert conf.items() == other_dict.items()
    assert conf.values() == other_dict.values()
    assert conf.keys() == other_dict.keys()
    assert [x for x in conf] == other_dict.keys()
    assert all(x in conf for x in other_dict)
    assert all(conf[k] == v for k, v in other_dict.items())
    assert all(conf.get(k) == v for k, v in other_dict.items())
    assert conf.get("DOESNOTEXIST") is None
    assert conf.get("DOESNOTEXIST", "foo") == "foo"
    with pytest.raises(KeyError):
        conf["DOESNOTEXIST"]
    assert ModelConfig(Project).items() == other_dict.items()
    assert ModelConfig(Project).values() == other_dict.values()
    assert ModelConfig(Project).keys() == other_dict.keys()
    assert [x for x in ModelConfig(Project)] == other_dict.keys()
    assert all(x in ModelConfig(Project) for x in other_dict)
    assert all(ModelConfig(Project)[k] == v for k, v in other_dict.items())
    assert all(ModelConfig(Project).get(k) == v for k, v in other_dict.items())
    assert ModelConfig(Project).get("DOESNOTEXIST") is None
    assert ModelConfig(Project).get("DOESNOTEXIST", "foo") == "foo"
    with pytest.raises(KeyError):
        ModelConfig(Project)["DOESNOTEXIST"]


@pytest.mark.django_db
def test_config_object_util(no_config_env):
    project = Project.objects.first()
    conf = ObjectConfig(project)
    assert conf.items() == conf.values() == conf.keys() == []
    # keys are returned order by key
    other_dict = OrderedDict()
    other_dict["foo.a"] = "bar"
    other_dict["foo.b"] = dict(bar=23)
    other_dict["foo.c"] = [1, 2, 3]
    conf["foo.a"] = "bar"
    conf["foo.b"] = dict(bar=23)
    conf["foo.c"] = [1, 2, 3]
    assert conf.items() == other_dict.items()
    assert conf.values() == other_dict.values()
    assert conf.keys() == other_dict.keys()
    assert [x for x in conf] == other_dict.keys()
    assert all(x in conf for x in other_dict)
    assert all(conf[k] == v for k, v in other_dict.items())
    assert all(conf.get(k) == v for k, v in other_dict.items())
    assert conf.get("DOESNOTEXIST") is None
    assert conf.get("DOESNOTEXIST", "foo") == "foo"
    with pytest.raises(KeyError):
        conf["DOESNOTEXIST"]
    assert ObjectConfig(project).items() == other_dict.items()
    assert ObjectConfig(project).values() == other_dict.values()
    assert ObjectConfig(project).keys() == other_dict.keys()
    assert [x for x in ObjectConfig(project)] == other_dict.keys()
    assert all(x in ObjectConfig(project) for x in other_dict)
    assert all(ObjectConfig(project)[k] == v for k, v in other_dict.items())
    assert all(ObjectConfig(project).get(k) == v for k, v in other_dict.items())
    assert ObjectConfig(project).get("DOESNOTEXIST") is None
    assert ObjectConfig(project).get("DOESNOTEXIST", "foo") == "foo"
    with pytest.raises(KeyError):
        ObjectConfig(project)["DOESNOTEXIST"]


@pytest.mark.django_db
def test_config_util_dict(no_config_env):
    with pytest.raises(NotImplementedError):
        ConfigDict("foo")["bar"]


@pytest.mark.django_db
def test_config_qs_chaining(no_config_env):

    config.get().set_config("foo", "bar")
    assert config.get().none().get_config("foo") == "bar"

    config.get(Project).set_config("foo", "bar2")
    assert config.get(Project).none().get_config("foo") == "bar2"

    project = Project.objects.get(code="project0")
    config.get(Project, instance=project).set_config("foo", "bar3")
    assert config.get(
        Project, instance=project).none().get_config("foo") == "bar3"
