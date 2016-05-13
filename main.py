import webapp2
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
sys.path.insert(0, 'libs')

app = webapp2.WSGIApplication([], debug=True)
app.router.add(webapp2.Route(r'/crawler', 'crawler.Basepage'))
app.router.add(webapp2.Route(r'/compress', 'compress.CompressHandler'))
