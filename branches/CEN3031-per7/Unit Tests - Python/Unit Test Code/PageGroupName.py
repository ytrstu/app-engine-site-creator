from google.appengine.api import users 
from core.models.users import UserGroup
query = UserGroup.all()
for group in query: 
    print group.name + " " + group.kind()