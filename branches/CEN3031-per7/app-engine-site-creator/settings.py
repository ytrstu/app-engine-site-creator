#!/usr/bin/python2.5
#
# Copyright 2008 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""Django settings for app-engine-site-creator project."""
# Increase this when you update your media on the production site, so users
# don't have to refresh their cache. By setting this your MEDIA_URL
# automatically becomes /media/MEDIA_VERSION/
MEDIA_VERSION = 1

# By hosting media on a different domain we can get a speedup (more parallel
# browser connections).
#if on_production_server or not have_appserver:
#    MEDIA_URL = 'http://media.mydomain.com/media/%d/'

# Add base media (jquery can be easily added via INSTALLED_APPS)
COMBINE_MEDIA = {
    'combined-%(LANGUAGE_CODE)s.js': (
        # See documentation why site_data can be useful:
        # http://code.google.com/p/app-engine-patch/wiki/MediaGenerator
        '.site_data.js',
    ),
    'combined-%(LANGUAGE_DIR)s.css': (
        'global/look.css',
    ),
}

import os,logging
from core.middleware import middleware, debug_toolbar

APPEND_SLASH = False
# DEBUG = os.environ['SERVER_SOFTWARE'].startswith('Dev')
DATABASE_ENGINE = 'appengine'
DEBUG = True
INTERNAL_IPS = ('localhost',)
MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    #'django.contrib.sessions.middleware.SessionMiddleware',
    #'django.contrib.auth.middleware.AuthenticationMiddleware',        
    'core.middleware.middleware.AddUserToRequestMiddleware',
    'core.middleware.debug_toolbar.middleware.DebugToolbarMiddleware',
    #'ragendja.auth.middleware.GoogleAuthenticationMiddleware',
)
ROOT_PATH = os.path.dirname(__file__)
ROOT_URLCONF = 'urls'
SERVER_NAME = 'localhost'
SERVER_PORT = 8000
TEMPLATE_DEBUG = DEBUG
TEMPLATE_CONTEXT_PROCESSORS = ()
TEMPLATE_DIRS = (
    os.path.join(os.path.dirname(__file__), 'templates'),
)
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
)

INSTALLED_APPS = (
    'appenginepatcher',
    #'django_extensions',
    'core.middleware.debug_toolbar',
)

DEBUG_TOOLBAR_CONFIG = {
        'INTERCEPT_REDIRECTS' : False,
        }
