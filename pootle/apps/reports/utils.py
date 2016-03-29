# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.


def get_grouped_word_stats(scores, user=None, month=None):
    result = []
    tp = None
    for score in scores:
        if tp != score.submission.translation_project:
            tp = score.submission.translation_project
            row = {
                'translation_project': u'%s / %s' % (tp.project.fullname,
                                                     tp.language.fullname),
                'project_code': tp.project.code,
                'score_delta': 0,
                'translated': 0,
                'reviewed': 0,
                'suggested': 0,
            }
            if user is not None:
                submissions_filter = {
                    'state': 'user-submissions',
                    'user': user.username,
                }
                suggestions_filter = {
                    'state': 'user-suggestions',
                    'user': user.username,
                }
                if month is not None:
                    submissions_filter['month'] = month
                    suggestions_filter['month'] = month

                row['tp_browse_url'] = tp.get_absolute_url()
                row['tp_submissions_translate_url'] = \
                    tp.get_translate_url(**submissions_filter)
                row['tp_suggestions_translate_url'] = \
                    tp.get_translate_url(**suggestions_filter)

            result.append(row)

        translated_words, reviewed_words = score.get_paid_wordcounts()
        if translated_words is not None:
            row['translated'] += translated_words
        if reviewed_words is not None:
            row['reviewed'] += reviewed_words
        row['score_delta'] += score.score_delta

        suggested_words = score.get_suggested_wordcount()
        if suggested_words is not None:
            row['suggested'] += suggested_words

    return sorted(result, key=lambda x: x['translation_project'])
