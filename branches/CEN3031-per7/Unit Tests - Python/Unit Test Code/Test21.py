from google.appengine.api import users 
from core.models.users import UserGroup
for group in UserGroup.all_groups():
    group.delete()
TestGroup = UserGroup(name="test")
TestGroup.put()
TestGroup = UserGroup(name="test1")
TestGroup.put()
TestGroup = UserGroup(name="test2")
TestGroup.put()
for group in UserGroup.all_groups():
    print group.name