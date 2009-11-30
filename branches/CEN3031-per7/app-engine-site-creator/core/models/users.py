#!/usr/bin/python2.5
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

"""User/Profile/Group related models."""


from django.core import urlresolvers
from google.appengine.ext import db

from core import utility
import yaml

class UserProfile(db.Model):
    # pylint: disable-msg=R0904
    """A class that represents the access levels of a given user."""

    email = db.EmailProperty(required=True)
    is_superuser = db.BooleanProperty(default=False)

    def __str__(self):
        """Overridden string representation."""
        return self.email

    @classmethod
    def kind(cls):
        return "UserProfile"

    @staticmethod
    def load(email):
        """Retrieves a given user profile, through memcache if possible.

        Args:
          email: email address of the profile to load

        Returns:
          UserProfile object for the given email address

        """
        key = 'email:' + email
        profile = utility.memcache_get(key)
        if not profile:
            profile = UserProfile.all().filter('email =', email).get()
            utility.memcache_set(key, profile)
        return profile

    def put(self):
        """Saves the profile and flushes the memcache."""
        super(UserProfile, self).put()
        utility.clear_memcache()

    @property
    def groups(self):
        """Returns a list of all of the groups the user is in.

        Returns:
          The list of groups the user is in

        """
        key = 'users_groups:%s' % self.key().id()
        groups = utility.memcache_get(key)
        if not groups:
            groups = list(UserGroup.all().filter('users = ', self.key()))
            utility.memcache_set(key, groups)
        return groups

    @property
    def groups_not_in(self):
        """Returns a list of all of the groups the user is not in.

        Returns:
          The list of groups the user is not in

        """
        all_group_keys = [g.key().id() for g in UserGroup.all_groups()]
        self_group_keys = [g.key().id() for g in self.groups]
        not_in_group_keys = [k for k in all_group_keys if k not in self_group_keys]
        return UserGroup.get_by_id(not_in_group_keys)

    def delete(self):
        """Overridden to ensure memcache is cleared."""
        super(UserProfile, self).delete()
        utility.clear_memcache()

    @staticmethod
    def update(email, is_superuser=False):
        """Creates or updates a user's profile.

        Args:
          email: the email address of the user to add or edit
          is_superuser: boolean value denoting if the user should be an editor

        Returns:
          True if the user is created/edited, False if the email address is invalid

        """
        if not is_valid_email(email):
            return False

        user = UserProfile.load(email)
        if user:
            user.is_superuser = is_superuser
        else:
            user = UserProfile(email=email, is_superuser=is_superuser)

        user.put()
        return True


class UserGroup(db.Model):
    # pylint: disable-msg=R0904
    """Model for logically grouping users for access control."""

    name = db.StringProperty(required=True)
    description = db.StringProperty()
    users = db.ListProperty(db.Key)

    @classmethod
    def kind(cls):
        return "UserGroup"

    def __str__(self):
        """Overridden string representation."""
        return self.name

    def put(self):
        """Overridden method to ensure name is kept unique."""
        for group in UserGroup.all().filter('name = ', self.name):
            if not self.is_saved() or group.key() != self.key():
                raise db.BadValueError('There is already a group named "%s"'
                                       % self.name)
        super(UserGroup, self).put()
        utility.clear_memcache()

    def delete(self):
        """Overridden to ensure memcache is cleared."""
        super(UserGroup, self).delete()
        utility.clear_memcache()

    @staticmethod
    def all_groups():
        """Returns a list of all of the groups in the system.

        Returns:
          A list of all groups

        """
        key = 'all_groups:'
        groups = utility.memcache_get(key)
        if not groups:
            groups = list(UserGroup.all())
            utility.memcache_set(key, groups)
        return groups

class Theme(db.Model):
    name = db.StringProperty(required=True)

    @staticmethod
    def get_theme():
        if len(Theme.all()) > 0:
            return Theme.all()[0]
        else:
            return None

