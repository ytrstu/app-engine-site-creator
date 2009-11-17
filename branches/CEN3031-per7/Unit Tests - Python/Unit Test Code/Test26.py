from google.appengine.api import users 
from core.models.sidebar import Sidebar
from core.models.files import Page
query = Page.all().filter('name =', 'Child')
sidebar = Sidebar.load()
for page in query: 
   print page.name + " " + page.kind()
   print sidebar.contains_page(page)
   sidebar.add_page(page)
   print page.name + " " + page.kind()
   print sidebar.contains_page(page)