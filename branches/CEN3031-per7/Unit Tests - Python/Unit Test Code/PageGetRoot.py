from google.appengine.api import users 
from core.models.files import Page
query = Page.all().filter('name =','Test') 
for page in query: 
    print page.get_root()
