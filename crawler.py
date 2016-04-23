import webapp2
import json
import urllib2
import re
import tinify
import requests
from requests.exceptions import HTTPError
import db_models
from google.appengine.ext import ndb
# from google.appengine.ext import blobstore
# from google.appengine.ext.webapp import blobstore_handlers
tinify.key = "RjQma6pVqAjKdolx3M4Htp8Se4m7p9bE"

# imagemagick on the server?
# We can use the image service from the google app engine for data
  # https://cloud.google.com/appengine/docs/python/images/

class Basepage(webapp2.RequestHandler):
  def post(self):
    """
    Initiates a crawl for files
    
    POST variables:
    url - Starting crawl location
    depth - Depth of crawl attempt (distance from starting URL). Activates depth-first crawl.
    breadth - The number of URLs crawled on each page (number of children of each URL)
    image - Number of image links to return for compression. Activates breadth-first crawl.
    keyword - Keyword that, if found, stops the crawl
    """
	self.response.headers.add_header("Access-Control-Allow-Origin", "*")
	
    if 'application/json' not in self.request.accept:
      self.response.state = 406
      self.response.status_message = "Crawler only supports JSON"

    # Get the URL from the request
    urls = []
    urls.append(self.request.get('url', default_value='none'))
    depth = self.request.get('depth', default_value=0)
    breadth = self.request.get('breadth', default_value=0)
    image_option = self.request.get('image', default_value=0)
    keyword = self.request.get('keyword', default_value='')


    if not urls:
      self.response.out.write("Provide a url to start crawl.")
      return


    if depth != 0:
      depth_crawler = DepthCrawler(urls, 0, depth, breadth, [], keyword)
      depth_crawler.depth_crawl()

      # The depth crawl returns a JSON object:
      #      <---       Depth                           --->
      #                 (children, grand-children ...)
      # {
      #   url: 'http://...'                                   ^
      #   children: [                                         |
      #     {                                                 |
      #       url: 'http://...'                   
      #       children: [
      #         {                                          Breadth
      #           url: 'http://...'               (siblings at each depth)
      #           children: []
      #         }, {                                          |
      #           url: 'http://...'                           |
      #           found: 'yes'                                v
      #         }
      #       ]
      #     }
      #   ]
      # }



    # The image crawl
    if image_option != 0:
      pass


    self.response.write(json.dumps(depth_crawler.response[0], sort_keys=True, 
      indent=4, separators=(',', ': ')))
    self.response.write('\n')

class DepthCrawler:
  def __init__(self, urls, depth, max_depth, breadth, visited, keyword):
    self.urls = urls
    self.depth = depth
    self.max_depth = int(max_depth)
    self.max_breadth = int(breadth)
    self.visited = visited
    self.keyword = keyword
    self.response = []

  # For all URLs stored in this DepthCrawler, visit each of them.
  # If there are crawlable URLs in the HTML response, create a new crawler and crawl
  # those URLs.
  def depth_crawl(self):

    # For all of the crawlable URLs stored in this object
    for url in self.urls:

      # Refer to the JSON response explanation in the BasePage handler 
      self.response.append({'url': url, 'children': []})

      # Mark this URL as visited
      self.visited.append(url)

      print "Visited: "
      print self.visited

      # Track the sibling number we're adding a sub-object to
      count = 0

      # Stop crawling at the max depth set by the user with the "depth" POST 
      # variable
      if self.depth < self.max_depth:

        children_urls = []
        try:
          
          print "\nOpening HTTP: " + url
          print "------------------------"

          HTMLresponse = urllib2.urlopen(url)
          html = HTMLresponse.read()

          # Parse HTML
          parser = Parser(html, self.keyword)

          # This is a list of all links in the html response
          parsed_urls = parser.parse()
          
          # Filter the links for crawlable URLs
          children_urls = self.filter_urls(parsed_urls)

          # Copies the attributes values (avoids copying references during recursion)
          depth = self.depth + 1
          visited = self.visited[:]

          child_crawler = DepthCrawler(children_urls, depth, self.max_depth, self.max_breadth, visited, self.keyword)
          child_crawler.depth_crawl()

          self.response[count]['children'] = (child_crawler.response)
          json.dumps(self.response[0], sort_keys=True, indent=4, separators=(',', ': '))
          
        except urllib2.HTTPError, e:
          print "\n ------ HTTPError ------\n"
          return

        # Go to next sibling
        count += 1

      else:
        return

  # Filter URLs, return only links that use HTTP or HTTPS
  # This is where the number of siblings to be crawled is controlled 
    # (the breadth of the crawl)
    # This number is set by the user with the "breadth" POST variable
  def filter_urls(self, urls):
    result = []
    unfiltered_links = urls['links']

    count = 0

    for url in unfiltered_links:
      if ( url[:7] == 'http://' ) or ( url[:8] == 'https://' ):
        pass
      else:
        print "=== Filtered (as invalid): " + url
        continue

      # Prioritize domains that haven't been visited yet
      if self.domain_filter(url):
        pass
      else:
        print "=== Filtered (as prev visit): " + url
        continue

      if count < self.max_breadth:
        result.append(url)
        count += 1
      else:
        return result

    return result

  # Returns True if URL domain has not been visited before
  def domain_filter(self, url):
    pattern = r'://(.*)/'
    n = re.search(pattern, url)
    if n:
      url_domain = n.group(0)

    for visited_url in self.visited:
      visited_domain = ''
      url_domain = ''

      if visited_url == url:
        return False

      if not visited_url.endswith('/'):
        visited_url += '/'

      if not url.endswith('/'):
        url += '/'
    
      m = re.search(pattern, visited_url)
      if m:
        visited_domain = m.group(0)

      if visited_domain == url_domain:
        return False
    
    return True

class Parser:
  def __init__(self, html, keyword):
    self.html = html
    self.keyword = keyword

  def parse(self):
    # This function returns a json object with the following format:
    # 
      # {
      #   "links":["http://web.com", "http://web2.com"]
      #   "images":["http://imgurl.com", "http://imgurl2.com"]
      # }
    #

    ## Search through the HTML string and pull out the links
    response = {}
    response['links'] = []
    # response['images'] = []

    for word in self.html.split():

      hreftype = 'links'
      # srctype = 'images'

      self.urlParser(word, "href", hreftype, response)
      # self.urlParser(word, "src", srctype, response)

    return response

  def urlParser(self, word, htmltag, urltype, responseObj):
    pattern = r'"(.*)"'
    if word.startswith(htmltag):
      m = re.search(pattern, word)
      if m:
        newurl = m.group()[1:-1]
        responseObj[urltype].append(newurl)

class Compressor:
  def __init__(self, url):
    self.url = url

  # This function returns the actual PNG or JPEG image
  def compress(self):
    img_store = db_models.Image()
    img_key = img_store.put()
    source = tinify.from_url()
    source.to_blob(img_key)
    comp_img_store = img_key.get()
    return comp_img_store.img





