#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2009 Zuza Software Foundation
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

"""measure precision and recall of a spell checker based on previously
checked corpus"""

import sys
import string
import enchant
from optparse import OptionParser

def spell_quality(lang, correct_filename, incorrect_filename):
    """calculate and print spellchecker Precision, Recall and Accuracy
    check http://en.wikipedia.org/wiki/Precision_and_Recall for
    explanation of these measures"""
    #prepare
    speller = enchant.Dict(lang)
    correct = open(correct_filename).read().decode('utf-8').split(u'\n')
    incorrect = open(incorrect_filename).read().decode('utf-8').split(u'\n')

    (tp, fp, tn, fn) = measure_spell_quality(speller, correct, incorrect)
    print "tp: %d" % tp, "fp: %d" % fp, "tn: %d" % tn, "fn: %d" % fn

    precision = float(tp) / (tp + fp)
    recall = float(tp) / (tp + fn)
    accuracy = 2 * (precision * recall) / (precision + recall)

    print "Precision: %d%%" % (precision * 100)
    print "Recall: %d%%" % (recall * 100)
    print "Accuracy: %d%%" % (accuracy * 100)

    nprecision = float(tn) / (tn + fn)
    nrecall = float(tn) / (tn + fp)
    naccuracy = 2 * (nprecision * nrecall) / (nprecision + nrecall)
    print "Negative Precision: %d%%" % (nprecision * 100)
    print "Negative Recall (Specificity): %d%%" % (nrecall * 100)
    print "Negative Accuracy: %d%%" % (naccuracy * 100)

def measure_spell_quality(speller, correct, incorrect):
    """counts true positive (tp), false positives (fp), true negatives
    (tn) and false negatives (fn)"""
    #measure tp and fn first
    tp = 0
    fn = 0
    fp = 0
    tn = 0
    for word in correct:
        if word:
            if speller.check(word):
                tp += 1
            else:
                fn += 1

    #letters = "abcdefghijklmnopqrstuvwxyz"

    #measure tn and fn now
    for word in incorrect:
        if word:
            #import random
            #letter = letters[random.randint(0,len(letters)-1)]
            #i = random.randint(0, len(word)-1)
            #word = word[:i] + letter + word [i:]
            if speller.check(word):
                fp += 1
            else:
                tn += 1


    return (tp, fp, tn, fn)

def main(argv=None):
    parser = OptionParser()
    parser.add_option("-c", "--correct", dest="correct",
                      help="file containing list of correct words")
    parser.add_option("-i", "--incorrect", dest="incorrect",
                      help="file containing list of incorrect words")
    parser.add_option("-l", "--language", dest="lang",
                      help="spellchecker language code")

    (options, args) = parser.parse_args()

    spell_quality(options.lang, options.correct, options.incorrect)

if __name__ == '__main__':
    main()
