from google.appengine.api import users 
from core.models.users import UserProfile
profile = UserProfile.load("test@example.com")
print profile