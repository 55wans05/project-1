"""
  A trivial web server in Python.

  Based largely on https://docs.python.org/3.4/howto/sockets.html
  This trivial implementation is not robust:  We have omitted decent
  error handling and many other things to keep the illustration as simple
  as possible.

  FIXME:
  Currently this program always serves an ascii graphic of a cat.
  Change it to serve files if they end with .html or .css, and are
  located in ./pages  (where '.' is the directory from which this
  program is run).
"""

import config    # Configure from .ini files and command line
import logging   # Better than print statements
import os
logging.basicConfig(format='%(levelname)s:%(message)s',
                    level=logging.INFO)
log = logging.getLogger(__name__)
# Logging level may be overridden by configuration 

import socket    # Basic TCP/IP communication on the internet
import _thread   # Response computation runs concurrently with main program


def listen(portnum):
    """
    Create and listen to a server socket.
    Args:
       portnum: Integer in range 1024-65535; temporary use ports
           should be in range 49152-65535.
    Returns:
       A server socket, unless connection fails (e.g., because
       the port is already in use).
    """
    # Internet, streaming socket
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Bind to port and make accessible from anywhere that has our IP address
    serversocket.bind(('', portnum))
    serversocket.listen(1)    # A real server would have multiple listeners
    return serversocket


def serve(sock, func):
    """
    Respond to connections on sock.
    Args:
       sock:  A server socket, already listening on some port.
       func:  a function that takes a client socket and does something with it
    Returns: nothing
    Effects:
        For each connection, func is called on a client socket connected
        to the connected client, running concurrently in its own thread.
    """
    while True:
        log.info("Attempting to accept a connection on {}".format(sock))
        (clientsocket, address) = sock.accept()
        _thread.start_new_thread(func, (clientsocket,))


##
# Starter version only serves cat pictures. In fact, only a
# particular cat picture.  This one.
##
CAT = """
     ^ ^
   =(   )=
"""

# Note: I did use chat gpt to generate these error pages
# mainly because i think its funny to ask the ai to generate
# genz and hackery pages
ERROR404 = """
<style>
    body {
        background-color: black;
        color: green;
        font-family: 'Courier New', monospace;
        text-align: center;
        padding: 20px;
    }

    h1 {
        font-size: 36px;
    }

    p {
        font-size: 18px;
        margin: 10px 0;
    }

    ul {
        list-style-type: none;
        padding: 0;
    }

    li {
        margin: 10px 0;
    }

    li:before {
        content: "> ";
        color: red;
    }
</style>

<h1>404 Error - Page Not Found, Lost in the Code Matrix 🚫💾</h1>

<p> Hold up, you just found a dead-end in the digital maze, and it's like Neo looking for the Matrix. 🧩🔍</p>

<p> We've been turning this place inside out, fam, but we couldn't track down the page you're after. It's like trying to find Waldo in a crowded selfie. 😅🔍</p>

<p> But no worries, we're all about helping you dodge those glitches and find the right path. Let's drop some knowledge:</p>

    <li>Double-check the URL, like you're checking for typos in your latest xeet. 📝🧐</li>
    <li>Smash that back button like you're unfollowing a clout chaser. ♻️🔙</li>
    <li>Head back to the homepage, hit refresh, and start your digital journey anew. 🏡🔄</li>
    <li>If you're still lost in the sauce, slide into our DMs. We're always up for a chat. 📩🤙</li>

<p> And remember, this 404 ain't personal—it's just a hiccup in the digital realm. Keep it real and keep scrolling! 🚀📱 #404Error #LostInTheMatrix #NoCodeFound</p>
"""

ERROR403 = """
<style>
    body {
        background-color: black;
        color: green;
        font-family: 'Courier New', monospace;
        text-align: center;
        padding: 20px;
    }

    h1 {
        font-size: 36px;
    }

    p {
        font-size: 18px;
        margin: 10px 0;
    }

    ul {
        list-style-type: none;
        padding: 0;
    }

    li {
        margin: 10px 0;
    }

    li:before {
        content: "> ";
        color: red;
    }
</style>

<h1>403 Forbidden - Access Denied, Hacker Alert 🚫👾</h1>

<p>Whoa, whoa, whoa! You've just hit a brick wall, my friend. Access denied, and we've got our cyber-eyes on you. 🙅‍♂️💻</p>

<p>No cap, this area is off-limits for a reason. We've got our digital guards up, and they're not here for games. 🛡️🔒</p>

<p>Here's the deal, hacker:</p>
<ul>
    <li>Your little shenanigans won't fly here, so don't even think about it. 🕵️‍♂️🚫</li>
    <li>We've got top-notch security, so you might as well give up the ghost and go legit. 👻💼</li>
    <li>If you're here by mistake, well, that's sus, but hit us up anyway. We'll see what's good. 🤔📞</li>
</ul>
<p>Remember, we're watching your every move, and we're not afraid to drop the banhammer. Stay on the right side of the digital law, fam. 🚀🤖 #403Forbidden #AccessDenied #HackerAlert</p>
"""

# HTTP response codes, as the strings we will actually send.
# See:  https://en.wikipedia.org/wiki/List_of_HTTP_status_codes
# or    http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html
##
STATUS_OK = "HTTP/1.0 200 OK\n\n"
STATUS_FORBIDDEN = "HTTP/1.0 403 Forbidden\n"
STATUS_NOT_FOUND = "HTTP/1.0 404 Not Found\n"
STATUS_NOT_IMPLEMENTED = "HTTP/1.0 401 Not Implemented\n\n"

# I added this and modified the two 400 statuses
# so that the webpage would render the utf emoji's properly
HTML_TYPE="Content-Type: text/html; charset=utf-8\n\n"

def respond(sock):
    """
    This server responds only to GET requests (not PUT, POST, or UPDATE).
    Any valid GET request is answered with an ascii graphic of a cat.
    """
    options = get_options()
    sent = 0
    request = sock.recv(1024)  # We accept only short requests
    request = str(request, encoding='utf-8', errors='strict')
    log.info("--- Received request ----")
    log.info("Request was {}\n***\n".format(request))

    parts = request.split()
    if len(parts) > 1 and parts[0] == "GET":
        if parts[1] == "/":
            transmit(STATUS_OK, sock)
            transmit(CAT, sock)
            sock.shutdown(socket.SHUT_RDWR)
            sock.close()
            return

        filepath = f'{options.DOCROOT}{parts[1]}'

        # Directly catching bad characters like a noob
        if '..' in filepath or '~' in filepath:
            transmit(STATUS_FORBIDDEN, sock)
            transmit(HTML_TYPE, sock)
            transmit(ERROR403, sock)
            sock.shutdown(socket.SHUT_RDWR)
            sock.close()
            return

        # The better way to check for an invalid path
        # resolve the final system path and ensure it
        # starts with the full path to the docroot
        fullpath = os.path.abspath(filepath)
        full_docroot = os.path.abspath(options.DOCROOT)
        if not fullpath.startswith(full_docroot):
            transmit(STATUS_FORBIDDEN, sock)
            transmit(HTML_TYPE, sock)
            transmit(ERROR403, sock)
            sock.shutdown(socket.SHUT_RDWR)
            sock.close()
            return

        # Check if the file exists
        print(fullpath)
        if not os.path.exists(fullpath):
            transmit(STATUS_NOT_FOUND, sock)
            transmit(HTML_TYPE, sock)
            transmit(ERROR404, sock)
            sock.shutdown(socket.SHUT_RDWR)
            sock.close()
            return

        # I'm not gonna check for permissions errors here,
        # even though a proper webserver would
        with open(fullpath, 'r') as file:
            contents = file.read()
        
        # transmit results
        transmit(STATUS_OK, sock)
        transmit(contents, sock)
    else:
        log.info("Unhandled request: {}".format(request))
        transmit(STATUS_NOT_IMPLEMENTED, sock)
        transmit("\nI don't handle this request: {}\n".format(request), sock)

    sock.shutdown(socket.SHUT_RDWR)
    sock.close()
    return


def transmit(msg, sock):
    """It might take several sends to get the whole message out"""
    sent = 0
    while sent < len(msg):
        buff = bytes(msg[sent:], encoding="utf-8")
        sent += sock.send(buff)

###
#
# Run from command line
#
###


def get_options():
    """
    Options from command line or configuration file.
    Returns namespace object with option value for port
    """
    # Defaults from configuration files;
    #   on conflict, the last value read has precedence
    options = config.configuration()
    # We want: PORT, DOCROOT, possibly LOGGING

    if options.PORT <= 1000:
        log.warning(("Port {} selected. " +
                         " Ports 0..1000 are reserved \n" +
                         "by the operating system").format(options.port))

    return options


def main():
    options = get_options()
    port = options.PORT
    if options.DEBUG:
        log.setLevel(logging.DEBUG)
    sock = listen(port)
    log.info("Listening on port {}".format(port))
    log.info("Socket is {}".format(sock))
    serve(sock, respond)


if __name__ == "__main__":
    main()
