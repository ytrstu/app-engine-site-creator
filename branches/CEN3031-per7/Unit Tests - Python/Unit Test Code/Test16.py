from google.appengine.api import users 
from core.models.users import UserProfile
user = UserProfile.load(email = 'test1@example.com')
list = UserProfile.all()
print "before:"
for query in list:
    print query.email
user.delete()
list = UserProfile.all()
print "after:"
for query in list:
    print query.email