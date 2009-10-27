from google.appengine.api import users 
from core.models.files import Page
query = Page.all()
for page in query: 
    print page.name + " " + page.kind()