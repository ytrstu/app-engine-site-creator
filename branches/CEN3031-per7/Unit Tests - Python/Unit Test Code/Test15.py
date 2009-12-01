from google.appengine.api import users 
from core.models.users import UserProfile
from core.models.users import UserGroup
user = UserProfile.load(email = 'test@example.com')
key = user.key()
list = user.groups_not_in
for query in list:
    print query.name