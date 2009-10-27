from google.appengine.api import users 
from core.models.sidebar import Sidebar
query = Sidebar.all()
for sidebar in query: 
    print sidebar.yaml + sidebar.kind()