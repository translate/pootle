# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.


import logging


# Log actions
TRANSLATION_ADDED = 'A'
TRANSLATION_CHANGED = 'C'
TRANSLATION_DELETED = 'D'
UNIT_ADDED = 'UA'
UNIT_OBSOLETE = 'UO'
UNIT_RESURRECTED = 'UR'
UNIT_DELETED = 'UD'
STORE_ADDED = 'SA'
STORE_OBSOLETE = 'SO'
STORE_RESURRECTED = 'SR'
STORE_DELETED = 'SD'
CMD_EXECUTED = 'X'
MUTE_QUALITYCHECK = 'QM'
UNMUTE_QUALITYCHECK = 'QU'
SCORE_CHANGED = 'SC'

PAID_TASK_ADDED = 'PTA'
PAID_TASK_DELETED = 'PTD'


def log(message):
    logger = logging.getLogger('action')
    logger.info(message)


def action_log(*args, **kwargs):
    logger = logging.getLogger('action')
    d = {}
    for p in ['user', 'lang', 'action', 'unit', 'path']:
        d[p] = kwargs.pop(p, '')

    tr = kwargs.pop('translation', '')
    tr = tr.replace("\\", "\\\\")
    tr = tr.replace("\n", "\\\n")
    d['translation'] = tr

    msg = (u"%(user)s\t%(action)s\t%(lang)s\t"
           "%(unit)s\t%(path)s\t%(translation)s" % d)

    logger.info(msg)


def cmd_log(*args, **kwargs):
    import os
    from django.conf import settings

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pootle.settings')
    fn = settings.LOGGING.get('handlers').get('log_action').get('filename')
    dft = settings.LOGGING.get('formatters').get('action').get('datefmt')

    with open(fn, 'a') as logfile:
        cmd = ' '.join(args)

        message = "%(user)s\t%(action)s\t%(cmd)s" % {
            'user': 'system',
            'action': CMD_EXECUTED,
            'cmd': cmd
        }

        from datetime import datetime
        now = datetime.now()
        d = {
            'message': message,
            'asctime': now.strftime(dft)
        }
        logfile.write("[%(asctime)s]\t%(message)s\n" % d)


def store_log(*args, **kwargs):
    logger = logging.getLogger('action')
    d = {}
    for p in ['user', 'path', 'action', 'store']:
        d[p] = kwargs.pop(p, '')

    message = "%(user)s\t%(action)s\t%(path)s\t%(store)s" % d

    logger.info(message)
