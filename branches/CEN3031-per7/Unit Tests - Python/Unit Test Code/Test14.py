from google.appengine.api import users 
from core.models.users import UserProfile
from core.models.users import UserGroup
user = UserProfile.load(email = 'test@example.com')
key = user.key()
group = UserGroup(name = 'group1')
group.users.append(key)
group.put()
list = user.groups
for query in list:
    print query.name