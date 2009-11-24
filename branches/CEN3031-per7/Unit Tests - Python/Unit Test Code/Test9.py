from google.appengine.api import users 
from core.models.files import Page
query = Page.all().filter('name =','Home') 
for page in query: 
        print page.get_attachment("testing.txt")