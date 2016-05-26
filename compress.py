import webapp2
import json
import urllib2
import re
import tinify
import requests
from requests.exceptions import HTTPError
import db_models
from google.appengine.ext import ndb

tinify.key = "RjQma6pVqAjKdolx3M4Htp8Se4m7p9bE"


class CompressHandler(webapp2.RequestHandler):
  def post(self):
    """
    Initiates image compression
    
    POST variables:
    url - Image compression location
    """
    if 'application/json' not in self.request.accept:
      self.response.state = 406
      self.response.status_message = "Compressor only supports JSON"

    # urls = []

    url = self.request.get('url')

    # for url in self.request.arguments():
    #   urls.append(self.request.get(url))

    # This only compresses the first image provided for now as we decide
    # how the client downloads will be handled. Perhaps we can just zip them
    # in one package and return that to the user?
    compressor = Compressor(url)

    compressed_img = compressor.compress()

    self.response.headers["Content-Type"] = "image/png"
    self.response.out.write(compressed_img)

class Compressor:
  def __init__(self, url):
    self.url = url

  # This function returns the actual PNG or JPEG image
  def compress(self):
    img_store = db_models.Image()
    img_key = img_store.put()
    source = tinify.from_url(self.url)
    source.to_blob(img_key)
    comp_img_store = img_key.get()
    return comp_img_store.img
