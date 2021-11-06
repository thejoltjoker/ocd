#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Setup logging
import logging

LOGGING_CONFIG = {'formatters': {'f': {'format': '%(asctime)s %(name)-12s %(levelname)-8s '
                                                 '%(message)s'}},
                  'handlers': {'h': {'class': 'logging.StreamHandler',
                                     'formatter': 'f',
                                     'level': logging.DEBUG}},
                  'root': {'handlers': ['h'], 'level': logging.DEBUG},
                  'version': 1}
# Define invalid characters and default rules
INVALID_CHARACTERS = r'\/:*?"<>|'
OPERATIONS = ['copy', 'move', 'delete', 'dryrun', 'rename']
TARGETS = ['files','folders','both']
DEFAULT_RULES = {
    'logging': LOGGING_CONFIG,
    'characters': {' ': '_'},
    'groups': {'audio': ['mp3', 'wav'],
               'document': ['txt', 'doc'],
               'picture': ['jpg', 'png']},
    'jobs': [{
        'name': 'defaults',
        'source': '/path/to/folder',
        'destination': '/path/to/folder',
        'operation': 'move',
        'pattern': '*',
        'group': True,
        'cleanup': True,
        'rename': True,
        'subdirs': False,
        'verify': False}],
}
