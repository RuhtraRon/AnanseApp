import BaseHTTPServer
from ssl import wrap_socket
import os
from urlparse import urlparse, parse_qs
import webbrowser
from healthvaultlib.exceptions import HealthVaultException
from healthvaultlib.healthvault import HealthVaultConn
from healthvaultlib.datatypes import DataType

BASE_URL = "https://localhost:8000"
#BASE_URL = "http://fourth-scheme-677.appspot.com"

# FIXME: This is my test app, you might need to set up your own and change these values
APP_ID = "e14a3b91-04b7-4c18-bc7b-9ac724af41f9"
THUMBPRINT = "DDCA0E527B1D5B3EBB0F3EA5FEC600FFC8EA508C"

APP_PUBLIC_KEY = 0xc16757cfbc596b30f0ae650b126def1312cdb3115de5d11f2c76da6e16149c64c39de9f919f3b3e8e7164482a02ade65b2e3536f23ebe2fdc3bb39afe70fd27553cb4a48521d3113e2bc64c8b1b43f34310e8913924f30509a96311e5b6eab3823e1980951dcfa69c5e9865998895a2ec0b09b36c90d9e8708eb5f1300eaf9f80cc36a748de52ffa746c83a0c6814e9361c7d0570daed19449a7aa675d9950fcc61329de92b5f3b9829279b7d349ef3b5543f22ff463bc8617c0b4058c603f4b73f2dd4dc72227915b11650264f41d518522a27bf83a736eaf5efb12a9b4aa04d5e7ea9da18ea5522381d1f760de08e8d3817409a2cdd04a199373a7fbe49f71
APP_PRIVATE_KEY =0xa18fcde828845e2a0cf4f24db4808775dc805f75438647128e975ed315b8f408aced0ed65bda9c51143222db2827878f5747d59c035afb4d57a3e085d435006fa8a72b0f8d20fbad8bfc2b090881f5468930864c062e06c35ecfd68a7080dba15340123cbed9258b149c86f1f39dd1eb3a668dd2cf53843973b703be214729b69b6f8c1e9891f9fc6675e39b97b5be27164107be683dc1615777bb7618f026f608131f5301e73f2128f838a0e8e095cd832d74ecc34162a78b1fc7e5d173d495bd39e47fab11f736f64f4514feecb58836160b0e03487c3bf583e0bc3d131662b8d57d3d232ea99ed0b34b8ac6bacaa509e9209815799ab27a8e4d5e9a7fcebd


# Lots of logging
import logging

handler = logging.StreamHandler()
root_logger = logging.getLogger('')
root_logger.setLevel(logging.DEBUG)
root_logger.addHandler(handler)
logger = logging.getLogger(__name__)

class Handler(BaseHTTPServer.BaseHTTPRequestHandler):
    def __init__(self, request, client_address, server):
        """We need to init a lot because a new one of these gets created for every request.
        Things we need to keep around we attach to the server object via self.server
        """
        self.server = server  # the superclass __init__ does this anyway

        if not hasattr(self.server, 'conn'):
            wctoken = None
            if os.path.exists("WCTOKEN"):
                with open("WCTOKEN", "r") as f:
                    wctoken = f.read()
                    if not wctoken:
                        os.remove("WCTOKEN")

            record_id = None
            if os.path.exists("RECORD_ID"):
                with open("RECORD_ID", "r") as f:
                    record_id = f.read()

            try:
                self.server.conn = HealthVaultConn(
                    wctoken=wctoken,
                    app_id=APP_ID,
                    app_thumbprint=THUMBPRINT,
                    public_key=APP_PUBLIC_KEY,
                    private_key=APP_PRIVATE_KEY,
                    record_id=record_id
                )
            except HealthVaultException as e:
                print e
                # Leave it un-authorized
                # set up un-authorized conn
                self.server.conn = HealthVaultConn(
                    app_id=APP_ID,
                    app_thumbprint=THUMBPRINT,
                    public_key=APP_PUBLIC_KEY,
                    private_key=APP_PRIVATE_KEY,
                    record_id=record_id
                )
            else:
                if self.server.conn.record_id:
                    with open("RECORD_ID", "w") as f:
                        f.write(self.server.conn.record_id)


            # And this is a stupid old-style class, sigh
        # AND THE __init__ PROCESSES THE REQUEST!  ARGGG
        BaseHTTPServer.BaseHTTPRequestHandler.__init__(self, request, client_address, server)

    def show_data(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        conn = self.server.conn

        if self.server.conn.record_id:
            with open("RECORD_ID", "w") as f:
                f.write(self.server.conn.record_id)

        self.wfile.write("<p>Record id: %s</p>\n" % conn.record_id)

        try:
            alt_ids = conn.get_alternate_ids()
        except HealthVaultException as e:
            self.wfile.write("Exception getting alternate Ids: %s<br/>\n" % e)
        else:
            msg = "Alternate IDs: %s<br/>\n" % ", ".join(alt_ids)
            self.wfile.write(msg)
            for alt_id in alt_ids:
                conn.disassociate_alternate_id(alt_id)
                self.wfile.write("Removed alternate ID %s<br/>\n" % alt_id)

        try:
            name="AnanseRonald" #raw_input('Enter your name : ')
            conn.associate_alternate_id(name)
        except HealthVaultException as e:
            self.wfile.write("Exception associating alternate ID: %s<br/>\n" % e)
        else:
            self.wfile.write("Added alternate ID %s<br/>\n" % name)

        #conn.get_authorized_people()
        #conn.get_application_info()

        # Use batch to get some things
        try:
            result = conn.batch_get([{'datatype': DataType.BASIC_DEMOGRAPHIC_DATA},
                                     {'datatype': DataType.BLOOD_GLUCOSE_MEASUREMENT},
                                     {'datatype': DataType.WEIGHT_MEASUREMENTS},
                                     {'datatype': DataType.DEVICES}
                                     ])
        except HealthVaultException as e:
            self.wfile.write("Exception getting batch data: %s<br/>\n" % e)
        else:
            demographic_data, glucose_data, weight_data, device_data = result

            self.wfile.write("Demographic data:<br/>\n")
            self.wfile.write(demographic_data)
            self.wfile.write("<br/>\n")

            self.wfile.write("Blood glucose: <ul>")
            self.wfile.write("".join(["<li>" + repr(d) + "</li>" for d in glucose_data]))
            self.wfile.write("</ul>\n")

            self.wfile.write("WEIGHTS:<br/>\n<ul>\n")
            for w in weight_data:
                self.wfile.write("<li>%s</li>\n" % str(w))
            self.wfile.write("</ul>\n")

            self.wfile.write("DEVICES:<br/>\n<ul>\n")
            for w in device_data:
                self.wfile.write("<li>%s</li>\n" % str(w))
            self.wfile.write("</ul>\n")

        # Get some other things individually
        try:
            data = conn.get_blood_pressure_measurements()
        except HealthVaultException as e:
            self.wfile.write("Exception getting BP: %s<br/>\n" % e)
        else:
            self.wfile.write("BP: <ul>")
            self.wfile.write("".join(["<li>" + repr(d) + "</li>" for d in data]))
            self.wfile.write("</ul>\n")

        try:
            data = conn.get_height_measurements()
        except HealthVaultException as e:
            self.wfile.write("Exception getting heights: %s<br/>\n" % e)
        else:
            self.wfile.write("Heights: <ul>")
            self.wfile.write("".join(["<li>" + repr(d) + "</li>" for d in data]))
            self.wfile.write("</ul>\n")

        try:
            data = conn.get_exercise()
        except HealthVaultException as e:
            self.wfile.write("Exception getting exercise: %s<br/>\n" % e)
        else:
            self.wfile.write("Exercise: <ul>")
            self.wfile.write("".join(["<li>" + repr(d) + "</li>" for d in data]))
            self.wfile.write("</ul>\n")

        try:
            data = conn.get_sleep_sessions()
        except HealthVaultException as e:
            self.wfile.write("Exception getting sleep sessions: %s<br/>\n" % e)
        else:
            self.wfile.write("Sleep sessions: <ul>")
            self.wfile.write("".join(["<li>" + repr(d) + "</li>" for d in data]))
            self.wfile.write("</ul>\n")

        """try:
            data = conn.put_things()
        except HealthVaultException as e:
            self.wfile.write("Exception putting data: %s<br/>\n" % e)
        else:
            self.wfile.write(("Response: %s")%str(data))
            self.wfile.write("<br/>\n")

        self.wfile.write("END.<br/>\n")     """


    def set_wctoken(self, wctoken):
        # Make sure we can connect okay
        try:
            self.server.conn.connect(wctoken)
        except HealthVaultException as e:
            print "Exception making connection or something: %s" % e
            raise
        else:
            # Looks good, remember it
            with open("WCTOKEN", "w") as f:
                f.write(wctoken)
            with open("RECORD_ID", "w") as f:
                f.write(self.server.conn.record_id)

    def do_POST(self):
        logger.debug("do_POST: will call do_GET to handle, after reading the request body")
        content_length = int(self.headers['content-length'])
        body = self.rfile.read(content_length)
        logger.debug("Incoming request body=%r" % body)
        self.body = body
        return self.do_GET()

    def do_GET(self):
        logger.debug("do_GET: path=%s", self.path)
        if self.path == '/':
            if not self.server.conn.is_authorized():
                logger.debug("Not authorized yet, redir to HV")
                # Start by redirecting user to HealthVault to authorize us
                record_id = None
                if os.path.exists("RECORD_ID"):
                    with open("RECORD_ID", "r") as f:
                        record_id = f.read()
                url = self.server.conn.authorization_url('%s/authtoken' % BASE_URL, record_id)
                self.send_response(307)
                self.send_header("Location", url)
                self.end_headers()
                return
            self.show_data()
            return

        if self.path == '/submit':
            self.send_response(200)
            self.end_headers()
            return

        if self.path.startswith('/authtoken?'):
            # This is the redirect after the user has authed us
            # the params include the wctoken we'll be using from here on for this user's data
            logger.debug("Handling /authtoken...")
            o = urlparse(self.path)
            query = parse_qs(o.query)
            target = query['target'][0]
            if target == 'AppAuthReject':
                logger.debug('reject')
                self.send_response(200)
                self.end_headers()
                self.wfile.write("Auth was rejected (by the user?)")
                return
            if target not in ('AppAuthSuccess', 'SelectedRecordChanged'):
                logger.debug('no idea')
                self.send_response(200)
                self.end_headers()
                self.wfile.write("Unexpected authtoken target=%s\n" % target)
                self.wfile.write(self.path)
                return
            if not 'wctoken' in query:
                logger.debug('no wctoken given')
                self.send_response(200)
                self.end_headers()
                self.wfile.write("No WCTOKEN in query: %s" % self.path)
                self.wfile.close()
                return
            logger.debug("looks like we got a wctoken to use")
            try:
                self.set_wctoken(query['wctoken'][0])
            except HealthVaultException:
                logger.exception("Something went wrong trying to use the token")
                if os.path.exists("WCTOKEN"):
                    os.remove("WCTOKEN")
                self.send_response(307)
                self.send_header("Location", "/")
                self.end_headers()
                return

            logger.debug("Got token okay, redir to /")
            # Now redirect to / again
            self.send_response(307)
            self.send_header("Location", "/")
            self.end_headers()
            return

        # Tired of seeing errors for this one
        if self.path == '/favicon.ico':
            self.send_response(200)
            self.end_headers()
            return

        # We get here for any URL we don't recognize
        # Let's do an actual 404
        self.send_response(404)
        self.end_headers()
        self.wfile.write("Unknown URL: %r" % self.path)
        return


class SSLServer(BaseHTTPServer.HTTPServer):
    def server_bind(self):
        """Called by constructor to bind the socket.

        May be overridden.

        """
        self.socket = wrap_socket(self.socket, server_side=True, certfile='cert.pem')
        BaseHTTPServer.HTTPServer.server_bind(self)

# Start server
server_address = ('', 8000)
httpd = SSLServer(server_address, Handler)

# Point user's browser at our starting URL
webbrowser.open("%s/" % BASE_URL)

# And handle requests forever
httpd.serve_forever()
