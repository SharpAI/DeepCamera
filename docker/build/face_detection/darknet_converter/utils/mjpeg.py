"""mjpeg.py

This module implements a simple MJPEG server which handles HTTP
requests from remote clients.
"""


import time
import queue
import threading
import socket
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

import numpy as np
import cv2


# globals
_MJPEG_QUEUE = queue.Queue(maxsize=2)
_SLEEP_INTERVAL = 0.1  # update JPG roughly every 0.1 second


class MjpegHandler(BaseHTTPRequestHandler):
    """A simple MJPEG handler which publishes images."""

    def _handle_mjpeg(self):
        global _MJPEG_QUEUE
        img = _MJPEG_QUEUE.get()

        self.send_response(200)
        self.send_header(
            'Content-type',
            'multipart/x-mixed-replace; boundary=--jpgboundary'
        )
        self.end_headers()

        while True:
            if not _MJPEG_QUEUE.empty():
                img = _MJPEG_QUEUE.get()
            ret, jpg = cv2.imencode('.jpg', img)
            assert jpg is not None
            self.wfile.write("--jpgboundary".encode("utf-8"))
            self.send_header('Content-type', 'image/jpeg')
            self.send_header('Content-length', str(jpg.size))
            self.end_headers()
            self.wfile.write(jpg.tostring())
            time.sleep(_SLEEP_INTERVAL)

    def _handle_error(self):
        self.send_response(404)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write('<html><head></head><body>')
        self.wfile.write('<h1>{0!s} not found</h1>'.format(self.path))
        self.wfile.write('</body></html>')

    def do_GET(self):
        if self.path == '/mjpg' or self.path == '/':
            self._handle_mjpeg()
        else:
            #print('ERROR: ', self.path)
            self._handle_error()

    def handle(self):
        try:
            super().handle()
        except socket.error:
            # ignore BrokenPipeError, which is caused by the client
            # terminating the HTTP connection
            pass


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle HTTP requests in a separate thread."""
    # not used...


def run_server(server):
    server.serve_forever()  # this exits when server.shutdown() is called
    server.socket.shutdown(socket.SHUT_RDWR)
    server.socket.close()


class MjpegServer(object):
    def __init__(self, init_img=None, ip='', port=8080):
        # initialize the queue with a dummy image
        global _MJPEG_QUEUE
        init_img = init_img if init_img else \
                   np.ones((480, 640, 3), np.uint8) * 255  # all white
        _MJPEG_QUEUE.put(init_img)
        # create the HTTP server and run it from the child thread
        self.server = HTTPServer((ip, port), MjpegHandler)
        self.run_thread = threading.Thread(
            target=run_server, args=(self.server,))
        self.run_thread.start()

    def send_img(self, img):
        global _MJPEG_QUEUE
        try:
            _MJPEG_QUEUE.put(img, block=False)
        except queue.Full:
            pass

    def shutdown(self):
        self.server.shutdown()
        del self.server
