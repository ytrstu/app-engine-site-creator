from google.appengine.api import users 
from core.models.files import Page
query = Page.all().filter('name =','Child') 
for page in query: 
    query2 = page.page_children
    for page2 in query2:
        print page2.name