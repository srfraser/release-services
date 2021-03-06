# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import base64
import os

import cli_common.taskcluster
import treestatus_api.config

DEBUG = bool(os.environ.get('DEBUG', False))


# -- LOAD SECRETS -------------------------------------------------------------

required = [
    'SECRET_KEY_BASE64',
    'DATABASE_URL',
    'AUTH_DOMAIN',
    'AUTH_CLIENT_ID',
    'AUTH_CLIENT_SECRET',
    'AUTH_REDIRECT_URI',
]

if not DEBUG:
    required += [
        'REDIS_URL',
        'PULSE_USER',
        'PULSE_TREESTATUS_EXCHANGE',
        'PULSE_USE_SSL',
        'PULSE_CONNECTION_TIMEOUT',
        'PULSE_HOST',
        'PULSE_PORT',
        'PULSE_USER',
        'PULSE_PASSWORD',
        'PULSE_VIRTUAL_HOST',
    ]

secrets = cli_common.taskcluster.get_secrets(
    os.environ.get('TASKCLUSTER_SECRET'),
    treestatus_api.config.PROJECT_NAME,
    required=required,
    existing={x: os.environ.get(x) for x in required if x in os.environ},
    taskcluster_client_id=os.environ.get('TASKCLUSTER_CLIENT_ID'),
    taskcluster_access_token=os.environ.get('TASKCLUSTER_ACCESS_TOKEN'),
)

locals().update(secrets)

SECRET_KEY = base64.b64decode(secrets['SECRET_KEY_BASE64'])


# -- DATABASE -----------------------------------------------------------------

SQLALCHEMY_TRACK_MODIFICATIONS = False

if DEBUG:
    SQLALCHEMY_ECHO = True

# We require DATABASE_URL set by environment variables for branches deployed to Dockerflow.
if secrets['APP_CHANNEL'] in ('testing', 'staging', 'production'):
    if 'DATABASE_URL' not in os.environ:
        SQLALCHEMY_DATABASE_URI = secrets['DATABASE_URL']
        # XXX: until we only deploy to GCP
        # raise RuntimeError(f'DATABASE_URL has to be set as an environment variable, when '
        #                    f'APP_CHANNEL is set to {secrets["APP_CHANNEL"]}')
    else:
        SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
else:
    SQLALCHEMY_DATABASE_URI = secrets['DATABASE_URL']


# -- CACHE --------------------------------------------------------------------

CACHE = {
    x: os.environ.get(x)
    for x in os.environ.keys()
    if x.startswith('CACHE_')
}

if 'CACHE_DEFAULT_TIMEOUT' not in CACHE:
    CACHE['CACHE_DEFAULT_TIMEOUT'] = 60 * 5
else:
    CACHE['CACHE_DEFAULT_TIMEOUT'] = float(CACHE['CACHE_DEFAULT_TIMEOUT'])

if 'CACHE_KEY_PREFIX' not in CACHE:
    CACHE['CACHE_KEY_PREFIX'] = treestatus_api.config.PROJECT_NAME + '-'

# We require REDIS_URL set by environment variables for branches deployed to Dockerflow.
if secrets['APP_CHANNEL'] in ('testing', 'staging', 'production'):
    CACHE['CACHE_TYPE'] = 'redis'
    if 'REDIS_URL' not in os.environ:
        CACHE['CACHE_REDIS_URL'] = secrets['REDIS_URL']
        # XXX: until we only deploy to GCP
        # raise RuntimeError(f'REDIS_URL has to be set as an environment variable, when '
        #                    f'APP_CHANNEL is set to {secrets["APP_CHANNEL"]}')
    else:
        CACHE['CACHE_REDIS_URL'] = os.environ['REDIS_URL']


# -- PULSE --------------------------------------------------------------------
#
# Only used in production.
#

PULSE_TREESTATUS_ENABLE = False

if not DEBUG:
    # XXX: PULSE_TREESTATUS_ENABLE = True
    PULSE_TREESTATUS_ENABLE = False
    PULSE_TREESTATUS_EXCHANGE = secrets['PULSE_TREESTATUS_EXCHANGE']
    PULSE_USE_SSL = bool(secrets['PULSE_USE_SSL'])
    PULSE_CONNECTION_TIMEOUT = int(secrets['PULSE_CONNECTION_TIMEOUT'])
    PULSE_HOST = secrets['PULSE_HOST']
    PULSE_PORT = int(secrets['PULSE_PORT'])
    PULSE_USER = secrets['PULSE_USER']
    PULSE_PASSWORD = secrets['PULSE_PASSWORD']
    PULSE_VIRTUAL_HOST = secrets['PULSE_VIRTUAL_HOST']


# -- STATUSPAGE  --------------------------------------------------------------

STATUSPAGE_ENABLE = True
# below setting should be set per channel (in secrets)
# STATUSPAGE_TOKEN <- authentication token
# STATUSPAGE_PAGE_ID <- id of the page which we are interacting with
# STATUSPAGE_COMPONENTS = <- a tree_name=>component_id mapping
# STATUSPAGE_NOTIFY_ON_ERROR <- email to where to send when error happens
# STATUSPAGE_TAGS <- list of tags which will trigger creation of status page incident
