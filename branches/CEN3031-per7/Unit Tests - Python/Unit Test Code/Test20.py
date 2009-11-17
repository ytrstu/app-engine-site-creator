from google.appengine.api import users 
from core.models.users import UserGroup
TestGroup = UserGroup(name="test")
TestGroup.put()
for group in UserGroup.all_groups():
    print group.name
    group.delete()
for group in UserGroup.all_groups():
    print group.name
