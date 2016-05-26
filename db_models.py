from google.appengine.ext import ndb

class Image(ndb.Model):
	img =  ndb.BlobProperty()
	
