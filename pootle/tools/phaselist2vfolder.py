#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import json


# Config
# Goals file to convert to JSON
phaselistfile = 'firefox.phaselist'
# Name of the project on Pootle
project = "firefox"
# Mapping of goals and priorities, default will be 1.0
priorities = {
    'shared': 1.0,
    'user1': 5.0,
    'lang': 0.9,
    'user2': 4.0,
    'user3': 3.0,
    'config1': 3.0,
    'user4': 2.0,
    'config2': 2.0,
    'install': 1.0,
    'platform': 1.0,
    'other': 0.9,
    '1': 0.9,
    'developers': 0.5,
    'security': 0.4,
    'notnb': 0.3,
    'never': 0.1,
    'langpack': 6.0,
}
# If a goal should be marked as not public
not_public = [
    'notnb',
    'never',
]


vfolders = []

with open(phaselistfile) as phaselist:
    for line in phaselist:
        goal, pofile = line.split("\t")
        goal = goal.strip()
        pofile = pofile.rstrip('\n').strip('.').lstrip('/')
        for vfolder in vfolders:
            if vfolder['name'] == goal:
                vfolder['filters']['files'].append(pofile)
                break
        else:
            priority = 1.0
            if goal in priorities:
                priority = priorities[goal]
            public = True
            if goal in not_public:
                public = False
            vfolders.append({
                'name': goal,
                'location': '/{LANG}/%s/' % project,
                'priority': priority,
                'is_public': public,
                'filters': {
                    'files': [
                        pofile,
                    ]
                }
            })

print json.dumps(vfolders, sort_keys=True, indent=4)
