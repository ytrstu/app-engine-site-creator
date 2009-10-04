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

"""Sidebar related models."""

from django.core import urlresolvers
from google.appengine.ext import db

from core import utility
import yaml

class Sidebar(db.Model):
    # pylint: disable-msg=R0904
    """Model for the left-hand navigation."""

    yaml = db.TextProperty(required=True)
    modified = db.DateTimeProperty(auto_now=True)

    @classmethod
    def kind(cls):
        return "Sidebar"

    def __try_parse(self):
        """Attempts to parse the provided YAML.

        If the YAML is malformed or the expected keys are not present exceptions
        will be thrown.

        """
        for section in yaml.load_all(self.yaml):
            if section['heading']:
                for item in section['pages']:
                    if item['id']:
                        if item['title']:
                            pass

    def put(self):
        """Saves the sidebar and flushes the memcache."""
        self.__try_parse()
        super(Sidebar, self).put()
        utility.clear_memcache()

    @staticmethod
    def load():
        """Retrieves the sidebar from the datastore.

        Returns:
          SideBar object

        """
        return Sidebar.all().get()

    @staticmethod
    def contains_page(page):
        """Determines if the page is referenced in the sidebar.

        Args:
          page: Page to check if it exists in the sidebar

        """
        key = 'page-in-sidebar:%s' % page.key().id()
        in_sidebar = utility.memcache_get(key)
        if in_sidebar is not None:
            return in_sidebar

        sidebar = Sidebar.load()

        if sidebar is not None:
            for section in yaml.load_all(sidebar.yaml):
                for item in section['pages']:
                    if item['id'] == page.key().id():
                        utility.memcache_set(key, True)
                        return True

        utility.memcache_set(key, False)
        return False

    @staticmethod
    def add_page(page):
        """Appends a page to the bottom of the sidebar.

        Args:
          page: Page to append

        """
        sidebar = Sidebar.load()

        if sidebar is None:
            sidebar = Sidebar(yaml="---\nheading: ''\n\n")

        sidebar_documents = list(yaml.load_all(sidebar.yaml))
        if sidebar_documents:
            last_document = sidebar_documents[-1]
            if not last_document.has_key('pages'):
                last_document['pages'] = []
            last_document['pages'].append({'id': page.key().id(),
                                           'title': page.title})

        sidebar.yaml = yaml.safe_dump_all(sidebar_documents)
        sidebar.put()

    @staticmethod
    def render(profile):
        """Retrieves the HTML for the sidebar.

        This method first checks the memcache layer for rendered HTML 
        based on the given profile's access level and returns it if found.
        If the HTML is not found, the sidebar's definition is loaded and 
        each page is checked for existence and if the profile's access 
        level has rights to view the page. HTML is then rendered and 
        stored in memcache for future accesses
        
        Args:
          profile: profile of the user accessing the sidebar

        Returns:
          A string containing the HTML of the sidebar for the given 
          profile's access level

        """
        if profile is not None:
            key = 'sidebar:%s' % profile.key().id()
        else:
            key = 'sidebar'

        html = utility.memcache_get(key)
        if html:
            return html

        html = []
        sidebar = Sidebar.load()
        #sidebar = None
        if not sidebar:
            return None

        for section in yaml.load_all(sidebar.yaml):
            section_html = []

            for item in section['pages']:
                # pylint: disable-msg=E1103
                from core.models.files import Page
                page = Page.get_by_id(int(item['id']))
                if not page or not page.user_can_read(profile):
                    continue
                url = urlresolvers.reverse('core.views.main.get_url', 
                                           args=[page.path])
                section_html.append('<li><a href="%s">%s</a></li>\n' %
                                    (url, item['title']))

            if section_html:
                html.append('<h1>%s</h1>\n' % section['heading'])
                html.append('<ul>\n%s</ul>\n' % ''.join(section_html))

        html = ''.join(html)
        utility.memcache_set(key, html)
        return html

