from google.appengine.api import users 
from core.models.files import File
testfile = File(name="test.txt")
testfile1 = File(name="test1.txt")
testfile.put()
testfile1.put()
query = File.all()
print "Before:"
for file in query:
    print file.name
testfile1.delete()
query = File.all()
print "After:"
for file in query:
    print file.name