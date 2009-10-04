# -*- coding: utf-8 -*-
import os, sys

# Add current folder to sys.path, so we can import aecmd.
# App Engine causes main.py to be reloaded if an exception gets raised
# on the first request of a main.py instance, so don't add current_dir multiple
# times.
current_dir = os.path.abspath(os.path.dirname(__file__))
if current_dir not in sys.path:
    sys.path = [current_dir] + sys.path

import aecmd
aecmd.setup_project()

from appenginepatcher.patch import patch_all, setup_logging
patch_all()

import django.core.handlers.wsgi
from google.appengine.ext.webapp import util
from django.conf import settings

def real_main():
    # Reset path and environment variables
    global path_backup
    try:
        sys.path = path_backup[:]
    except:
        path_backup = sys.path[:]
    os.environ.update(aecmd.env_ext)
    setup_logging()

    # Create a Django application for WSGI.
    application = django.core.handlers.wsgi.WSGIHandler()

    # Run the WSGI CGI handler with that application.
    util.run_wsgi_app(application)

def profile_main():
    import logging, cProfile, pstats, random, StringIO
    only_forced_profile = getattr(settings, 'ONLY_FORCED_PROFILE', False)
    profile_percentage = getattr(settings, 'PROFILE_PERCENTAGE', None)
    if (only_forced_profile and
                'profile=forced' not in os.environ.get('QUERY_STRING')) or \
            (not only_forced_profile and profile_percentage and
                float(profile_percentage) / 100.0 <= random.random()):
        return real_main()

    prof = cProfile.Profile()
    prof = prof.runctx('real_main()', globals(), locals())
    stream = StringIO.StringIO()
    stats = pstats.Stats(prof, stream=stream)
    sort_by = getattr(settings, 'SORT_PROFILE_RESULTS_BY', 'time')
    if not isinstance(sort_by, (list, tuple)):
        sort_by = (sort_by,)
    stats.sort_stats(*sort_by)

    restrictions = []
    profile_pattern = getattr(settings, 'PROFILE_PATTERN', None)
    if profile_pattern:
        restrictions.append(profile_pattern)
    max_results = getattr(settings, 'MAX_PROFILE_RESULTS', 80)
    if max_results and max_results != 'all':
        restrictions.append(max_results)
    stats.print_stats(*restrictions)
    extra_output = getattr(settings, 'EXTRA_PROFILE_OUTPUT', None) or ()
    if not isinstance(sort_by, (list, tuple)):
        extra_output = (extra_output,)
    if 'callees' in extra_output:
        stats.print_callees()
    if 'callers' in extra_output:
        stats.print_callers()
    logging.info('Profile data:\n%s', stream.getvalue())

main = getattr(settings, 'ENABLE_PROFILER', False) and profile_main or real_main

if __name__ == '__main__':
    main()


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

"""Main views for viewing pages and downloading files."""

import datetime
import logging
import mimetypes

import configuration
from django import http
from django.core import urlresolvers
from django.utils import simplejson
from core.models.sidebar import Sidebar
from core.models.files import Page
from core import utility


def send_page(page, request):
    """Sends a given page to a user if they have access rights.

    Args:
      page: The page to send to the user
      request: The Django request object

    Returns:
      A Django HttpResponse containing the requested page, or an error message.

    """
    profile = request.profile
    global_access = page.acl.global_read
    if not global_access:
        if profile is None:
            return http.HttpResponseRedirect(users.create_login_url(request.path))
        if not page.user_can_read(profile):
            logging.warning('User %s made an invalid attempt to access page %s' %
                            (profile.email, page.name))
            return utility.forbidden(request)

    files = page.attached_files()
    files = [file_obj for file_obj in files if not file_obj.is_hidden]

    for item in files:
        ext = item.name.split('.')[-1]
        item.icon = '/static/images/fileicons/%s.png' % ext

    is_editor = page.user_can_write(profile)

    if configuration.SYSTEM_THEME_NAME:
        template = 'themes/%s/page.html' % (configuration.SYSTEM_THEME_NAME)

    return utility.respond(request, template, {'page': page, 'files': files,
                                               'is_editor': is_editor})


def send_file(file_record, request):
    """Sends a given file to a user if they have access rights.

    Args:
      file_record: The file to send to the user
      request: The Django request object

    Returns:
      A Django HttpResponse containing the requested file, or an error message.

    """
    profile = request.profile
    mimetype = mimetypes.guess_type(file_record.name)[0]

    if not file_record.user_can_read(profile):
        logging.warning('User %s made an invalid attempt to access file %s' %
                        (profile.email, file_record.name))
        return utility.forbidden(request)

    expires = datetime.datetime.now() + configuration.FILE_CACHE_TIME
    response = http.HttpResponse(content=file_record.data, mimetype=mimetype)
    response['Cache-Control'] = configuration.FILE_CACHE_CONTROL
    response['Expires'] = expires.strftime('%a, %d %b %Y %H:%M:%S GMT')
    return response


def get_url(request, path_str):
    """Parse the URL and return the requested content to the user.

    Args:
      request: The Django request object.
      path_str: The URL path as a string

    Returns:
      A Django HttpResponse containing the requested page or file, or an error
      message.

    """
    def follow_url_forwards(base, path):
        """Follow the path forwards, returning the desired item."""
        if not base:
            return None
        if not path:
            utility.memcache_set('path:%s' % path_str, base)
            return base
        if len(path) == 1:
            attachment = base.get_attachment(path[0])
            if attachment:
                return attachment
        return follow_url_forwards(base.get_child(path[0]), path[1:])

    def follow_url_backwards(pre_path, post_path):
        """Traverse the path backwards to find a cached page or the root."""
        key = 'path:' + '/'.join(pre_path)
        item = utility.memcache_get(key)
        if item:
            return follow_url_forwards(item, post_path)
        if not pre_path:
            return follow_url_forwards(Page.get_root(), post_path)
        return follow_url_backwards(pre_path[:-1], [pre_path[-1]] + post_path)

    path = [dir_name for dir_name in path_str.split('/') if dir_name is not '']
    item = follow_url_backwards(path, [])

    if isinstance(item, Page):
        return send_page(item, request)

    if isinstance(item, FileStore):
        return send_file(item, request)

    return utility.page_not_found(request)


def get_tree_data(request):
    """Returns the structure of the file hierarchy in JSON format.

    Args:
      request: The Django request object

    Returns:
      A Django HttpResponse object containing the file data.

    """

    def get_node_data(page):
        """A recursive function to output individual nodes of the tree."""
        page_id = str(page.key().id())
        data = {'title': page.title,
                'path': page.path,
                'id': page_id,
                'edit_url': urlresolvers.reverse(
                    'views.admin.edit_page', args=[page_id]),
                'child_url': urlresolvers.reverse(
                    'views.admin.new_page', args=[page_id]),
                'delete_url': urlresolvers.reverse(
                    'views.admin.delete_page', args=[page_id])}
        children = []
        for child in page.page_children:
            if child.acl.user_can_read(request.profile):
                children.append(get_node_data(child))
        if children:
            data['children'] = children
        return data

    data = {'identifier': 'id', 'label': 'title',
            'items': [get_node_data(Page.get_root())]}
    return http.HttpResponse(simplejson.dumps(data))


def page_list(request):
    """List all pages."""
    return utility.respond(request, 'sitemap')
