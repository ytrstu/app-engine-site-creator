from google.appengine.api import users 
from core.models.files import Page
query = Page.all().filter('name =','Home') 
for page in query: 
    query2 = page.filestore_children
    for page2 in query2:
        print page2.name