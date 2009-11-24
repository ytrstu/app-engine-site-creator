from google.appengine.api import users 
from core.models.users import UserProfile
user = UserProfile(email = 'test1@example.com')
user1 = UserProfile.load('test1@example.com') 
print user1
user.put()
user1 = UserProfile.load('test1@example.com') 
print user1