# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.


import logging


# Log actions
STORE_ADDED = 'SA'
STORE_OBSOLETE = 'SO'
STORE_RESURRECTED = 'SR'
STORE_DELETED = 'SD'
CMD_EXECUTED = 'X'
SCORE_CHANGED = 'SC'


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

    logger.debug(message)
