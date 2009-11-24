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

"""File/Page/Access related models."""

from django.core import urlresolvers
from google.appengine.ext import db

from core import utility
from core.models.sidebar import Sidebar
import yaml


class AccessControlList(db.Model):
    # pylint: disable-msg=R0904
    """Model defining access to objects in the system."""
    group_write = db.ListProperty(db.Key)
    user_write = db.ListProperty(db.Key)
    global_write = db.BooleanProperty()
    group_read = db.ListProperty(db.Key)
    user_read = db.ListProperty(db.Key)
    global_read = db.BooleanProperty()
 
    @classmethod 
    def kind(cls):
        return "AccessControlList"

    def clone(self):
        """Returns a duplicate copy of the ACL.

        Returns:
          A cloned version of the ACL to be used when a child page wants to change
          its security.

        """
        new_acl = AccessControlList(group_write=self.group_write,
                                    user_write=self.user_write,
                                    global_write=self.global_write,
                                    group_read=self.group_read,
                                    user_read=self.user_read,
                                    global_read=self.global_read)
        return new_acl

    def put(self):
        """Saves the ACL and flushes the memcache."""
        super(AccessControlList, self).put()
        utility.clear_memcache()

    def __has_access(self, user, access_type):
        """Determines if user has the specified access type.

        Args:
          user: UserProfile to check
          access_type: Type of access to check, either 'read' or 'write'

        Returns:
          True if the user has the requested access, False otherwise

        """
        if user is not None:
            key = 'acl-has-%s:%s-%s' % (access_type, self.key().id(), user.key().id())
        else:
            key = 'acl-has-%s:%s' % (access_type, self.key().id())
        has_access = utility.memcache_get(key)

        if has_access is not None:
            return has_access

        global_access = self.__getattribute__('global_%s' % access_type)
        user_list = self.__getattribute__('user_%s' % access_type)
        group_list = self.__getattribute__('group_%s' % access_type)

        if global_access:
            has_access = True

        if user is not None:
            if user.is_superuser or user.key() in user_list:
                has_access = True
            else:
                for group in UserGroup.get(group_list):
                    if user.key() in group.users:
                        has_access = True
                        break

        if has_access is None:
            has_access = False

        utility.memcache_set(key, has_access)
        return has_access

    def user_can_write(self, user):
        """Determines if user has write access.

        Args:
          user: UserProfile to check

        Returns:
          True if the user has write access, False otherwise

        """
        return self.__has_access(user, 'write')

    def user_can_read(self, user):
        """Determines if user has read access.

        Args:
          user: UserProfile to check

        Returns:
          True if the user has read access, False otherwise

        """
        if self.user_can_write(user):
            return True

        return self.__has_access(user, 'read')


class File(db.Model):
    # pylint: disable-msg=R0904
    """Defines common properties and methods for pages and files."""
    name = db.StringProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    modified = db.DateTimeProperty(auto_now=True)
    parent_page = db.SelfReferenceProperty()
    acl_ref = db.ReferenceProperty(AccessControlList)

    @classmethod
    def kind(cls):
        return "File"

    def put(self):
        """Overridden method to flush the memcache."""
        super(File, self).put()
        if self.acl:
            self.acl.put()
        utility.clear_memcache()

    def delete(self):
        """Overridden method to clean up ACLs and to flush the memcache."""
        if self.acl:
            self.acl.delete()
        super(File, self).delete()
        utility.clear_memcache()

    def __get_acl(self):
        """Returns the ACL for the object by recursion up the path."""
        key = 'acl:%s' % self.key().id()
        acl = utility.memcache_get(key)
        if acl:
            return acl

        if not acl and self.parent_page:
            acl = self.parent_page.acl

        if not acl:
            newacl = AccessControlList(global_read=True)
            newacl.put()
            acl = newacl

        utility.memcache_set(key, acl)
        return acl

    def __set_acl(self, data):
        """Sets the underlying acl.

        Args:
          data: The new ACL to use

        """
        self.acl_ref = data

    acl = property(__get_acl, __set_acl)

    def inherits_acl(self):
        """Determines if the file is inheriting its ACL from its parent.

        Returns:
          True if the file does not have it's own ACL, and therefore is 
          inheriting, otherwise False

        """
        return self.acl is None

    def inherits_acl_from(self):
        """Determines which ancestor file the ACL is inherited from.

        Returns:
          The Page object that has the ACL controlling the security for
          this page

        """
        if self.inherits_acl():
            return self.parent_page.inherits_acl_from()
        else:
            return self

    def user_can_write(self, user):
        """Wrapper method to check if user can write to this file.

        Args:
          user: UserProfile to check

        Returns:
          True if the user has write access otherwise False

        """
        return self.acl.user_can_write(user)

    def user_can_read(self, user):
        """Wrapper method to check if user can read this file.

        Args:
          user: UserProfile to check

        Returns:
          True if the user has read access otherwise False

        """
        return self.acl.user_can_read(user)

    @property
    def path(self):
        """Returns the URL path used to access the page."""
        if self.is_root:
            return ''
        return '%s%s/' % (self.parent_page.path, self.name)

    @property
    def filepath(self):
        """Returns the URL path for a file attachment. Removes trailing slash."""
        return '%s%s' % (self.parent_page.path, self.name)

    @property
    def is_root(self):
        """Returns True for the root page, False for all others."""
        return self.parent_page is None


class Page(File):
    # pylint: disable-msg=R0904
    """Defines a page object which may have HTML content and associated 
    files."""

    title = db.StringProperty()
    content = db.TextProperty()
    version = db.IntegerProperty(default = 1)

    @classmethod
    def kind(cls):
        return "Page"

    def delete(self):
        """Overridden to ensure child objects are cleaned up on delete."""
        for page in self.page_children:
            page.delete()
        for file_store in self.filestore_children:
            file_store.delete()
        super(Page, self).delete()

    def get_child(self, name):
        """Returns the child with the given name."""
        return self.page_children.filter('name =', name).order('-version').get()

    def in_sidebar(self):
        """Determines if the page is referenced in the sidebar."""
        return Sidebar.contains_page(self)

    @staticmethod
    def get_root():
        """Returns the root page."""
        key = 'rootpage'
        root = utility.memcache_get(key)
        if not root:
            root = Page.all().filter('parent_page =', None).order('-version').get()
            #logging.debug('Parent: %s', root)
            utility.memcache_set(key, root)
        if not root:
            root = utility.set_up_data_store()
            utility.memcache_set(key,root)
        return root

    @property
    def page_children(self):
        """Returns a query for all of the child FileStore objects."""
        return Page.all().filter('parent_page = ', self)

    @property
    def filestore_children(self):
        """Returns a query for all of the child FileStore objects."""
        return FileStore.all().filter('parent_page = ', self)

    @property
    def breadcrumbs(self):
        """Returns the HTML representation of the breadcrumbs for the
        page."""
        key = 'breadcrumbs:%s' % self.key().id()
        breadcrumbs = utility.memcache_get(key)

        if breadcrumbs:
            return breadcrumbs

        breadcrumbs = []
        if self.parent_page:
            breadcrumbs = self.parent_page.breadcrumbs
            breadcrumbs.append({'path': '/' + self.parent_page.path,
                                'name': self.parent_page.name})

        utility.memcache_set(key, breadcrumbs)
        return breadcrumbs

    def get_attachment(self, name):
        """Retrieves a file with the given name that is attached to the 
        page.

        Args:
          name: name of the file to retrieve

        Returns:
          A FileStore object.

        """
        return self.filestore_children.filter('name =', name).get()

    def attached_files(self):
        """Returns all files attached to the current page.

        Returns:
          A query representing the list of all attached files

        """
        key = 'file-list:%s' % self.key().id()
        file_list = utility.memcache_get(key)
        if not file_list:
            # Convert the iterator to a list for caching
            file_list = list(self.filestore_children.order('name'))
            utility.memcache_set(key, file_list)
        return file_list


class FileStoreData(db.Model):
    """A class that holds the data for a FileStore object."""

    data = db.BlobProperty()
    modified = db.DateTimeProperty(auto_now=True)

    @classmethod
    def kind(cls):
        return "FileStoreData"


class FileStore(File):
    # pylint: disable-msg=R0904
    """A class that represents a single file attached to a page.

    This class contains a property data which abstracts the underlying child
    FileStoreData object.  The data property should be treated as though
    it were a BlobProperty.  This prevents the Blob being read into memory
    until it is actually referenced.

    """

    is_hidden = db.BooleanProperty(default=False)
    url_data = db.LinkProperty()
    blob_data = db.ReferenceProperty(FileStoreData)

    @classmethod
    def kind(cls):
        return "FileStore"

    def __get_data(self):
        """Retrieves the data from the child object."""
        return self.blob_data.data

    def __set_data(self, data):
        """Sets the data on the child object, creating one if necessary."""
        if not data:
            if self.blob_data:
                self.blob_data.delete()
                self.blob_data = None
                self.put()
            return

        if not self.blob_data:
            file_store_data = FileStoreData()
            file_store_data.put()
            self.blob_data = file_store_data
            self.put()
        self.blob_data.data = data
        self.blob_data.put()
        self.url = None
        self.put()

    data = property(__get_data, __set_data)

    def __get_url(self):
        """Exposes the url property."""
        return self.url_data

    def __set_deal(self, link):
        """Sets the url property and removes any data associated with the file."""
        if link:
            self.url_data = link
            self.data = None
        else:
            self.url_data = None

    url = property(__get_url, __set_deal)

    def delete(self):
        """Overridden to ensure child objects are cleaned up on delete."""
        if self.blob_data:
            self.blob_data.delete()
        super(FileStore, self).delete()

