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

"""Administrative core.views for page editing and user management."""

import csv
import functools
import logging
import StringIO

import configuration
from django import http
from django.http import HttpResponse, Http404
from django.core import urlresolvers
from google.appengine.api import memcache
from google.appengine.ext import db
from core import forms, utility
from core.views.main import get_root
from core.models.sidebar import Sidebar
from core.models.files import Page, File, FileStore, AccessControlList
from core.models.users import UserGroup, UserProfile, Theme


import yaml

PRE='admin'

def admin_required(func):
    """Ensure that the logged in user is an administrator."""

    @functools.wraps(func)
    def __wrapper(request, *args, **kwds):
        """Makes it possible for admin_required to be used as a decorator."""
        if request.user_is_admin:
            return func(request, *args, **kwds)  # pylint: disable-msg=W0142
        else:
            return HttpResponse(status=403)

    return __wrapper


def super_user_required(func):
    """Ensure that the logged in user has editing privileges."""

    @functools.wraps(func)
    def __wrapper(request, *args, **kwds):
        """Makes it possible for super_user_required to be used as a decorator."""
        if request.profile.is_superuser:
            return func(request, *args, **kwds)  # pylint: disable-msg=W0142
        else:
            return HttpResponse(status=403)

    return __wrapper


@super_user_required
def index(request):
    global PRE
    if Theme.get_theme():
        if Theme.get_theme().name == 'frames':
            PRE='themes/frames/admin'
    return utility.respond(request, PRE+'/index')
    """Show the root administrative page."""


@super_user_required
def recently_modified(request):
    """Show the 10 most recently modified pages."""
    global PRE
    pages = Page.all().order('modified').fetch(10)
    if Theme.get_theme():
        if Theme.get_theme().name == 'frames':
            PRE='themes/frames/admin'
    return utility.respond(request, PRE+'/recently_modified', {'pages': pages})


@super_user_required
def get_help(request):
    """Return a help page for the site maintainer."""
    global PRE
    if Theme.get_theme():
        if Theme.get_theme().name == 'frames':
            PRE='themes/frames/admin'
    return utility.respond(request, PRE+'/help')


def edit_acl(request):
    """Edits the contents of an ACL."""
    global PRE

    def grant_access(acl, list_to_edit):
        """Grants access to a page based on data in the POST.

        Args:
          acl: AccessControlList to be manipulated
          list_to_edit: string representing the list on the ACL to add users or
                        groups to

        """
        if request.POST[list_to_edit]:
            datastore_object = None
            if request.POST[list_to_edit].startswith('user'):
                datastore_object = UserProfile.load(request.POST[list_to_edit])
            else:
                datastore_object = UserGroup.get_by_id(
                    int(request.POST[list_to_edit]))
            if datastore_object.key() not in acl.__getattribute__(list_to_edit):
                acl.__getattribute__(list_to_edit).append(datastore_object.key())

    def remove_access(acl, list_to_edit):
        """Removes access to a page based on data in the POST.

        Args:
          acl: AccessControlList to be manipulated
          list_to_edit: string representing the list on the ACL to remove users or
                        groups from

        """
        post_key = '%s_remove_' % list_to_edit
        removal_keys = [k for k in request.POST.keys() if k.startswith(post_key)]
        for key in removal_keys:
            model_type = UserGroup
            if list_to_edit.startswith('user'):
                model_type = UserProfile
            key_id = int(key.replace(post_key, ''))
            datastore_object = model_type.get_by_id(key_id)
            acl.__getattribute__(list_to_edit).remove(datastore_object.key())

    page_id = request.POST['page_id']
    page = Page.get_by_id(int(page_id))

    if not page:
        raise Http404
    if not page.user_can_write(request.profile):
        return HttpResponse(status=403)

    acl = page.acl

    if page.inherits_acl():
        acl = acl.clone()
        acl.put()
        page.acl = acl
        page.put()

    acl.global_write = 'global_write' in request.POST
    acl.global_read = 'global_read' in request.POST

    for object_list in ['group_write', 'group_read', 'user_write', 'user_read']:
        grant_access(acl, object_list)
        remove_access(acl, object_list)

    acl.put()

    return utility.edit_updated_page(page_id, tab_name='security',
                                   message_id='msgChangesSaved')

def choose_theme(request):

    global PRE
    import logging, settings, os
    tdir = settings.TEMPLATE_DIRS[0] + "/themes/"
    themes = []
    for file in os.listdir(tdir):
        if os.path.isdir(tdir+file) and not file.startswith("."):
            themes.append(file)
    if Theme.get_theme():
        sel = Theme.get_theme().name
    else:
        sel = configuration.SYSTEM_THEME_NAME

    if request.method == 'POST':
        sel = request.POST['menu']
        if Theme.get_theme():
            theme = Theme.get_theme()
            theme.name = sel
        else:
            theme = Theme(name=sel)
        theme.put()
        if sel == 'frames':
            PRE='themes/frames/admin'
            to_page='/admin/edit/choosetheme'
            return utility.respond(request,'themes/frames/base',{'to_page':to_page})
        else:
            PRE='admin'

    return utility.respond(request,PRE+'/choose_theme',{'selected' : sel,
            'themes': themes})
       

	




def edit_page(request, page_id=None, parent_id=None):
    """Generates and processes the form to create or edit a specified page.

    Args:
      request: The request object
      page_id: ID of the page.
      parent_id: ID of the parent page

    Returns:
      A Django HttpResponse object.

    """
    page = None
    files = None

    global PRE
    if Theme.get_theme():
        if Theme.get_theme().name == 'frames':
            PRE='themes/frames/admin'
    if page_id:
        page = Page.get_by_id(int(page_id))
        logging.debug('%s', page)
        if not page:
            raise Http404
        elif not page.acl:
            if parent_id:
                parent = Page.get_by_id(int(parent_id))
                page.acl = parent.__get_acl()
            else:
                acl = AccessControlList(global_read=True)
                acl.put()
                page.acl = acl
        if not page.user_can_write(request.profile):
            return HttpResponse(status=403)
        files = list(
            FileStore.all().filter('parent_page =', page).order('name'))
        for item in files:
            item.icon = '/static/images/fileicons/%s.png' % item.name.split('.')[-1]

    acl_data = {}

    if page:
        all_group_keys = [
            g.key() for g in UserGroup.all().order('name')]
        groups_without_write_keys = [
            k for k in all_group_keys if k not in page.acl.group_write]
        groups_without_read_keys = [
            k for k in all_group_keys if k not in page.acl.group_read]
        acl_data = {
            'groups_without_write': UserGroup.get(groups_without_write_keys),
            'groups_without_read': UserGroup.get(groups_without_read_keys),
            'group_write': UserGroup.get(page.acl.group_write),
            'group_read': UserGroup.get(page.acl.group_read),
            'user_write': UserProfile.get(page.acl.user_write),
            'user_read': UserProfile.get(page.acl.user_read),
            'inherits_acl': page.inherits_acl(),
        }

    if not request.POST:
        form = forms.PageEditForm(data=None, instance=page)
        return utility.respond(request, PRE+'/edit_page',
                               {'form': form, 'page': page, 'files': files,
                                'acl_data': acl_data})

    form = forms.PageEditForm(data=request.POST, instance=page)

    same_name = None
    same_name = Page.all().filter('name = ', form.data['name']).filter('parent_page = ',page.parent_page).filter('created != ',page.created)
    if same_name:
        form.errors['name'] = 'The name \'%s\' already exists.' % (form.data['name'])

    if not form.errors:
        try:
            page = form.save(commit=False)
        except ValueError, err:
            form.errors['__all__'] = unicode(err)
    if form.errors:
        return utility.respond(request, PRE+'/edit_page',
                               {'form': form, 'page': page, 'files': files})

    page.content = request.POST['editorHtml']
    if parent_id and not page.parent_page:
        page.parent_page = Page.get_by_id(int(parent_id))
    
    new_page = Page(name=page.name,
                    created=page.created,
                    modified=page.modified,
                    parent_page=page.parent_page,
                    acl_ref=page.acl_ref,
                    title=page.title,
                    content=page.content,
                    version=page.version)
    
    new_page.version = new_page.version + 1
    new_page.put()
    
    children = page.page_children
    for child in children:
        child.parent_page = new_page
        child.put()
    attachments = page.attached_files()
    for attachment in attachments:
        attachment.parent_page = new_page
        attachment.put()

    return utility.edit_updated_page(new_page.key().id(),
                                     message_id='msgChangesSaved')


def new_page(request, parent_id):
    """Create a new page.

    Args:
      request: The request object
      parent_id: Page that will be the parent of the new page

    Returns:
      A Django HttpResponse object.

    """
    if parent_id:
        parent_page = Page.get_by_id(int(parent_id))
    else:
        parent_page = Page.get_root()
        if parent_page:
            # there is a root, lets force everything to be a child of
            # the root and set the parent_id
            parent_id = parent_page.key().id()
        else:
            # TODO(gpennington): Figure out a more intuitive method for 
            # site initialization
            parent_page = utility.set_up_data_store()
            return utility.edit_updated_page(parent_page.key().id())

    if not parent_page.user_can_write(request.profile):
        return HttpResponse(status=403)
    newpage = Page(name = 'New Page')
    if parent_page:
        newpage.parent_page = parent_page
    newpage.put()

    return edit_page(request, page_id=newpage.key().id(), parent_id=parent_id)


def upload_file(request):
    """Reads a file from POST data and stores it in the db.

    Args:
      request: The request object

    Returns:
      A http redirect to the edit form for the parent page

    """
    global PRE
    if not request.POST or not 'page_id' in request.POST:
        raise Http404
    if Theme.get_theme():
        if Theme.get_theme().name == 'frames':
            PRE='themes/frames/admin'

    page_id = request.POST['page_id']
    page = Page.get_by_id(int(page_id))

    if not page:
        logging.warning(PRE+'.upload_file was passed an invalid page id %r',
                        page_id)
        raise Http404

    if not page.user_can_write(request.profile):
        return HttpResponse(status=403)

    file_data = None
    file_name = None
    url = None
    if request.FILES and 'attachment' in request.FILES:
        file_name = request.FILES['attachment'].name
        file_data = request.FILES['attachment'].read()
    elif 'url' in request.POST:
        url = request.POST['url']
        file_name = url.split('/')[-1]
    else:
        raise Http404

    if not url and not file_name:
        url = 'invalid URL'

    #if url == 'invalid URL'
    #  except forms.ValidationError, excption:
    #    return Response.set_status(request, excption.messages[0])

    file_record = page.get_attachment(file_name)

    if not file_record:
        file_record = FileStore(name=file_name, parent_page=page)

    if file_data:
        file_record.data = db.Blob(file_data)
    elif url:
        file_record.url = db.Link(url)

    # Determine whether to list the file when the page is viewed
    file_record.is_hidden = 'hidden' in request.POST

    file_record.put()
    utility.clear_memcache()

    return utility.edit_updated_page(page_id, tab_name='files')


def delete_file(request, page_id, file_id):
    """Removes a specified file from the database.

    Args:
      request: The request object
      page_id: ID of the page the file is attached to.
      file_id: Id of the file.

    Returns:
      A Django HttpResponse object.

    """
    record = FileStore.get_by_id(int(file_id))
    if record:
        if not record.user_can_write(request.profile):
            return HttpResponse(status=403)

        record.delete()
        return utility.edit_updated_page(page_id, tab_name='files')
    else:
        raise Http404


def delete_page(request, page_id):
    """Removes a page from the database.

    The page with name page_name is completely removed from the db, and all files
    attached to that page are removed.

    Args:
      request: The request object
      page_id: Key id of the page to delete

    Returns:
      A http redirect to the admin index page.

    """
    page = Page.get_by_id(int(page_id))

    if not page:
        raise Http404

    if not page.user_can_write(request.profile):
        return HttpResponse(status=403)

    page.delete()

    url = urlresolvers.reverse('core.views.admin.index')
    return http.HttpResponseRedirect(url)


@super_user_required
def download_page_html(request, page_id):
    """Gives users access to the current html content of a page.

    Args:
      request: The request object
      page_id: ID of the page being edited

    Returns:
      A Django HttpResponse object containing the page's html content.

    """
    page = Page.get_by_id(int(page_id))
    if not page:
        raise Http404
    response = http.HttpResponse(content=page.content, mimetype='text/html')
    response['Content-Disposition'] = 'attachment; filename=%s.html' % page.name
    return response


@super_user_required
def filter_users(request):
    """Lists all the UserGroups in the DB to filter the user list.

    Args:
      request: The request object

    Returns:
      A Django HttpResponse object.

    """
    global PRE
    groups = UserGroup.all().order('name')
    if Theme.get_theme():
        if Theme.get_theme().name == 'frames':
            PRE='themes/frames/admin'
    return utility.respond(request, PRE+'/filter_users', {'groups': groups})


@super_user_required
def list_groups(request):
    """Lists all the UserGroups in the DB for editing.

    Args:
      request: The request object

    Returns:
      A Django HttpResponse object.

    """
    global PRE
    groups = UserGroup.all().order('name')
    if Theme.get_theme():
        if Theme.get_theme().name == 'frames':
            PRE='themes/frames/admin'
    return utility.respond(request, PRE+'/list_groups', {'groups': groups})


@super_user_required
def view_group(request, group_id):
    """Lists all the UserProfiles in a group.

    Args:
      request: The request object
      group_id: Id of the group to display

    Returns:
      A Django HttpResponse object.

    """
    global PRE
    users = UserProfile.all().order('email')
    if group_id:
        group = UserGroup.get_by_id(int(group_id))
        if group.users:
            users = UserProfile.get(group.users)
        else:
            users = []
    if Theme.get_theme():
        if Theme.get_theme().name == 'frames':
            PRE='themes/frames/admin'
    return utility.respond(request, PRE+'/view_group', {'users': users})


@super_user_required
def add_to_group(_request, group_id, email):
    """Adds a user to a group.

    Args:
      _request: The request object (ignored)
      group_id: id of the group to add the user to
      email: email address of the user to add

    Returns:
      A HttpResponse object.

    """
    group = UserGroup.get_by_id(int(group_id))
    user_key = UserProfile.load(email).key()
    if group.users is None:
        group.users = []
        logging.warning('Group "%s" had a None users list', group.name)
    group.users.append(user_key)
    group.put()

    url = urlresolvers.reverse('core.views.admin.edit_user', args=[email])
    return http.HttpResponseRedirect(url)


@super_user_required
def remove_from_group(_request, group_id, email):
    """Removes a user from a group.

    Args:
      _request: The request object (ignored)
      group_id: id of the group to remove the user from
      email: email address of the user to remove

    Returns:
      A HttpResponse object.

    """
    group = UserGroup.get_by_id(int(group_id))
    user_key = UserProfile.load(email).key()
    if group.users is None:
        group.users = []
        logging.warning('Group "%s" had a None users list' % group.name)
    group.users.remove(user_key)
    group.put()

    url = urlresolvers.reverse('core.views.admin.edit_user', args=[email])
    return http.HttpResponseRedirect(url)


@super_user_required
def new_group(request):
    """Creates a new group.

    Args:
      request: The request object

    Returns:
      A HttpResponse object.

    """
    # this needs to be unique so find a better way to do this
    newgroup = UserGroup(name="New Group")
    newgroup.put()
    return edit_group(request, newgroup.key().id())


@super_user_required
def edit_group(request, group_id):
    """Edits an existing group or creates a new one if no ID is passed.

    Args:
      request: The request object
      group_id: The ID of the group to edit, or None if this is a new group

    Returns:
      A Django HttpResponse object.

    """
    global PRE
    group = None
    if Theme.get_theme():
        if Theme.get_theme().name == 'frames':
            PRE='themes/frames/admin'
    if group_id:
        group = UserGroup.get_by_id(int(group_id))
    return utility.edit_instance(request, UserGroup, forms.GroupEditForm,
                                 PRE+'/edit_group',
                                 urlresolvers.reverse('core.views.admin.list_groups'),
                                 group_id, group=group)


@super_user_required
def delete_group(_request, group_id):
    """Deletes a given group.

    Args:
      _request: The request object (ignored)
      group_id: Id of the group to delete

    Returns:
      A Django HttpResponse object.

    """
    group = UserGroup.get_by_id(int(group_id))
    group.delete()

    url = urlresolvers.reverse('core.views.admin.list_groups')
    
    return http.HttpResponseRedirect(url)

@super_user_required
def edit_user(request, email):
    """Renders and processes a form to edit a UserProfile.

    Args:
      request: The request object
      email: The user's email

    Returns:
      A Django HttpResponse object.

    """
    global PRE
    if not email:
        if request.POST and request.POST['email']:
            url = urlresolvers.reverse('core.views.admin.edit_user',
                                       args=[request.POST['email']])
            return http.HttpResponseRedirect(url)
        else:
            if Theme.get_theme():
                if Theme.get_theme().name == 'frames':
                    PRE='themes/frames/admin'
            return utility.respond(request, PRE+'/edit_user', {'title': 'Edit user'})

    profile = UserProfile.load(email)
    if not profile:
        raise Http404
    title = 'Edit user: ' + email
    if Theme.get_theme():
        if Theme.get_theme().name == 'frames':
            PRE='themes/frames/admin'

    return utility.edit_instance(request, UserProfile, forms.UserEditForm,
                                 PRE+'/edit_user',
                                 urlresolvers.reverse('core.views.admin.index'),
                                 profile.key().id(), title=title, profile=profile)


@super_user_required
def bulk_edit_users(request):
    """Renders and processes a form to edit UserProfiles with a csv format.

    Args:
      request: The request object

    Returns:
      A Django HttpResponse object.

    """
    global PRE
    if Theme.get_theme():
        if Theme.get_theme().name == 'frames':
            PRE='themes/frames/admin'
    if not request.POST:
        return utility.respond(request, PRE+'/bulk_edit_users',
                               {'title': 'Bulk user upload form'})

    data = request.POST['users_text']
    if data and data[-1] != '\n':
        data += '\n'

    if request.FILES and 'users_file' in request.FILES:
        data += request.FILES['users_file']['content']

    if 'complete' in request.POST:
        for profile in UserProfile.all():
            db.delete(profile)

    csv_buffer = StringIO.StringIO(data)
    for email, is_superuser in csv.reader(csv_buffer, skipinitialspace=True):
        if not UserProfile.update(email, is_superuser == '1'):
            logging.warning('Could not update user %r' % email)

    url = urlresolvers.reverse('core.views.admin.index')
    return http.HttpResponseRedirect(url)


@super_user_required
def export_users(_request):
    """Export a csv file listing all UserProfiles in the database.

    Args:
      _request: The request object (ignored)

    Returns:
      The csv file in a HttpResponse object.

    """
    query = UserProfile.all().order('email')
    rows = []
    for user in query:
        is_superuser = 0
        if user.is_superuser:
            is_superuser = 1
        rows.append('%s,%s\n' % (user.email, is_superuser))

    response = http.HttpResponse(''.join(rows), mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=users.csv'
    return response


@super_user_required
def add_to_sidebar(request, page_id):
    """Adds a page to the bottom of the sidebar.

    Args:
      request: The request object (ignored)
      page_id: Id of the page to add to the sidebar

    Returns:
      A Django HttpResponse object.

    """
    if request.POST and 'page_id' in request.POST:
        page = Page.get_by_id(int(request.POST['page_id']))
    else:
        page = Page.get_by_id(int(page_id))
        
    Sidebar.add_page(page)
    return http.HttpResponseRedirect(
        urlresolvers.reverse('core.views.admin.edit_sidebar'))


@super_user_required
def edit_sidebar(request):
    """Renders and processes a form to edit the YAML definition of the
    sidebar.

    Args:
      request: The request object

    Returns:
      A Django HttpResponse object.

    """
    global PRE
    sidebar = Sidebar.load()

    if request.POST and 'heading' in request.POST:
        newHeading = request.POST['heading']
        yaml_data = "heading: '%s'\n" % newHeading
        yaml_data = yaml_data + "pages:\n"

        for pageId in request.POST.getlist('ids'):
            yaml_data = yaml_data + "- {id: %s, title:" % pageId
            yaml_data = yaml_data + " %s }\n" % request.POST['page' + pageId]

        if not sidebar:
            sidebar = Sidebar(yaml=yaml_data)
        else:
            sidebar.yaml = yaml_data            

        error_message = None
        try:
            sidebar.put()
        except yaml.YAMLError:
            error_message = 'Invalid YAML'
        except KeyError, error:
            error_message = 'Invalid YAML, missing key %s' % error

        if error_message:
            if Theme.get_theme():
                if Theme.get_theme().name == 'frames':
                    PRE='themes/frames/admin'
            return utility.respond(request, PRE+'/edit_sidebar',
                                   {'yaml': yaml_data,
                                    'error_message': error_message})

        return http.HttpResponseRedirect(urlresolvers.reverse('core.views.admin.index'))

    else:
        heading = ''
        page = []
        pageOptions = []
        
        if sidebar:
            sections = list(yaml.load_all(sidebar.yaml))
            heading = sections[0]['heading']
            pages = sections[0]['pages']
            pageOptions = Page.all()
        if Theme.get_theme():
            if Theme.get_theme().name == 'frames':
                PRE='themes/frames/admin'
            
        return utility.respond(request, PRE+'/edit_sidebar', {'pages': pages,
                                                              'pageOptions': pageOptions,
                                                              'heading': heading})


@admin_required
def flush_memcache_info(_request):
    """Flushes the memcache.

    Args:
      _request: The request object (ignored)

    Returns:
      A Django HttpResponse object.

    """
    utility.clear_memcache()
    return http.HttpResponseRedirect(
        urlresolvers.reverse('core.views.admin.display_memcache_info'))


@admin_required
def display_memcache_info(request):
    """Displays all of the information about the applications memcache.

    Args:
      request: The request object

    Returns:
      A Django HttpResponse object.

    """
    global PRE
    if Theme.get_theme():
        if Theme.get_theme().name == 'frames':
            PRE='themes/frames/admin'
    # pylint: disable-msg=E1101
    return utility.respond(request, PRE+'/memcache_info',
                           {'memcache_info': memcache.get_stats()})
