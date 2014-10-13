import os
import urllib
from google.appengine.api import users
from google.appengine.ext import ndb
import jinja2
import webapp2
import healthvaultlib.healthvault
from healthvaultlib.datatypes import DataType
from healthvaultlib.exceptions import HealthVaultException


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

	
APP_ID = "e14a3b91-04b7-4c18-bc7b-9ac724af41f9"
THUMBPRINT = "DDCA0E527B1D5B3EBB0F3EA5FEC600FFC8EA508C"

APP_PUBLIC_KEY = 0xc16757cfbc596b30f0ae650b126def1312cdb3115de5d11f2c76da6e16149c64c39de9f919f3b3e8e7164482a02ade65b2e3536f23ebe2fdc3bb39afe70fd27553cb4a48521d3113e2bc64c8b1b43f34310e8913924f30509a96311e5b6eab3823e1980951dcfa69c5e9865998895a2ec0b09b36c90d9e8708eb5f1300eaf9f80cc36a748de52ffa746c83a0c6814e9361c7d0570daed19449a7aa675d9950fcc61329de92b5f3b9829279b7d349ef3b5543f22ff463bc8617c0b4058c603f4b73f2dd4dc72227915b11650264f41d518522a27bf83a736eaf5efb12a9b4aa04d5e7ea9da18ea5522381d1f760de08e8d3817409a2cdd04a199373a7fbe49f71
APP_PRIVATE_KEY =0xa18fcde828845e2a0cf4f24db4808775dc805f75438647128e975ed315b8f408aced0ed65bda9c51143222db2827878f5747d59c035afb4d57a3e085d435006fa8a72b0f8d20fbad8bfc2b090881f5468930864c062e06c35ecfd68a7080dba15340123cbed9258b149c86f1f39dd1eb3a668dd2cf53843973b703be214729b69b6f8c1e9891f9fc6675e39b97b5be27164107be683dc1615777bb7618f026f608131f5301e73f2128f838a0e8e095cd832d74ecc34162a78b1fc7e5d173d495bd39e47fab11f736f64f4514feecb58836160b0e03487c3bf583e0bc3d131662b8d57d3d232ea99ed0b34b8ac6bacaa509e9209815799ab27a8e4d5e9a7fcebd


hvdata = DataType.BASIC_DEMOGRAPHIC_DATA

DEFAULT_GUESTBOOK_NAME = 'default_guestbook'

def guestbook_key(guestbook_name=DEFAULT_GUESTBOOK_NAME):
    """Constructs a Datastore key for a Guestbook entity with guestbook_name."""
    return ndb.Key('Guestbook', guestbook_name)

class Greeting(ndb.Model):
    """Models an individual Guestbook entry."""
    author = ndb.UserProperty()
    content = ndb.StringProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)

class MainPage(webapp2.RequestHandler):
    def get(self):
        guestbook_name = self.request.get('guestbook_name', DEFAULT_GUESTBOOK_NAME)
        greetings_query = Greeting.query(
            ancestor=guestbook_key(guestbook_name)).order(-Greeting.date)
        greetings = greetings_query.fetch(10)

        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
			#hvdata = 'temp'

        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'		


        template_values = {
            'greetings': greetings,
            'guestbook_name': urllib.quote_plus(guestbook_name),
            'url': url,
            'url_linktext': url_linktext,
			'app_id': APP_ID,
			'hvdata': hvdata,
        }

        template = JINJA_ENVIRONMENT.get_template('index2.html')
        self.response.write(template.render(template_values))

class Guestbook(webapp2.RequestHandler):
    def post(self):
        # We set the same parent key on the 'Greeting' to ensure each Greeting
        # is in the same entity group. Queries across the single entity group
        # will be consistent. However, the write rate to a single entity group
        # should be limited to ~1/second.
        guestbook_name = self.request.get('guestbook_name',
                                          DEFAULT_GUESTBOOK_NAME)
        greeting = Greeting(parent=guestbook_key(guestbook_name))

        if users.get_current_user():
            greeting.author = users.get_current_user()

        greeting.content = self.request.get('content')
        greeting.put()

        query_params = {'guestbook_name': guestbook_name}
        self.redirect('/?' + urllib.urlencode(query_params))

application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/sign', Guestbook),
], debug=True)
