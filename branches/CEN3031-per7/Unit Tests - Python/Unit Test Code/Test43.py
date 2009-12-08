from google.appengine.api import users 
from core.models.files import FileStore
testfilestore = FileStore(name="testfile.txt")
print testfilestore.name + " " + testfilestore.kind()