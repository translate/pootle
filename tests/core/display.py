# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.


import pytest

from pootle.core.display import Display, ItemDisplay, SectionDisplay


# context can be any dict-like object whose values are non-string iterables
# in this case we wrap the data dict, but we could just provide that dict
# as the context
class DummyDisplayContext(object):

    data = {
        "section1": ["item1", "item2"],
        "section2": None,
        "section3": [],
        "section4": ["some", "more", "iterable", "values"]}

    def __iter__(self):
        for section in self.data:
            yield section

    def __getitem__(self, k):
        return self.data[k]


def test_display_instance():
    context = DummyDisplayContext()
    display = Display(context)
    assert sorted(display.sections) == ["section1", "section4"]
    assert display.context is context
    assert display.section_class == SectionDisplay
    assert display.no_results_msg == ""
    for name in display.sections:
        section = display.section(name)
        assert isinstance(section, SectionDisplay)
        assert section.context is display
        assert section.name == name
    result = ""
    for section in display.sections:
        result += str(display.section(section))
    assert str(display) == "%s\n" % result


def test_display_no_results():

    class DisplayNoResults(Display):

        no_results_msg = "Nothing to see here, move along"

    display = DisplayNoResults({})
    assert str(display) == "%s\n" % DisplayNoResults.no_results_msg


def test_display_section_instance():
    context = DummyDisplayContext()
    display = Display(context)
    section = SectionDisplay(display, "section4")
    assert section.context is display
    assert section.name == "section4"
    assert section.info == dict(title=section.name)
    assert section.data == context[section.name]
    assert section.description == ""
    assert section.title == (
        "%s (%s)"
        % (section.name, len(section.data)))
    assert len(section.items) == len(section.data)
    for i, item_display in enumerate(section.items):
        assert isinstance(item_display, section.item_class)
        assert item_display.item == section.data[i]
    result = (
        "%s\n%s\n\n"
        % (section.title,
           "-" * len(section.title)))
    for item in section:
        result += str(item)
    assert str(section) == "%s\n" % result


def test_display_section_info():
    context = DummyDisplayContext()

    class DisplayWithInfo(Display):
        context_info = dict(
            section4=dict(
                title="Section 4 title",
                description="Section 4 description"))

    display = DisplayWithInfo(context)
    section = display.section("section4")
    assert section.info == display.context_info["section4"]
    assert section.description == section.info["description"]
    assert section.title == (
        "%s (%s)"
        % (section.info["title"], len(section.data)))
    result = (
        "%s\n%s\n%s\n\n"
        % (section.title,
           "-" * len(section.title),
           section.description))
    for item in section:
        result += str(item)
    assert str(section) == "%s\n" % result


def test_display_section_no_info():
    context = DummyDisplayContext()

    class DisplayWithoutInfo(Display):
        context_info = dict(
            section2=dict(
                title="Section 4 title",
                description="Section 4 description"))

    display = DisplayWithoutInfo(context)
    section = display.section("section4")
    assert section.info == dict(title="section4")
    assert section.description == ""
    assert section.title == (
        "%s (%s)"
        % (section.name, len(section.data)))
    result = (
        "%s\n%s\n\n"
        % (section.title,
           "-" * len(section.title)))
    for item in section:
        result += str(item)
    assert str(section) == "%s\n" % result


def test_display_section_bad_items_none():
    display = Display(DummyDisplayContext())
    section = SectionDisplay(display, "section2")
    # in the example section2 would normally be ignored by
    # the Display class, but if a section were created from it
    # it would raise a TypeError
    with pytest.raises(TypeError):
        assert section.items


def test_display_section_bad_items_str():
    display = Display(dict(section1="FOO"))
    section = SectionDisplay(display, "section1")
    assert section.data == "FOO"
    with pytest.raises(TypeError):
        assert section.items


def test_display_item_instance():
    display = Display(DummyDisplayContext())
    section = SectionDisplay(display, "section1")
    item_display = ItemDisplay(section, section.data[0])
    assert item_display.section is section
    assert item_display.item == section.data[0]
    assert str(item_display) == "%s\n" % section.data[0]
