from google.appengine.api import users 
from core.models.files import File
testfile = File(name="test.txt")
query = File.all()
for file in query:
    print "Before: " + file.name
testfile.put()
query = File.all()
for file in query:
    print "After: " + file.name