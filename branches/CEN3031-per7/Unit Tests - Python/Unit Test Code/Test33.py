from google.appengine.api import users 
from core.models.files import File
testfile = File(name="test.txt")
print testfile.name + " " + testfile.kind()