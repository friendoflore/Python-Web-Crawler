import webapp2
import json
import urllib2
import re

class Basepage(webapp2.RequestHandler):
	def post(self):
		"""
		Initiates a crawl for files
		
		POST variables:
		url - Starting crawl location
		"""

		if 'application/json' not in self.request.accept:
			self.response.state = 406
			self.response.status_message = "Crawler only supports JSON"

		# Get the URL from the request
		url = self.request.get('url')

		# Begin the crawl.
		# TODO: We will have to control the crawl using some judgments about 
		# the URLs our crawler found on this page.
			#
		# An approach to this is to pass in options to the crawler in
		# instantiation or to the crawl function.
			# Breadth versus depth option?
			# Width or depth of the crawl
		crawler = Crawler(url)
		parsed = crawler.crawl()

		self.response.write(url)
		self.response.write(json.dumps(parsed, sort_keys=True, 
			indent=4, separators=(',', ': ')))


class Crawler:
	def __init__(self, baseUrl):
		self.baseUrl = baseUrl

	def crawl(self):
		response = urllib2.urlopen(self.baseUrl)
		html = response.read()

		# Parser object returns:
			# {
			# 	"links":["http://web.com", "http://web2.com"]
			#		"images":["http://imgurl.com", "http://imgurl2.com"]
			# }
		parser = Parser(html)
		response = parser.parse()

		return response

class Parser:
	def __init__(self, html):
		self.html = html

	def parse(self):
		# This function returns a json object with the following format:
		# 
			# {
			# 	"links":["http://web.com", "http://web2.com"]
			#		"images":["http://imgurl.com", "http://imgurl2.com"]
			# }
		#
		## Search through the big html string and pull out the links

		response = {}
		response['links'] = []
		response['images'] = []

		for word in self.html.split():

			hreftype = 'links'
			srctype = 'images'

			self.urlParser(word, "href", hreftype, response)
			self.urlParser(word, "src", srctype, response)

		return response

	def urlParser(self, word, htmltag, urltype, responseObj):
		pattern = r'"(.*)"'
		if word.startswith(htmltag):
			m = re.search(pattern, word)
			if m:
				newurl = m.group()[1:-1]
				responseObj[urltype].append(newurl)




