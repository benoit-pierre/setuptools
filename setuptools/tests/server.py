"""Basic http server for tests to simulate PyPI or custom indexes
"""

import os
import threading

from setuptools.extern.six.moves import BaseHTTPServer
from setuptools.extern.six.moves.urllib_parse import urljoin
from setuptools.extern.six.moves.urllib.request import pathname2url




class RequestRecorder(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        requests = vars(self.server).setdefault('requests', [])
        requests.append(self)
        self.send_response(200, 'OK')


class MockServer(BaseHTTPServer.HTTPServer, threading.Thread):
    """
    A simple HTTP Server that records the requests made to it.
    """

    def __init__(
            self, server_address=('', 0),
            RequestHandlerClass=RequestRecorder):
        BaseHTTPServer.HTTPServer.__init__(
            self, server_address, RequestHandlerClass)
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.requests = []

    def run(self):
        self.serve_forever()

    @property
    def netloc(self):
        return 'localhost:%s' % self.server_port

    @property
    def url(self):
        return 'http://%s/' % self.netloc


def path_to_url(path, authority=None):
    """ Convert a path to a file: URL. """
    path = os.path.normpath(os.path.abspath(path))
    base = 'file:'
    if authority is not None:
        base += '//' + authority
    url = urljoin(base, pathname2url(path))
    return url
