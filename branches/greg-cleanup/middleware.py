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

"""Middleware classes for Django."""

import logging

from google.appengine.api import users

import models


class AddUserToRequestMiddleware(object):
  # pylint: disable-msg=R0903
  """Adds a dictionary containing user data to each request.

  Creates dict request.context with the fields: user, profile, user_is_admin,
  sign_out_url, and sign_in_url.
  """

  def process_request(self, request):
    # pylint: disable-msg=R0201
    """This method is executed by Django before the view function is called.

    Args:
      request: the Django http request object
    """
    user = users.GetCurrentUser()
    profile = models.UserProfile.load(user.email()) if user else None

    # Make a new administrator also a superuser
    if users.is_current_user_admin() and not profile:
      logging.info('Creating new superuser profile for %s' % profile.email)
      profile = models.UserProfile(email=user.email(), is_superuser=True)
      profile.put()

    context = {'user': user; 'profile': profile}
    context['user_is_admin'] = users.is_current_user_admin()
    context['sign_out_url'] = users.CreateLogoutURL('/')
    context['sign_in_url'] = users.CreateLoginURL(request.path)

    # request.user = user
    # request.profile = None

    request.context = context
