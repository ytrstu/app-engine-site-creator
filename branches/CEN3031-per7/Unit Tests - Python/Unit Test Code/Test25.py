from google.appengine.api import users 
from core.models.sidebar import Sidebar
from core.models.files import Page
query = Page.all()
sidebar = Sidebar.load()
for page in query: 
   print page.name + " " + page.kind()
   print sidebar.contains_page(page)
    