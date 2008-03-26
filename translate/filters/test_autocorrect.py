#!/usr/bin/env python
# -*- coding: utf-8 -*-

from translate.filters import autocorrect

class TestAutocorrect:

    def correct(self, msgid, msgstr, expected):
        """helper to run correct function from autocorrect module"""
        corrected = autocorrect.correct(msgid, msgstr)
        print msgid
        print msgstr
        print corrected
        assert corrected == expected

    def test_correct_ellipsis(self):
        """test that we convert single ... to three dots"""
        self.correct("String...", "String…", "String...")

    def test_correct_spacestart_spaceend(self):
        """test that we can correct leading and trailing space errors"""
        self.correct("Simple string", "Dimpled ring  ", "Dimpled ring")
        self.correct("Simple string", "  Dimpled ring", "Dimpled ring")
        self.correct("  Simple string", "Dimpled ring", "  Dimpled ring")
        self.correct("Simple string  ", "Dimpled ring", "Dimpled ring  ")

    def test_correct_start_capitals(self):
        """test that we can correct the starting capital"""
        self.correct("Simple string", "dimpled ring", "Dimpled ring")
        self.correct("simple string", "Dimpled ring", "dimpled ring")

    def test_correct_end_punc(self):
        """test that we can correct end punctuation"""
        self.correct("Simple string:", "Dimpled ring", "Dimpled ring:")
        #self.correct("Simple string: ", "Dimpled ring", "Dimpled ring: ")
        self.correct("Simple string.", "Dimpled ring", "Dimpled ring.")
        #self.correct("Simple string. ", "Dimpled ring", "Dimpled ring. ")
        self.correct("Simple string?", "Dimpled ring", "Dimpled ring?")
