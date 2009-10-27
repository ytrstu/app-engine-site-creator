from google.appengine.api import users 
from core.models.users import UserProfile
query = UserProfile.all()
for profile in query: 
    print profile.email + " " + profile.kind()