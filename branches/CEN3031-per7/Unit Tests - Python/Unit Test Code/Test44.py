from google.appengine.api import users 
from core.models.files import FileStore
filestore1 = FileStore(name="test.txt")
filestore2 = FileStore(name="Testing.txt")
filestore1.put()
filestore2.put()
print "Before:"
query = FileStore.all()
for filestore in query:
    print filestore.name
filestore2.delete()
print "After:"
query = FileStore.all()
for filestore in query:
    print filestore.name