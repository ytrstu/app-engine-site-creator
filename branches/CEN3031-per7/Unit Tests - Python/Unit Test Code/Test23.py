from google.appengine.api import users 
from core.models.sidebar import Sidebar
sidebar = Sidebar.load()
print sidebar.put()
print sidebar.yaml
print sidebar.modified